#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import os

# Configurazione del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def carica_promozioni():
    """
    Carica le promozioni dal file promozioni.
    Se il file non esiste, crea promozioni di esempio.
    """
    promo_file_path = "bot/promo.txt"
    
    # Se il file non esiste, crealo con promozioni di esempio
    if not os.path.exists(promo_file_path):
        promozioni_esempio = [
            "🎰 *CASINO BONUS SPECIALE* 🎰\n\n"
            "💰 Ricevi *100€ GRATIS* sul primo deposito!\n"
            "🔥 Codice: *BENVENUTO100*\n\n"
            "✅ Registrati ora: casinobonus.it\n"
            "⏰ Offerta valida fino al 31/12/2025",
            
            "♠️ *NUOVI GIOCHI BLACKJACK* ♠️\n\n"
            "🎲 Prova il nuovo tavolo VIP con *croupier dal vivo*\n"
            "💵 Puntata minima: 5€\n"
            "💎 Puntata massima: 10.000€\n\n"
            "🎮 Gioca ora: blackjackvip.it",
            
            "🎡 *GIRI GRATIS SLOT MACHINE* 🎡\n\n"
            "🎰 *50 FREE SPINS* sulla nuova slot Book of Fortune!\n"
            "💸 Nessun deposito richiesto\n"
            "🏆 Vincita massima: 500€\n\n"
            "⚡️ Usa il codice: *FORTUNE50*\n"
            "⏳ Offerta valida solo per 24 ore"
        ]
        
        with open(promo_file_path, "w", encoding="utf-8") as f:
            f.write("\n---\n".join(promozioni_esempio))
        
        return promozioni_esempio
    
    # Altrimenti, carica le promozioni dal file esistente
    try:
        with open(promo_file_path, "r", encoding="utf-8") as f:
            promozioni = f.read().strip().split("---")
            return [promo.strip() for promo in promozioni if promo.strip()]
    except Exception as e:
        logger.error(f"Errore nel caricamento delle promozioni: {e}")
        return []

def invia_promo_programmata(bot):
    """
    Funzione per inviare promozioni programmate.
    Questa funzione è mantenuta per retrocompatibilità.
    Nella versione corrente con telebot, si utilizza la funzione
    invia_promo_programmata_tutti() definita in main.py.
    """
    try:
        promozioni = carica_promozioni()
        
        if not promozioni:
            logger.warning("Nessuna promozione disponibile.")
            return
        
        # Seleziona una promozione casuale
        promo_text = random.choice(promozioni)
        
        logger.info(f"Invio programmato di promozione: {promo_text[:50]}...")
        return True
    
    except Exception as e:
        logger.error(f"Errore nell'invio programmato della promozione: {e}")
        return False

if __name__ == "__main__":
    # Se eseguito direttamente, carica solo le promozioni
    promozioni = carica_promozioni()
    print(f"Caricate {len(promozioni)} promozioni.") 