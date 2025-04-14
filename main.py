#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Nota: per eseguire questo bot in produzione con Python 3.13+
# è necessario utilizzare una versione più recente di python-telegram-bot 
# che non dipenda dal modulo imghdr (rimosso in Python 3.13)

import logging
import json
import telebot
from telebot import types
from telebot import apihelper
from apscheduler.schedulers.background import BackgroundScheduler
import os
import random
from datetime import datetime, time
import pytz  # Importiamo il modulo pytz per gestire i fusi orari

from quote_scraper import aggiorna_quote
from schedine import genera_schedina
from promo_scheduler import invia_promo_programmata

# Configurazione del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fuso orario italiano
fuso_orario_italia = pytz.timezone('Europe/Rome')

# Token del bot Telegram
TOKEN = ""

# ID del canale Telegram dove inviare le schedine automatiche
CHANNEL_ID = "@"  # Sostituisci con l'ID o username del tuo canale

# Inizializza il bot
bot = telebot.TeleBot(TOKEN, parse_mode='Markdown')

# Dizionario per memorizzare gli stati degli utenti
user_states = {}

# Funzione per creare il menu principale
def crea_menu_principale():
    """Crea la tastiera inline per il menu principale."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_schedina_facile = types.InlineKeyboardButton("🟢 Schedina Facile", callback_data="schedina_facile")
    btn_schedina_media = types.InlineKeyboardButton("🟡 Schedina Media", callback_data="schedina_media")
    btn_schedina_difficile = types.InlineKeyboardButton("🔴 Schedina Difficile", callback_data="schedina_difficile")
    btn_schedina_fortunata = types.InlineKeyboardButton("🍀 Schedina Fortunata", callback_data="schedina_fortunata")
    btn_promo = types.InlineKeyboardButton("🎰 Promozioni Casinò", callback_data="promo")
    btn_info = types.InlineKeyboardButton("ℹ️ Info", callback_data="info")
    
    markup.add(btn_schedina_facile, btn_schedina_media)
    markup.add(btn_schedina_difficile, btn_schedina_fortunata)
    markup.add(btn_promo, btn_info)
    
    return markup

# Funzione per creare la tastiera di selezione numero partite
def crea_tastiera_num_partite(tipo_schedina):
    """Crea la tastiera per selezionare il numero di partite."""
    markup = types.InlineKeyboardMarkup(row_width=4)
    
    btn_2 = types.InlineKeyboardButton("2️⃣", callback_data=f"num_{tipo_schedina}_2")
    btn_3 = types.InlineKeyboardButton("3️⃣", callback_data=f"num_{tipo_schedina}_3")
    btn_4 = types.InlineKeyboardButton("4️⃣", callback_data=f"num_{tipo_schedina}_4")
    btn_5 = types.InlineKeyboardButton("5️⃣", callback_data=f"num_{tipo_schedina}_5")
    btn_6 = types.InlineKeyboardButton("6️⃣", callback_data=f"num_{tipo_schedina}_6")
    btn_menu = types.InlineKeyboardButton("🔙 Menu", callback_data="menu")
    
    markup.add(btn_2, btn_3, btn_4, btn_5, btn_6)
    markup.add(btn_menu)
    
    return markup

# Funzione per creare un bottone di ritorno al menu
def crea_bottone_menu():
    """Crea un bottone per tornare al menu principale."""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Torna al Menu", callback_data="menu"))
    return markup

# Funzione per il comando /start
@bot.message_handler(commands=['start', 'menu'])
def start(message):
    """Invia un messaggio di benvenuto con il menu principale."""
    user_first_name = message.from_user.first_name
    message_text = (
        f"👋 *Benvenuto {user_first_name} nel Bot Schedine Calcio!*\n\n"
        f"🎯 *Seleziona un'opzione dal menu:*\n\n"
        f"🟢 *Schedina Facile* - Quote basse (1.20-1.50)\n"
        f"🟡 *Schedina Media* - Quote medie (1.60-2.50)\n"
        f"🔴 *Schedina Difficile* - Quote alte (2.50-5.00)\n"
        f"🍀 *Schedina Fortunata* - Basata su analisi e tendenze\n"
        f"🎰 *Promozioni* - Mostra offerte casinò\n\n"
        f"⚠️ _Ricorda di giocare responsabilmente!_"
    )
    
    bot.send_message(
        message.chat.id, 
        message_text, 
        reply_markup=crea_menu_principale()
    )

# Gestore di callback per i bottoni
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Gestisce le callback dai bottoni inline."""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    callback_data = call.data
    
    try:
        # Tipo di schedina selezionato
        if callback_data in ["schedina_facile", "schedina_media", "schedina_difficile", "schedina_fortunata"]:
            tipo_schedina = callback_data.split("_")[1]
            
            messaggio = (
                f"Hai selezionato: *Schedina {tipo_schedina.capitalize()}*\n\n"
                f"Quante partite vuoi nella schedina?\n"
                f"Seleziona un numero da 2 a 6:"
            )
            
            bot.edit_message_text(
                chat_id=chat_id, 
                message_id=message_id,
                text=messaggio,
                reply_markup=crea_tastiera_num_partite(tipo_schedina),
                parse_mode='Markdown'
            )
        
        # Numero di partite selezionato
        elif callback_data.startswith("num_"):
            parti = callback_data.split("_")
            tipo_schedina = parti[1]
            num_partite = int(parti[2])
            
            # Messaggio di attesa
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"⏳ Sto generando la tua schedina {tipo_schedina.upper()} con {num_partite} partite...",
                parse_mode='Markdown'
            )
            
            try:
                # Genera la schedina
                schedina = genera_schedina(tipo_schedina, num_partite)
                
                # Invia la schedina con bottone di ritorno al menu
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=schedina,
                    reply_markup=crea_bottone_menu(),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Errore nella generazione della schedina: {e}")
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="❌ Mi dispiace, si è verificato un errore nella generazione della schedina.",
                    reply_markup=crea_bottone_menu(),
                    parse_mode='Markdown'
                )
        
        # Richiesta promozioni
        elif callback_data == "promo":
            try:
                with open('bot/promo.txt', 'r', encoding='utf-8') as file:
                    promos = file.read().strip().split('---')
                
                # Scegli una promo casuale
                promo_text = random.choice(promos).strip()
                
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=promo_text,
                    reply_markup=crea_bottone_menu(),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Errore nell'invio della promo: {e}")
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="❌ Mi dispiace, non riesco a recuperare le promozioni al momento.",
                    reply_markup=crea_bottone_menu(),
                    parse_mode='Markdown'
                )
        
        # Informazioni
        elif callback_data == "info":
            info_text = (
                "*ℹ️ Informazioni sul Bot*\n\n"
                "Questo bot ti permette di generare schedine calcistiche con diverse difficoltà:\n\n"
                "🟢 *Schedina Facile* - Quote basse (1.20-1.50), alta probabilità di vincita\n"
                "🟡 *Schedina Media* - Quote medie (1.60-2.50), probabilità media\n"
                "🔴 *Schedina Difficile* - Quote alte (2.50-5.00), bassa probabilità ma alto guadagno\n"
                "🍀 *Schedina Fortunata* - Seleziona le partite in base a trend e statistiche\n\n"
                "Le quote vengono aggiornate ogni 30 minuti dai principali bookmakers.\n\n"
                "⚠️ *Ricorda*: Il gioco deve essere un divertimento, non un problema. Gioca responsabilmente."
            )
            
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=info_text,
                reply_markup=crea_bottone_menu(),
                parse_mode='Markdown'
            )
        
        # Ritorno al menu principale
        elif callback_data == "menu":
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="🎯 *Menu Principale*\nSeleziona un'opzione:",
                reply_markup=crea_menu_principale(),
                parse_mode='Markdown'
            )
        
        # Risponde alla callback per evitare l'icona di attesa
        bot.answer_callback_query(call.id)
    
    except apihelper.ApiTelegramException as e:
        # Gestisce sia l'errore "message is not modified" sia l'errore "query is too old"
        if "message is not modified" in str(e):
            # L'utente ha premuto lo stesso pulsante più volte
            logger.debug(f"Ignorato errore 'message is not modified': {e}")
            # Prova comunque a rispondere alla callback
            try:
                bot.answer_callback_query(call.id)
            except:
                pass
        elif "query is too old" in str(e) or "query ID is invalid" in str(e):
            # La callback è scaduta (troppo vecchia) o l'ID non è valido
            logger.debug(f"Ignorato errore di callback scaduta: {e}")
            # Non provare a rispondere di nuovo alla callback, è già scaduta
        else:
            # Altri errori dell'API di Telegram vanno gestiti o loggati
            logger.error(f"Errore API Telegram: {e}")
            try:
                bot.answer_callback_query(call.id)
            except:
                pass
    
    except Exception as e:
        # Errori generici
        logger.error(f"Errore generico nel gestore callback: {e}")
        try:
            bot.answer_callback_query(call.id)
        except:
            pass

# Mantiene i vecchi gestori di comandi per retrocompatibilità
@bot.message_handler(commands=['schedina_facile', 'schedina_media', 'schedina_difficile', 'schedina_fortunata', 'promo'])
def comandi_legacy(message):
    """Gestisce i vecchi comandi reindirizzando al nuovo menu."""
    start(message)

# Gestisce i messaggi di testo
@bot.message_handler(func=lambda message: True)
def gestisci_messaggio(message):
    """Gestisce i messaggi di testo in arrivo."""
    # Qualsiasi input di testo porta al menu principale
    start(message)

def invia_schedina_canale(tipo_schedina, momento_giornata):
    """
    Invia una schedina programmata al canale specificato.
    
    Args:
        tipo_schedina: Il tipo di schedina da generare (facile, media, difficile, fortunata)
        momento_giornata: Stringa che indica il momento della giornata (mattina, pomeriggio, sera)
    """
    try:
        # Genera una schedina con 6 partite
        schedina = genera_schedina(tipo_schedina, 6)
        
        # Aggiungi un'intestazione
        header = f"📊 *SCHEDINA {tipo_schedina.upper()} DEL {momento_giornata.upper()}*\n"
        footer = "\n\n🤖 _Generata automaticamente dal bot - Gioca responsabilmente!_"
        
        # Messaggio completo
        messaggio = header + schedina + footer
        
        # Invia al canale
        bot.send_message(CHANNEL_ID, messaggio, parse_mode='Markdown')
        logger.info(f"Inviata schedina {tipo_schedina} del {momento_giornata} al canale {CHANNEL_ID}")
    
    except Exception as e:
        logger.error(f"Errore nell'invio della schedina {tipo_schedina} al canale: {e}")

def invia_schedina_facile_mattina():
    """Invia una schedina facile al mattino."""
    invia_schedina_canale("facile", "mattina")

def invia_schedina_media_mattina():
    """Invia una schedina media al mattino."""
    invia_schedina_canale("media", "mattina")

def invia_schedina_difficile_mattina():
    """Invia una schedina difficile al mattino."""
    invia_schedina_canale("difficile", "mattina")

def invia_schedina_fortunata_mattina():
    """Invia una schedina fortunata al mattino."""
    invia_schedina_canale("fortunata", "mattina")

def invia_schedina_facile_pomeriggio():
    """Invia una schedina facile al pomeriggio."""
    invia_schedina_canale("facile", "pomeriggio")

def invia_schedina_media_pomeriggio():
    """Invia una schedina media al pomeriggio."""
    invia_schedina_canale("media", "pomeriggio")

def invia_schedina_difficile_pomeriggio():
    """Invia una schedina difficile al pomeriggio."""
    invia_schedina_canale("difficile", "pomeriggio")

def invia_schedina_fortunata_pomeriggio():
    """Invia una schedina fortunata al pomeriggio."""
    invia_schedina_canale("fortunata", "pomeriggio")

def invia_schedina_facile_sera():
    """Invia una schedina facile alla sera."""
    invia_schedina_canale("facile", "sera")

def invia_schedina_media_sera():
    """Invia una schedina media alla sera."""
    invia_schedina_canale("media", "sera")

def invia_schedina_difficile_sera():
    """Invia una schedina difficile alla sera."""
    invia_schedina_canale("difficile", "sera")

def invia_schedina_fortunata_sera():
    """Invia una schedina fortunata alla sera."""
    invia_schedina_canale("fortunata", "sera")

def invia_promo_programmata_tutti():
    """Invio programmato di promozioni."""
    try:
        from promo_scheduler import carica_promozioni
        promozioni = carica_promozioni()
        
        if not promozioni:
            logger.warning("Nessuna promozione disponibile.")
            return
        
        promo_text = random.choice(promozioni)
        logger.info(f"Invio programmato di promozione: {promo_text[:50]}...")
        
        # Invia la promozione al canale specificato
        try:
            bot.send_message(CHANNEL_ID, promo_text, parse_mode='Markdown')
            logger.info(f"Promozione inviata al canale {CHANNEL_ID}")
        except Exception as e:
            logger.error(f"Errore nell'invio della promozione al canale {CHANNEL_ID}: {e}")
        
    except Exception as e:
        logger.error(f"Errore nell'invio programmato della promozione: {e}")

def main():
    """Avvia il bot."""
    # Avvia lo scheduler in background
    scheduler = BackgroundScheduler(timezone=fuso_orario_italia)
    
    # Pianifica l'aggiornamento delle quote ogni 30 minuti
    scheduler.add_job(aggiorna_quote, 'interval', minutes=30)
    
    # Pianifica l'invio delle schedine al canale - MATTINA (8:45)
    scheduler.add_job(invia_schedina_facile_mattina, 'cron', hour=8, minute=45)  # Alle 8:45
    scheduler.add_job(invia_schedina_media_mattina, 'cron', hour=8, minute=55)  # Alle 8:55
    scheduler.add_job(invia_schedina_difficile_mattina, 'cron', hour=9, minute=5)  # Alle 9:05
    scheduler.add_job(invia_schedina_fortunata_mattina, 'cron', hour=9, minute=15)  # Alle 9:15
    
    # Pianifica l'invio delle schedine al canale - POMERIGGIO (14:00)
    scheduler.add_job(invia_schedina_facile_pomeriggio, 'cron', hour=14, minute=0)  # Alle 14:00
    scheduler.add_job(invia_schedina_media_pomeriggio, 'cron', hour=14, minute=10)  # Alle 14:10
    scheduler.add_job(invia_schedina_difficile_pomeriggio, 'cron', hour=14, minute=20)  # Alle 14:20
    scheduler.add_job(invia_schedina_fortunata_pomeriggio, 'cron', hour=14, minute=30)  # Alle 14:30
    
    # Pianifica l'invio delle schedine al canale - SERA (19:00)
    scheduler.add_job(invia_schedina_facile_sera, 'cron', hour=19, minute=0)  # Alle 19:00
    scheduler.add_job(invia_schedina_media_sera, 'cron', hour=19, minute=10)  # Alle 19:10
    scheduler.add_job(invia_schedina_difficile_sera, 'cron', hour=19, minute=20)  # Alle 19:20
    scheduler.add_job(invia_schedina_fortunata_sera, 'cron', hour=19, minute=30)  # Alle 19:30
    
    # Pianifica l'invio delle promo ogni 6 ore
    scheduler.add_job(invia_promo_programmata_tutti, 'interval', hours=6)
    
    # Avvia lo scheduler
    scheduler.start()
    
    # Stampa informazioni sul fuso orario
    ora_locale = datetime.now(fuso_orario_italia)
    logger.info(f"Bot avviato con fuso orario italiano: {ora_locale.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    
    # Esegui l'aggiornamento delle quote all'avvio
    try:
        aggiorna_quote()
    except Exception as e:
        logger.error(f"Errore nell'aggiornamento iniziale delle quote: {e}")

    logger.info("Bot avviato. In attesa di messaggi...")
    print("Bot avviato. Premi Ctrl+C per terminare.")
    
    # Avvia il bot in modalità polling
    bot.infinity_polling()

if __name__ == '__main__':
    main() 
