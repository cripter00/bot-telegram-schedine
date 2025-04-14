#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import requests
import os
import time
from datetime import datetime, timedelta
import random

# Configurazione del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def aggiorna_quote():
    """
    Aggiorna le quote di calcio e le salva in un file JSON.
    Ottiene SOLO quote reali tramite API pubbliche.
    """
    logger.info("Aggiornamento delle quote in corso...")
    
    try:
        # Ottieni quote reali tramite API
        partite = ottieni_quote_reali()
        
        # Verifica se abbiamo ottenuto abbastanza partite
        if not partite or len(partite) < 3:
            logger.error(f"Non sono state trovate abbastanza partite reali ({len(partite) if partite else 0}). Aggiornamento non eseguito.")
            return False
        
        # Filtra le partite per ottenere solo quelle della giornata corrente
        oggi = datetime.now()
        domani = oggi + timedelta(days=1)
        partite_di_oggi = []
        
        for partita in partite:
            try:
                data_partita = datetime.fromisoformat(partita["orario"])
                # Prendi solo le partite di oggi o domani
                if oggi.date() <= data_partita.date() <= domani.date():
                    partite_di_oggi.append(partita)
            except Exception as e:
                logger.error(f"Errore nella gestione della data: {e}")
                continue
        
        # Verifica se abbiamo abbastanza partite dopo il filtraggio
        if len(partite_di_oggi) < 3:
            logger.error(f"Dopo il filtraggio per data, non sono rimaste abbastanza partite ({len(partite_di_oggi)}). Aggiornamento non eseguito.")
            return False
        
        # Assicurati che la directory di output esista
        os.makedirs("bot", exist_ok=True)
        
        # Salva le quote in un file JSON
        with open("bot/quote.json", "w", encoding="utf-8") as f:
            json.dump(partite_di_oggi, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Quote aggiornate con successo. {len(partite_di_oggi)} partite salvate.")
        return True
    
    except Exception as e:
        logger.error(f"Errore durante l'aggiornamento delle quote: {e}")
        return False

def ottieni_quote_reali():
    """
    Ottiene quote reali esclusivamente da API.
    """
    logger.info("Inizio recupero quote reali da API...")
    partite = []
    
    # Ottieni quote da football-data.org
    try:
        partite_football_data = ottieni_da_football_data()
        if partite_football_data:
            logger.info(f"Ottenute {len(partite_football_data)} partite da football-data.org")
            partite.extend(partite_football_data)
        else:
            logger.warning("Nessuna partita ottenuta da football-data.org")
    except Exception as e:
        logger.error(f"Errore durante l'estrazione da football-data.org: {e}")
    
    # Prova anche con API-Football se necessario
    if len(partite) < 5:
        try:
            partite_api_football = ottieni_da_api_football()
            if partite_api_football:
                logger.info(f"Ottenute {len(partite_api_football)} partite da API-Football")
                partite.extend(partite_api_football)
            else:
                logger.warning("Nessuna partita ottenuta da API-Football")
        except Exception as e:
            logger.error(f"Errore durante l'estrazione da API-Football: {e}")
    
    # Prova con TheOddsAPI se ancora non abbiamo abbastanza partite
    if len(partite) < 5:
        try:
            partite_the_odds_api = ottieni_da_the_odds_api()
            if partite_the_odds_api:
                logger.info(f"Ottenute {len(partite_the_odds_api)} partite da TheOddsAPI")
                partite.extend(partite_the_odds_api)
            else:
                logger.warning("Nessuna partita ottenuta da TheOddsAPI")
        except Exception as e:
            logger.error(f"Errore durante l'estrazione da TheOddsAPI: {e}")
    
    # Rimuovi possibili duplicati basati su squadre e data
    partite_uniche = []
    match_ids = set()
    for partita in partite:
        match_id = f"{partita['match']}_{partita['orario']}"
        if match_id not in match_ids:
            match_ids.add(match_id)
            partite_uniche.append(partita)
    
    logger.info(f"Totale partite uniche raccolte: {len(partite_uniche)}")
    
    # Controllo della validità delle quote
    partite_valide = []
    for partita in partite_uniche:
        # Verifica che tutte le quote siano presenti e siano numeri positivi
        quote_valide = True
        for tipo_quota in ["1", "X", "2"]:
            if tipo_quota not in partita["quote"] or not isinstance(partita["quote"][tipo_quota], (int, float)) or partita["quote"][tipo_quota] <= 1.0:
                quote_valide = False
                logger.warning(f"Quote non valide per {partita['match']}: {partita['quote']}")
                break
        
        if quote_valide:
            partite_valide.append(partita)
        else:
            logger.warning(f"Partita scartata per quote non valide: {partita['match']}")
    
    logger.info(f"Partite con quote valide: {len(partite_valide)}")
    return partite_valide

def ottieni_da_football_data():
    """
    Ottiene partite e quote da football-data.org.
    
    Football-data.org ha un piano gratuito che consente 10 richieste al minuto
    e fornisce partite con relative quote per le principali competizioni europee.
    """
    partite = []
    oggi = datetime.now()
    data_inizio = oggi.strftime("%Y-%m-%d")
    data_fine = (oggi + timedelta(days=1)).strftime("%Y-%m-%d")  # Solo partite di oggi e domani
    
    # API key fornita dall'utente
    api_key = "a76f04e3ebd64facb456ed0888227003"
    
    # Lista delle competizioni disponibili nel piano gratuito
    competizioni = [
        {"id": 2021, "nome": "Premier League"},
        {"id": 2019, "nome": "Serie A"},
        {"id": 2014, "nome": "La Liga"},
        {"id": 2002, "nome": "Bundesliga"},
        {"id": 2015, "nome": "Ligue 1"},
        {"id": 2001, "nome": "Champions League"}
    ]
    
    headers = {
        "X-Auth-Token": api_key
    }
    
    for competizione in competizioni:
        try:
            # Ottieni le partite per questa competizione
            url = f"https://api.football-data.org/v4/competitions/{competizione['id']}/matches"
            params = {
                "dateFrom": data_inizio,
                "dateTo": data_fine,
                "status": "SCHEDULED"
            }
            
            logger.info(f"Recupero partite per {competizione['nome']} da football-data.org")
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.warning(f"Errore API football-data.org: HTTP {response.status_code} - {response.text}")
                continue
            
            data = response.json()
            
            # Estrai le partite
            for match in data.get("matches", []):
                try:
                    squadra_casa = match.get("homeTeam", {}).get("name", "")
                    squadra_trasferta = match.get("awayTeam", {}).get("name", "")
                    
                    if not squadra_casa or not squadra_trasferta:
                        continue
                    
                    data_ora_str = match.get("utcDate", "")
                    if not data_ora_str:
                        continue
                        
                    # Converti la data in formato isoformat
                    data_ora = datetime.fromisoformat(data_ora_str.replace("Z", "+00:00"))
                    
                    # Ottieni le quote se disponibili
                    odds = match.get("odds", {})
                    quota_home = odds.get("homeWin")
                    quota_draw = odds.get("draw")
                    quota_away = odds.get("awayWin")
                    
                    # Verifica che tutte le quote necessarie siano presenti
                    if not quota_home or not quota_draw or not quota_away:
                        logger.warning(f"Quote mancanti per {squadra_casa} vs {squadra_trasferta}, partita saltata")
                        continue
                    
                    partita = {
                        "match": f"{squadra_casa} vs {squadra_trasferta}",
                        "competizione": competizione["nome"],
                        "orario": data_ora.isoformat(),
                        "quote": {"1": float(quota_home), "X": float(quota_draw), "2": float(quota_away)}
                    }
                    
                    partite.append(partita)
                    
                except Exception as e:
                    logger.error(f"Errore nell'elaborazione di una partita: {e}")
            
            # Rispetta i limiti dell'API (max 10 richieste al minuto per il piano gratuito)
            time.sleep(6)  # 6 secondi di pausa tra le richieste
            
        except Exception as e:
            logger.error(f"Errore nel recupero delle partite per {competizione['nome']}: {e}")
    
    return partite

def ottieni_da_api_football():
    """
    Ottiene partite e quote da API-Football (RapidAPI).
    
    API-Football ha un piano gratuito che consente 100 richieste al giorno.
    """
    partite = []
    
    # API key fornita dall'utente
    api_key = "5a9d158875msh1ac01d856ccee21p1d4e63jsn42014ab5c262"
    
    # Se non hai una chiave API, torna una lista vuota
    if not api_key or api_key == "TUA_API_KEY_QUI":
        logger.warning("API key per API-Football non impostata. Saltando questa fonte.")
        return []
    
    # Lista delle leghe disponibili
    leghe = [
        {"id": 39, "nome": "Premier League"},
        {"id": 135, "nome": "Serie A"},
        {"id": 140, "nome": "La Liga"},
        {"id": 78, "nome": "Bundesliga"},
        {"id": 61, "nome": "Ligue 1"},
        {"id": 2, "nome": "Champions League"}
    ]
    
    oggi = datetime.now()
    data = oggi.strftime("%Y-%m-%d")
    domani = (oggi + timedelta(days=1)).strftime("%Y-%m-%d")
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
    }
    
    for lega in leghe:
        try:
            # Ottieni le partite in programma oggi e domani
            url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            params = {
                "league": lega["id"],
                "from": data,
                "to": domani,
                "season": oggi.year if oggi.month > 7 else oggi.year - 1
            }
            
            logger.info(f"Recupero partite per {lega['nome']} da API-Football")
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.warning(f"Errore API-Football: HTTP {response.status_code} - {response.text}")
                continue
                
            data_resp = response.json()
            
            # Estrai le partite
            for fixture in data_resp.get("response", []):
                try:
                    squadra_casa = fixture.get("teams", {}).get("home", {}).get("name", "")
                    squadra_trasferta = fixture.get("teams", {}).get("away", {}).get("name", "")
                    
                    if not squadra_casa or not squadra_trasferta:
                        continue
                    
                    timestamp = fixture.get("fixture", {}).get("timestamp", 0)
                    if not timestamp:
                        continue
                    
                    # Converti il timestamp in datetime
                    data_ora = datetime.fromtimestamp(timestamp)
                    
                    # Per le quote, facciamo una richiesta separata
                    fixture_id = fixture.get("fixture", {}).get("id")
                    if not fixture_id:
                        logger.warning(f"ID mancante per la partita {squadra_casa} vs {squadra_trasferta}, saltata")
                        continue
                        
                    quote = ottieni_quote_api_football(fixture_id, headers)
                    
                    # Se le quote non sono valide, salta questa partita
                    if not quote or not all(k in quote and quote[k] > 1.0 for k in ["1", "X", "2"]):
                        logger.warning(f"Quote non valide per {squadra_casa} vs {squadra_trasferta}, partita saltata")
                        continue
                    
                    partita = {
                        "match": f"{squadra_casa} vs {squadra_trasferta}",
                        "competizione": lega["nome"],
                        "orario": data_ora.isoformat(),
                        "quote": quote
                    }
                    
                    partite.append(partita)
                    
                except Exception as e:
                    logger.error(f"Errore nell'elaborazione di una partita API-Football: {e}")
            
            # Rispetta i limiti dell'API (100 richieste al giorno per il piano gratuito)
            time.sleep(10)  # 10 secondi di pausa tra le richieste
            
        except Exception as e:
            logger.error(f"Errore nel recupero delle partite per {lega['nome']}: {e}")
    
    return partite

def ottieni_quote_api_football(fixture_id, headers):
    """
    Ottiene le quote per una partita specifica da API-Football.
    Restituisce None se le quote non sono disponibili.
    """
    try:
        url = "https://api-football-v1.p.rapidapi.com/v3/odds"
        params = {
            "fixture": fixture_id,
            "bookmaker": 8  # Bookmaker ID per bet365
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            logger.warning(f"Errore nel recupero quote: HTTP {response.status_code}")
            return None
        
        data = response.json()
        
        # Dizionario per le quote
        quote = {}
        quote_trovate = False
        
        for odds in data.get("response", []):
            for bookmaker in odds.get("bookmakers", []):
                for bet in bookmaker.get("bets", []):
                    if bet.get("name") == "Match Winner":
                        for value in bet.get("values", []):
                            value_name = value.get("value")
                            odd = value.get("odd")
                            
                            if not odd:
                                continue
                                
                            try:
                                odd_float = float(odd)
                                if odd_float <= 1.0:
                                    logger.warning(f"Quota non valida ({odd_float}) per {value_name}")
                                    continue
                            except ValueError:
                                logger.warning(f"Errore nella conversione della quota: {odd}")
                                continue
                            
                            if value_name == "Home":
                                quote["1"] = float(odd)
                                quote_trovate = True
                            elif value_name == "Draw":
                                quote["X"] = float(odd)
                                quote_trovate = True
                            elif value_name == "Away":
                                quote["2"] = float(odd)
                                quote_trovate = True
        
        if quote_trovate and all(k in quote for k in ["1", "X", "2"]):
            logger.info(f"Quote ottenute per fixture {fixture_id}: 1:{quote['1']}, X:{quote['X']}, 2:{quote['2']}")
            return quote
        else:
            logger.warning(f"Quote incomplete per fixture {fixture_id}")
            return None
        
    except Exception as e:
        logger.error(f"Errore nel recupero delle quote per fixture {fixture_id}: {e}")
        return None

def ottieni_da_the_odds_api():
    """
    Ottiene partite e quote da TheOddsAPI.
    
    TheOddsAPI ha un piano gratuito con 500 richieste al mese (≈ 16 al giorno)
    https://the-odds-api.com/
    """
    partite = []
    
    # API key fornita dall'utente - registrarsi su https://the-odds-api.com per ottenere una chiave gratuita
    api_key = "4cfcde2e8c93b776df9cbfc1ba57939f"
    
    # Se non hai una chiave API, torna una lista vuota
    if not api_key or api_key == "YOUR_THE_ODDS_API_KEY":
        logger.warning("API key per TheOddsAPI non impostata. Saltando questa fonte.")
        return []
    
    # Lista degli sport disponibili nel piano gratuito
    regions = ["eu"]  # Formato quota europea (decimale)
    markets = ["h2h"]  # Quote 1X2 per il calcio
    
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds"
    params = {
        "api_key": api_key,
        "regions": ",".join(regions),
        "markets": ",".join(markets),
        "dateFormat": "iso",
        "oddsFormat": "decimal"
    }
    
    try:
        logger.info("Recupero partite da TheOddsAPI")
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            logger.warning(f"Errore TheOddsAPI: HTTP {response.status_code} - {response.text}")
            return []
        
        data = response.json()
        
        # Verifica il limite di richieste rimanenti
        requests_remaining = response.headers.get('x-requests-remaining', 'Unknown')
        logger.info(f"Richieste TheOddsAPI rimanenti: {requests_remaining}")
        
        # Debug: visualizza la struttura dei dati ricevuti
        if data:
            logger.info(f"Ricevuti {len(data)} eventi da TheOddsAPI")
            if len(data) > 0:
                sample_event = data[0]
                logger.info(f"Esempio di struttura evento: {json.dumps(sample_event, indent=2)}")
        
        for event in data:
            try:
                # Estrai informazioni di base
                sport_key = event.get("sport_key", "")
                competizione = sport_key.replace("soccer_", "").replace("_", " ").title()
                
                # Estrai squadre (queste sono a livello di evento, non di bookmaker)
                squadra_casa = event.get("home_team", "")
                squadra_trasferta = event.get("away_team", "")
                
                if not squadra_casa or not squadra_trasferta:
                    logger.warning(f"Squadre non trovate nell'evento: {event.get('id', 'ID sconosciuto')}")
                    continue
                
                # Estrai data e ora
                commence_time = event.get("commence_time", "")
                if not commence_time:
                    logger.warning(f"Orario non trovato per {squadra_casa} vs {squadra_trasferta}")
                    continue
                
                logger.info(f"Analisi evento: {squadra_casa} vs {squadra_trasferta} - {commence_time}")
                
                # Per le quote, estrai dai bookmakers disponibili
                bookmakers = event.get("bookmakers", [])
                if not bookmakers:
                    logger.warning(f"Nessun bookmaker trovato per {squadra_casa} vs {squadra_trasferta}")
                    continue
                
                # Cerca tra i bookmaker disponibili (priorità a bet365 se disponibile)
                quote = None
                for bookmaker in bookmakers:
                    bookmaker_key = bookmaker.get("key", "sconosciuto")
                    logger.info(f"Analisi bookmaker: {bookmaker_key}")
                    
                    # Passa le squadre al metodo di estrazione quote
                    quote_trovate = estrai_quote_the_odds_api(bookmaker, squadra_casa, squadra_trasferta)
                    if quote_trovate:
                        quote = quote_trovate
                        logger.info(f"Quote trovate dal bookmaker {bookmaker_key} per {squadra_casa} vs {squadra_trasferta}")
                        break  # Abbiamo trovato quote valide, interrompiamo il ciclo
                
                if not quote:
                    logger.warning(f"Quote non trovate per {squadra_casa} vs {squadra_trasferta}")
                    continue
                
                # Crea l'oggetto partita
                partita = {
                    "match": f"{squadra_casa} vs {squadra_trasferta}",
                    "competizione": competizione,
                    "orario": commence_time,
                    "quote": quote
                }
                
                partite.append(partita)
                logger.info(f"Partita aggiunta: {squadra_casa} vs {squadra_trasferta} con quote {quote}")
                
            except Exception as e:
                logger.error(f"Errore nell'elaborazione di un evento TheOddsAPI: {e}")
        
    except Exception as e:
        logger.error(f"Errore nel recupero delle partite da TheOddsAPI: {e}")
    
    return partite

def estrai_quote_the_odds_api(bookmaker, home_team, away_team):
    """
    Estrae le quote da un bookmaker di TheOddsAPI.
    
    Args:
        bookmaker: I dati del bookmaker
        home_team: Nome della squadra di casa
        away_team: Nome della squadra in trasferta
    """
    try:
        markets = bookmaker.get("markets", [])
        
        for market in markets:
            if market.get("key") == "h2h":
                outcomes = market.get("outcomes", [])
                logger.info(f"Trovati {len(outcomes)} risultati possibili")
                
                # Dizionario per le quote
                quote = {}
                
                # Debug per controllare la struttura
                outcome_names = [outcome.get("name", "") for outcome in outcomes]
                logger.info(f"Nomi outcomes disponibili: {outcome_names}")
                
                # Prima passata: mappatura esatta
                for outcome in outcomes:
                    name = outcome.get("name", "")
                    price = outcome.get("price")
                    
                    if not price or price <= 1.0:
                        continue
                    
                    # Match case-insensitive
                    if name.lower() == home_team.lower():
                        quote["1"] = float(price)
                    elif name.lower() == away_team.lower():
                        quote["2"] = float(price)
                    elif name.lower() in ["draw", "pareggio", "tie", "x"]:
                        quote["X"] = float(price)
                
                # Se non abbiamo abbastanza info, proviamo il metodo per posizione
                if len(outcomes) == 3 and not all(k in quote for k in ["1", "X", "2"]):
                    # Assumiamo che le quote seguano l'ordine: 1, X, 2 oppure Home, Draw, Away
                    home_found = False
                    away_found = False
                    draw_found = False
                    
                    for outcome in outcomes:
                        name = outcome.get("name", "").lower()
                        price = outcome.get("price")
                        
                        if not price or price <= 1.0:
                            continue
                            
                        if name == home_team.lower() or name.find("home") >= 0 or name.find("1") >= 0:
                            quote["1"] = float(price)
                            home_found = True
                        elif name == away_team.lower() or name.find("away") >= 0 or name.find("2") >= 0:
                            quote["2"] = float(price)
                            away_found = True
                        elif name.find("draw") >= 0 or name.find("tie") >= 0 or name.find("x") >= 0 or name.find("pareggio") >= 0:
                            quote["X"] = float(price)
                            draw_found = True
                    
                    # Se ancora non abbiamo tutte le quote e sono esattamente 3 outcomes, assegniamo per posizione
                    if len(outcomes) == 3 and not (home_found and away_found and draw_found):
                        logger.info("Assegnazione quote per posizione")
                        valid_prices = all(outcome.get("price", 0) > 1.0 for outcome in outcomes)
                        
                        if valid_prices:
                            # Assumiamo che il primo sia 1, il secondo X e il terzo 2
                            quote["1"] = float(outcomes[0].get("price"))
                            quote["X"] = float(outcomes[1].get("price"))
                            quote["2"] = float(outcomes[2].get("price"))
                
                # Verifica che tutte le quote siano presenti
                if all(k in quote for k in ["1", "X", "2"]):
                    logger.info(f"Quote complete trovate: 1={quote['1']}, X={quote['X']}, 2={quote['2']}")
                    return quote
                else:
                    missing = [k for k in ["1", "X", "2"] if k not in quote]
                    logger.warning(f"Quote incomplete, mancano: {', '.join(missing)}")
                    return None
        
        return None
    
    except Exception as e:
        logger.error(f"Errore nell'estrazione delle quote da TheOddsAPI: {e}")
        return None

if __name__ == "__main__":
    # Esegui l'aggiornamento quando lo script viene eseguito direttamente
    aggiorna_quote() 