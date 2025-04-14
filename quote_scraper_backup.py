#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime, timedelta
import os
import re
import time

# Configurazione del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def aggiorna_quote():
    """
    Aggiorna le quote di calcio e le salva in un file JSON.
    Ottiene SOLO quote reali tramite scraping da siti pubblici.
    """
    logger.info("Aggiornamento delle quote in corso...")
    
    try:
        # Ottieni solo quote reali - non utilizziamo più il fallback
        partite = ottieni_quote_reali()
        
        # Verifica se abbiamo ottenuto abbastanza partite
        if not partite or len(partite) < 5:
            logger.error(f"Non sono state trovate abbastanza partite reali ({len(partite) if partite else 0}). Aggiornamento non eseguito.")
            return False
        
        # Filtra solo le partite di oggi e dei giorni successivi
        oggi = datetime.now()
        partite_filtrate = []
        
        for partita in partite:
            try:
                data_partita = datetime.fromisoformat(partita["orario"])
                # Mantieni solo partite di oggi o future (max 7 giorni)
                if data_partita >= oggi and data_partita <= (oggi + timedelta(days=7)):
                    # Verifica che la partita abbia tutti i campi necessari
                    if ("match" in partita and 
                        "orario" in partita and 
                        "competizione" in partita and 
                        "quote" in partita and
                        "1" in partita["quote"] and 
                        "X" in partita["quote"] and 
                        "2" in partita["quote"]):
                        # Verifica che il formato del match sia corretto
                        if " vs " in partita["match"]:
                            # Verifica che le squadre siano squadre reali (almeno 2 caratteri)
                            squadre = partita["match"].split(" vs ")
                            if len(squadre) == 2 and len(squadre[0]) >= 2 and len(squadre[1]) >= 2:
                                partite_filtrate.append(partita)
            except Exception as e:
                logger.error(f"Errore nella conversione della data o validazione: {e}")
                continue
        
        # Verifica se abbiamo abbastanza partite dopo il filtraggio
        if len(partite_filtrate) < 5:
            logger.error(f"Dopo il filtraggio per data e validazione, non sono rimaste abbastanza partite ({len(partite_filtrate)}). Aggiornamento non eseguito.")
            return False
        
        # Assicurati che la directory di output esista
        os.makedirs("bot", exist_ok=True)
        
        # Salva le quote in un file JSON
        with open("bot/quote.json", "w", encoding="utf-8") as f:
            json.dump(partite_filtrate, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Quote aggiornate con successo. {len(partite_filtrate)} partite salvate.")
        return True
    
    except Exception as e:
        logger.error(f"Errore durante l'aggiornamento delle quote: {e}")
        return False

def ottieni_quote_reali():
    """
    Ottiene quote reali da siti pubblici di quote calcio.
    Restituisce un elenco di partite con le relative quote.
    """
    try:
        # Headers più completi per evitare blocchi anti-scraping
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Referer": "https://www.google.com/",
            "Sec-Ch-Ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
        # Array di URL specifici per partite che avvengono OGGI o DOMANI
        urls = [
            "https://www.oddsportal.com/soccer/", # Pagina principale calcio
            "https://www.oddsportal.com/matches/soccer/", # Partite di calcio di oggi
            "https://www.oddsportal.com/soccer/italy/serie-a/", # Serie A
            "https://www.oddsportal.com/soccer/england/premier-league/", # Premier League
            "https://www.oddsportal.com/soccer/spain/laliga/", # La Liga
            "https://www.oddsportal.com/soccer/germany/bundesliga/", # Bundesliga
            "https://www.oddsportal.com/soccer/france/ligue-1/", # Ligue 1
            "https://www.oddsportal.com/soccer/europe/champions-league/", # Champions League
            "https://www.oddsportal.com/soccer/europe/europa-league/", # Europa League
        ]
        
        partite = []
        
        for url in urls:
            try:
                logger.info(f"Tentativo di scaricamento dati da: {url}")
                # Utilizza un timeout più lungo per assicurarsi che la pagina si carichi
                response = requests.get(url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    logger.warning(f"Errore nel recupero delle quote da {url}: HTTP {response.status_code}")
                    continue
                
                logger.info(f"Pagina scaricata con successo da {url}, analisi in corso...")
                
                # Esegui lo scraping con il parser dedicato per Oddsportal
                nuove_partite = estrai_partite_oddsportal(response.text, url)
                
                if nuove_partite:
                    logger.info(f"Trovate {len(nuove_partite)} partite da {url}")
                    # Aggiungi le partite trovate alla lista
                    partite.extend(nuove_partite)
                else:
                    logger.warning(f"Nessuna partita trovata da {url}")
                
                # Se abbiamo un numero sufficiente di partite, possiamo fermarci
                if len(partite) >= 50:  # Limitiamo a 50 partite
                    logger.info(f"Raccolte {len(partite)} partite, numero massimo raggiunto")
                    break
                
                # Aggiungiamo una piccola pausa tra le richieste per evitare di essere bloccati
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Errore durante il recupero delle quote da {url}: {e}")
                continue
        
        # Rimuovi eventuali duplicati (stesse squadre e stesso orario)
        partite_uniche = []
        partite_viste = set()
        
        for partita in partite:
            chiave = f"{partita['match']}_{partita['orario']}"
            if chiave not in partite_viste:
                partite_uniche.append(partita)
                partite_viste.add(chiave)
        
        logger.info(f"Quote reali ottenute: {len(partite_uniche)} partite uniche.")
        return partite_uniche
    
    except Exception as e:
        logger.error(f"Errore durante il recupero delle quote reali: {e}")
        return []

def estrai_partite_oddsportal(html_content, url_origine):
    """
    Estrae le partite dal contenuto HTML di Oddsportal.
    
    Args:
        html_content: Il contenuto HTML della pagina
        url_origine: L'URL da cui proviene il contenuto, per determinare il tipo di pagina
    
    Returns:
        Una lista di partite estratte
    """
    partite = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Verifica se la pagina è vuota o se è una pagina di errore
        if "No data available" in html_content or "Error" in html_content:
            logger.warning(f"La pagina {url_origine} non contiene dati validi.")
            return []
        
        # Estrai le informazioni sulla competizione se disponibili
        competizione = "Calcio"  # Default
        data_competizione = soup.select_one('h1.heading')
        if data_competizione:
            competizione = data_competizione.text.strip()
        
        # Cerca le tabelle delle partite
        tabelle_partite = soup.select('table.table-main')
        
        if not tabelle_partite:
            # Sito potrebbe aver cambiato struttura, prova selettori alternativi
            logger.warning(f"Nessuna tabella trovata con il selettore principale. Provo selettori alternativi.")
            tabelle_partite = soup.select('div.table-container table')
        
        if not tabelle_partite:
            logger.warning(f"Nessuna tabella trovata in {url_origine}.")
            return []
        
        logger.info(f"Trovate {len(tabelle_partite)} tabelle in {url_origine}")
        
        for tabella in tabelle_partite:
            righe = tabella.select('tr:not(.dark):not(.table-head)')
            
            logger.info(f"Trovate {len(righe)} righe in una tabella")
            
            for riga in righe:
                try:
                    # Estrai i dati della partita
                    celle = riga.select('td')
                    if len(celle) < 4:
                        continue
                    
                    tempo = riga.select_one('td.table-time')
                    if not tempo:
                        continue
                    
                    # Estrai l'orario e la data
                    orario_testo = tempo.text.strip()
                    orario_match = re.search(r'(\d{2}:\d{2})', orario_testo)
                    
                    # Cerca anche una data eventuale (formato: 12 Apr)
                    data_match = re.search(r'(\d{1,2}\s+\w{3})', orario_testo)
                    
                    if not orario_match:
                        continue
                    
                    orario = orario_match.group(1)
                    oggi = datetime.now()
                    
                    # Se abbiamo una data specifica, utilizzala
                    if data_match:
                        data_testo = data_match.group(1)
                        try:
                            # Prova a convertire in un formato di data
                            data_partita = datetime.strptime(f"{data_testo} {oggi.year}", "%d %b %Y")
                            
                            # Se la data è nel passato (potrebbe essere dell'anno prossimo)
                            if data_partita < oggi and (oggi - data_partita).days > 30:
                                data_partita = data_partita.replace(year=oggi.year + 1)
                            
                            # Ora combina la data con l'orario
                            data_ora = data_partita.replace(
                                hour=int(orario.split(':')[0]),
                                minute=int(orario.split(':')[1]),
                                second=0,
                                microsecond=0
                            )
                        except ValueError:
                            # Se la conversione fallisce, usa la data di oggi
                            data_ora = oggi.replace(
                                hour=int(orario.split(':')[0]),
                                minute=int(orario.split(':')[1]),
                                second=0,
                                microsecond=0
                            )
                    else:
                        # Determina la data in base all'URL
                        if "today" in url_origine.lower():
                            data_ora = oggi.replace(
                                hour=int(orario.split(':')[0]),
                                minute=int(orario.split(':')[1]),
                                second=0,
                                microsecond=0
                            )
                        elif "tomorrow" in url_origine.lower():
                            data_ora = (oggi + timedelta(days=1)).replace(
                                hour=int(orario.split(':')[0]),
                                minute=int(orario.split(':')[1]),
                                second=0,
                                microsecond=0
                            )
                        else:
                            # Usa la data di oggi con l'orario della partita
                            data_ora = oggi.replace(
                                hour=int(orario.split(':')[0]),
                                minute=int(orario.split(':')[1]),
                                second=0,
                                microsecond=0
                            )
                    
                    # Se l'ora è nel passato, probabilmente è per domani
                    if data_ora < oggi and "tomorrow" not in url_origine.lower():
                        data_ora = data_ora + timedelta(days=1)
                    
                    # Estrai i nomi delle squadre
                    nome_partita = riga.select_one('td.name a')
                    if not nome_partita:
                        continue
                    
                    partita_testo = nome_partita.text.strip()
                    squadre = partita_testo.split(' - ')
                    
                    if len(squadre) != 2:
                        continue
                    
                    squadra_casa = squadre[0].strip()
                    squadra_trasferta = squadre[1].strip()
                    
                    # Verifica che i nomi delle squadre siano validi (almeno 2 caratteri)
                    if len(squadra_casa) < 2 or len(squadra_trasferta) < 2:
                        continue
                    
                    # Estrai le quote
                    quote_celle = riga.select('td.odds-nowrp')
                    
                    if len(quote_celle) < 3:
                        continue
                    
                    try:
                        quota_1 = float(quote_celle[0].text.strip())
                        quota_x = float(quote_celle[1].text.strip())
                        quota_2 = float(quote_celle[2].text.strip())
                        
                        # Verifica che le quote siano in un range realistico
                        if not (1.01 <= quota_1 <= 15.0 and 1.5 <= quota_x <= 12.0 and 1.01 <= quota_2 <= 20.0):
                            continue
                    except ValueError:
                        continue
                    
                    # Determina la competizione più precisa dalla URL, se disponibile
                    if competizione == "Calcio" or "matches" in competizione.lower():
                        if "serie-a" in url_origine.lower():
                            competizione = "Serie A"
                        elif "premier-league" in url_origine.lower():
                            competizione = "Premier League"
                        elif "laliga" in url_origine.lower():
                            competizione = "La Liga"
                        elif "bundesliga" in url_origine.lower():
                            competizione = "Bundesliga"
                        elif "ligue-1" in url_origine.lower():
                            competizione = "Ligue 1"
                        elif "champions-league" in url_origine.lower():
                            competizione = "Champions League"
                        elif "europa-league" in url_origine.lower():
                            competizione = "Europa League"
                    
                    # Crea l'oggetto partita
                    partita = {
                        "match": f"{squadra_casa} vs {squadra_trasferta}",
                        "competizione": competizione,
                        "orario": data_ora.isoformat(),
                        "quote": {"1": quota_1, "X": quota_x, "2": quota_2}
                    }
                    
                    partite.append(partita)
                    logger.debug(f"Partita estratta: {partita['match']} ({partita['orario']})")
                
                except Exception as e:
                    logger.error(f"Errore nell'elaborazione di una riga: {e}")
                    continue
    
    except Exception as e:
        logger.error(f"Errore nell'analisi HTML di Oddsportal: {e}")
    
    return partite

def estrai_partite_flashscore(html_content):
    """
    Estrae le partite dal contenuto HTML di Flashscore.
    NOTA: Non utilizziamo più questa funzione perché non fornisce quote reali.
    """
    # Restituisci una lista vuota
    return []

def estrai_partite_betexplorer(html_content):
    """
    Estrae le partite dal contenuto HTML di BetExplorer.
    """
    partite = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # BetExplorer ha una struttura diversa, adatta il selettore
        match_rows = soup.select('table.table-main tr.js-event-list-tournament-events')
        
        for row in match_rows:
            try:
                # Estrai i nomi delle squadre
                squadre_elem = row.select_one('.in-match')
                if not squadre_elem:
                    continue
                
                partita_testo = squadre_elem.text.strip().replace('\n', ' ')
                squadre = partita_testo.split(' - ')
                
                if len(squadre) != 2:
                    continue
                
                squadra_casa = squadre[0].strip()
                squadra_trasferta = squadre[1].strip()
                
                # Estrai l'orario
                orario_elem = row.select_one('.table-time')
                if not orario_elem:
                    continue
                
                orario_testo = orario_elem.text.strip()
                orario_match = re.search(r'(\d{2}:\d{2})', orario_testo)
                
                if not orario_match:
                    continue
                
                orario = orario_match.group(1)
                oggi = datetime.now()
                
                data_ora = oggi.replace(
                    hour=int(orario.split(':')[0]),
                    minute=int(orario.split(':')[1]),
                    second=0,
                    microsecond=0
                )
                
                # Se l'ora è nel passato, probabilmente è per domani
                if data_ora < oggi:
                    data_ora = data_ora + timedelta(days=1)
                
                # Estrai le quote se disponibili
                quote_cells = row.select('td.table-odds')
                
                if len(quote_cells) >= 3:
                    try:
                        quota_1 = float(quote_cells[0].text.strip())
                        quota_x = float(quote_cells[1].text.strip())
                        quota_2 = float(quote_cells[2].text.strip())
                        
                        # Verifica che le quote siano in un range realistico
                        if not (1.01 <= quota_1 <= 15.0 and 1.5 <= quota_x <= 12.0 and 1.01 <= quota_2 <= 20.0):
                            continue
                    except (ValueError, IndexError):
                        # Se non possiamo estrarre quote reali, saltiamo questa partita
                        continue
                else:
                    # Se non ci sono quote, saltiamo questa partita
                    continue
                
                # Cerca di identificare la competizione
                competizione_elem = row.find_previous('div', class_='js-tournament-name')
                competizione = "Calcio"
                if competizione_elem:
                    competizione = competizione_elem.text.strip()
                
                partita = {
                    "match": f"{squadra_casa} vs {squadra_trasferta}",
                    "competizione": competizione,
                    "orario": data_ora.isoformat(),
                    "quote": {"1": quota_1, "X": quota_x, "2": quota_2}
                }
                
                partite.append(partita)
                
            except Exception as e:
                logger.error(f"Errore nell'elaborazione di una partita BetExplorer: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Errore nell'analisi HTML di BetExplorer: {e}")
    
    return partite

def estrai_partite_sofascore(html_content):
    """
    Estrae le partite dal contenuto HTML di SofaScore.
    NOTA: Non utilizziamo più questa funzione perché non fornisce quote reali.
    """
    # Restituisci una lista vuota
    return []

if __name__ == "__main__":
    # Esegui l'aggiornamento quando lo script viene eseguito direttamente
    aggiorna_quote() 