#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import random
from datetime import datetime, timedelta

# Configurazione del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def carica_quote():
    """Carica le quote dal file JSON."""
    try:
        with open("bot/quote.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Errore nel caricamento delle quote: {e}")
        return []

def filtra_partite_per_quota(partite, min_quota, max_quota):
    """Filtra le partite per range di quota."""
    partite_filtrate = []
    
    for partita in partite:
        quote = partita["quote"]
        # Controlla se almeno una delle quote è nel range specificato
        if (min_quota <= quote["1"] <= max_quota or 
            min_quota <= quote["X"] <= max_quota or 
            min_quota <= quote["2"] <= max_quota):
            partite_filtrate.append(partita)
    
    return partite_filtrate

# Statistiche reali del calcio - basate su analisi storiche di migliaia di partite
STATISTICHE_CALCIO = {
    # Probabilità di vittoria della squadra di casa, pareggio, vittoria trasferta
    "distribuzione_risultati": {"1": 45.9, "X": 24.8, "2": 29.3},
    
    # Distribuzione delle quote in base alla probabilità reale dell'evento
    "affidabilita_quote": {
        "bassa": 0.9,     # Quotes 1.01-1.50 si avverano circa 90% delle volte
        "medio_bassa": 0.7,  # Quotes 1.51-2.00 si avverano circa 70% delle volte
        "media": 0.5,     # Quotes 2.01-3.00 si avverano circa 50% delle volte
        "medio_alta": 0.3,   # Quotes 3.01-5.00 si avverano circa 30% delle volte
        "alta": 0.15      # Quotes >5.00 si avverano circa 15% delle volte
    },
    
    # Statistiche sulle quote delle big leagues europee
    "quote_medie": {
        "vittoria_favorita": 1.55,
        "pareggio_medio": 3.50,
        "vittoria_sfavorita": 5.80
    },
    
    # Probabilità che una partita finisca con il risultato favorito dalle quote
    "probabilita_pronostico_rispettato": 0.62
}

def seleziona_pronostico(partita, tipo_schedina):
    """Seleziona un pronostico per una partita in base al tipo di schedina."""
    quote = partita["quote"]
    
    # Estrai nomi delle squadre dalla stringa della partita
    squadre = partita["match"].split(" vs ")
    squadra_casa = squadre[0].strip()
    squadra_trasferta = squadre[1].strip()
    
    # Calcola probabilità implicite dalle quote (inverso della quota)
    prob_1 = 1/quote["1"]
    prob_x = 1/quote["X"]
    prob_2 = 1/quote["2"]
    
    # Normalizza le probabilità (la somma deve essere 1)
    somma_prob = prob_1 + prob_x + prob_2
    prob_1 /= somma_prob
    prob_x /= somma_prob
    prob_2 /= somma_prob
    
    # Determina il favorito in base alle probabilità implicite
    favorito = "1" if prob_1 > max(prob_x, prob_2) else "2" if prob_2 > max(prob_1, prob_x) else "X"
    
    # Determina se c'è un favorito netto (probabilità molto alta)
    favorito_netto = max(prob_1, prob_x, prob_2) > 0.6
    
    # Pronostici in base al tipo di schedina
    if tipo_schedina == "facile":
        # Per schedine facili, scegli pronostici con alta probabilità di riuscita
        # Di solito si tratta di favoriti netti in casa o in trasferta
        if favorito_netto:
            return favorito, quote[favorito]
        else:
            # Se non c'è un favorito netto, scegli l'evento con quota più bassa
            return min(quote.items(), key=lambda x: x[1])
    
    elif tipo_schedina == "media":
        # Per schedine medie, bilancia rischio e rendimento
        # Evita outsider completi ma anche i favoriti troppo scontati
        quote_medie = {k: v for k, v in quote.items() if 1.6 <= v <= 2.5}
        
        if quote_medie:
            # Se ci sono quote nel range medio, selezionale con una leggera preferenza per quelle più probabili
            items = list(quote_medie.items())
            pesi = [1/item[1] for item in items]  # Più bassa la quota, più alto il peso
            return random.choices(items, weights=pesi, k=1)[0]
        else:
            # Se non ci sono quote nel range, scegli l'evento con probabilità media
            items = list(quote.items())
            
            # Escludi le quote troppo basse
            items = [item for item in items if item[1] >= 1.4]
            
            if items:
                return random.choice(items)
            else:
                return random.choice(list(quote.items()))
    
    elif tipo_schedina == "difficile":
        # Per schedine difficili, cerca quote più alte ma ancora con una chance ragionevole
        # Evita i favoriti netti, cerca sorprese con valore
        quote_alte = {k: v for k, v in quote.items() if 2.5 <= v <= 5.0}
        
        if quote_alte:
            return random.choice(list(quote_alte.items()))
        else:
            # Se non ci sono quote nel range, scegli la quota più alta tra quelle non impossibili
            items = list(quote.items())
            # Ordina per quota decrescente
            items.sort(key=lambda x: x[1], reverse=True)
            # Prendi una delle prime due quote più alte
            return items[0] if len(items) == 1 else random.choice(items[:2])
    
    elif tipo_schedina == "fortunata":
        # Per schedine fortunate, usa una strategia più sofisticata basata su value betting
        
        # Calcola il "valore" di ogni quota
        # Valore = (probabilità stimata * quota) - 1
        # Un valore > 0 suggerisce una quota con valore positivo
        
        # Stima le probabilità reali in base a fattore casa/trasferta e quote
        # Questa è una versione semplificata del modello utilizzato dai bookmaker
        prob_stimata_1 = prob_1 * 1.05  # Leggero boost alle squadre in casa
        prob_stimata_x = prob_x * 0.95  # Leggera penalizzazione al pareggio
        prob_stimata_2 = prob_2 * 1.0   # Neutrale per le squadre in trasferta
        
        # Calcola i valori
        valore_1 = (prob_stimata_1 * quote["1"]) - 1
        valore_x = (prob_stimata_x * quote["X"]) - 1
        valore_2 = (prob_stimata_2 * quote["2"]) - 1
        
        # Crea una lista di tuple (segno, quota, valore)
        valori = [
            ("1", quote["1"], valore_1),
            ("X", quote["X"], valore_x),
            ("2", quote["2"], valore_2)
        ]
        
        # Ordina per valore decrescente
        valori.sort(key=lambda x: x[2], reverse=True)
        
        # Scegli fra i migliori valori con una probabilità pesata
        if random.random() < 0.7:
            # 70% delle volte, scegli il miglior valore
            return valori[0][0], valori[0][1]
        else:
            # 30% delle volte, scegli tra i primi due migliori valori
            indice = 0 if len(valori) == 1 else random.randint(0, min(1, len(valori)-1))
            return valori[indice][0], valori[indice][1]
    
    else:
        # Default: scegli casualmente ma pesato in base alle probabilità implicite
        items = list(quote.items())
        pesi = [1/item[1] for item in items]
        return random.choices(items, weights=pesi, k=1)[0]

def genera_schedina(tipo_schedina, num_partite=5):
    """
    Genera una schedina con pronostici basati sulle quote.
    
    Args:
        tipo_schedina (str): 'facile', 'media', 'difficile' o 'fortunata'
        num_partite (int): Numero di partite da includere
        
    Returns:
        str: Messaggio formattato con la schedina
    """
    try:
        quote = carica_quote()
        if not quote or not isinstance(quote, list) or len(quote) == 0:
            return "⚠️ *Errore*: Non sono riuscito a caricare le quote. Riprova più tardi."
        
        # Ottieni la data di oggi
        oggi = datetime.now().date()
        
        # Filtra solo le partite di oggi
        partite_oggi = []
        for partita in quote:
            try:
                # Il campo orario è in formato ISO
                data_str = partita["orario"]
                
                # Gestisci formato ISO con e senza indicatore di zona
                try:
                    # Prova a usare fromisoformat (Python 3.7+)
                    data_partita = datetime.fromisoformat(data_str.replace('Z', '+00:00')).date()
                except (ValueError, AttributeError):
                    # Fallback per versioni precedenti o formati non standard
                    if 'T' in data_str:
                        data_str = data_str.split('T')[0]  # Estrai solo la parte della data
                    data_partita = datetime.strptime(data_str, "%Y-%m-%d").date()
                    
                if data_partita == oggi:
                    partite_oggi.append(partita)
            except (ValueError, KeyError) as e:
                logger.error(f"Errore nel filtraggio per data: {e}")
                continue
        
        if not partite_oggi:
            return "⚠️ *Non ci sono partite in programma per oggi!* Prova domani o seleziona un'altra opzione."
        
        # Logica di selezione in base al tipo di schedina
        if tipo_schedina == 'facile':
            # Quote basse (alta probabilità)
            partite_filtrate = filtra_partite_per_quota(partite_oggi, 1.01, 1.80)
        elif tipo_schedina == 'media':
            # Quote medie (probabilità media)
            partite_filtrate = filtra_partite_per_quota(partite_oggi, 1.60, 2.50)
        elif tipo_schedina == 'difficile':
            # Quotes alte (bassa probabilità)
            partite_filtrate = filtra_partite_per_quota(partite_oggi, 2.50, 10.00)
        elif tipo_schedina == 'fortunata':
            # Mix di quote, con prevalenza di quote medie
            partite_filtrate = partite_oggi
        else:
            return "⚠️ *Errore*: Tipo di schedina non valido."
        
        # Verifica che ci siano abbastanza partite filtrate
        if len(partite_filtrate) < num_partite:
            messaggio = f"⚠️ *Ci sono solo {len(partite_filtrate)} partite disponibili oggi per questo tipo di schedina.*\n\n"
            
            if len(partite_filtrate) == 0:
                return messaggio + "Prova un altro tipo di schedina."
            
            num_partite = len(partite_filtrate)
        else:
            messaggio = ""
        
        # Seleziona num_partite partite casuali tra quelle filtrate
        partite_selezionate = random.sample(partite_filtrate, num_partite)
        
        # Seleziona i pronostici
        pronostici = []
        quota_totale = 1.0
        
        for partita in partite_selezionate:
            # Ottieni la coppia (segno, quota) dal pronostico
            segno, quota = seleziona_pronostico(partita, tipo_schedina)
            quota_totale *= quota
            
            # Formatta l'orario in italiano (ore e minuti)
            # Converti dal formato ISO e considera il fuso orario italiano (+2 in estate, +1 in inverno)
            try:
                data_str = partita["orario"]
                
                # Gestisci formato ISO con e senza indicatore di zona
                try:
                    # Prova a usare fromisoformat (Python 3.7+)
                    data_ora_utc = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    # Fallback per versioni precedenti o formati non standard
                    data_ora_utc = datetime.strptime(data_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                
                # Aggiungi l'offset del fuso orario italiano
                # Determina automaticamente se è ora legale o solare
                now = datetime.now()
                # In Italia l'ora legale è attiva dalla fine di marzo alla fine di ottobre
                is_dst = 3 <= now.month <= 10
                offset_ore = 2 if is_dst else 1
                data_ora_it = data_ora_utc + timedelta(hours=offset_ore)
                
                # Formatta in stile italiano: gg/mm ore:minuti
                orario_formattato = data_ora_it.strftime("%d/%m %H:%M")
            except Exception as e:
                logger.error(f"Errore nella formattazione dell'orario: {e}")
                orario_formattato = "Oggi"
            
            pronostici.append({
                'match': partita['match'],
                'orario': orario_formattato,
                'pronostico': segno,
                'quota': quota,
                'competizione': partita.get('competizione', 'Calcio')
            })
        
        # Formatta la schedina
        schedina_formattata = formatta_schedina(pronostici, tipo_schedina, quota_totale)
        
        # Aggiungi il messaggio di avviso se necessario
        if messaggio:
            return messaggio + schedina_formattata
        
        return schedina_formattata
    
    except Exception as e:
        logger.error(f"Errore nella generazione della schedina: {str(e)}")
        return f"⚠️ *Errore*: Si è verificato un problema durante la generazione della schedina. Dettaglio: {str(e)}"

def formatta_schedina(pronostici, tipo_schedina, quota_totale):
    """Formatta la schedina in un messaggio Markdown."""
    # Intestazione
    schedina = f"🎟️ *Schedina {tipo_schedina.upper()} pronta per te:*\n\n"
    
    # Partite
    for i, p in enumerate(pronostici, 1):
        # Traduci il pronostico in italiano per una migliore leggibilità
        pronostico_testo = p['pronostico']
        if pronostico_testo == "1":
            pronostico_tradotto = "1 (Casa)"
        elif pronostico_testo == "X":
            pronostico_tradotto = "X (Pareggio)"
        elif pronostico_testo == "2":
            pronostico_tradotto = "2 (Trasferta)"
        else:
            pronostico_tradotto = pronostico_testo
            
        schedina += (
            f"*{i}. {p['match']}*\n"
            f"🏆 {p.get('competizione', 'Calcio')} | ⏰ *{p['orario']} (IT)*\n"
            f"🎯 Pronostico: *{pronostico_tradotto}* (Quota: {p['quota']})\n\n"
        )
    
    # Quota totale
    quota_totale_formattata = f"{quota_totale:.2f}".rstrip('0').rstrip('.') if '.' in f"{quota_totale:.2f}" else f"{quota_totale:.2f}"
    schedina += f"📊 *Quota totale: {quota_totale_formattata}*\n"
    
    # Vincita potenziale su €10
    vincita_potenziale = quota_totale * 10
    vincita_formattata = f"{vincita_potenziale:.2f}".rstrip('0').rstrip('.') if '.' in f"{vincita_potenziale:.2f}" else f"{vincita_potenziale:.2f}"
    schedina += f"💰 Vincita potenziale su €10: *€{vincita_formattata}*\n\n"
    
    # Note finali
    oggi = datetime.now().strftime("%d/%m/%Y")
    schedina += f"📅 *Schedina del {oggi}*\n"
    schedina += f"⚠️ _Gioca responsabilmente. Le quote potrebbero variare._"
    
    return schedina 