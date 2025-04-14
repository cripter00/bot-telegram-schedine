# Bot Telegram per Schedine di Calcio

Questo bot Telegram genera schedine di calcio con quattro diverse modalità, ottiene quote reali da API multiple e invia schedine automaticamente a un canale Telegram.

## 🚀 Funzionalità

### Generazione intelligente di schedine
- 🟢 **Schedina Facile**: Quote basse (1.20-1.50), alta probabilità di vincita
- 🟡 **Schedina Media**: Quote medie (1.60-2.50), probabilità media
- 🔴 **Schedina Difficile**: Quote alte (2.50-5.00), bassa probabilità ma alto guadagno
- 🍀 **Schedina Fortunata**: Basata su analisi statistiche e tendenze
- 📊 Personalizzazione: da 2 a 6 partite per schedina

### Sistema multi-API per le quote
- 🔄 Quote ottenute in tempo reale da tre diverse API:
  - football-data.org
  - API-Football
  - TheOddsAPI
- 💪 Fallback automatico: se un'API fallisce, prova con la successiva
- ✅ Validazione rigorosa delle quote (solo quote reali > 1.0)
- 🔍 Filtraggio per data: solo partite di oggi e domani

### Invio automatico a canale Telegram
- 📅 Invio programmato di tutte le schedine (facile, media, difficile, fortunata):
  - **Mattina**: a partire dalle 8:45 (con intervalli di 10 minuti)
  - **Pomeriggio**: a partire dalle 14:00 (con intervalli di 10 minuti)
  - **Sera**: a partire dalle 19:00 (con intervalli di 10 minuti)
- 🌍 Supporto fuso orario: rispetta sempre l'ora italiana (Europe/Rome)
- 🎰 Invio automatico di promozioni casinò ogni 6 ore

### Altre caratteristiche
- 🔄 Aggiornamento quote ogni 30 minuti
- 🤖 Interfaccia utente interattiva con pulsanti inline
- 📱 Formattazione avanzata dei messaggi con Markdown
- 🛡️ Gestione robusta degli errori e logging dettagliato

## 📋 Requisiti

- Python 3.7+ (consigliato 3.9+)
- Connessione internet stabile
- Account Telegram
- Canale Telegram (per l'invio automatico delle schedine)
- API keys per i servizi delle quote

## 💬 Comandi e Interazione

### Comandi principali
- `/start` o `/menu` - Mostra il menu principale con tutte le opzioni
- `/schedina_facile` - Genera una schedina con quote basse (vecchio metodo, preferire il menu)
- `/schedina_media` - Genera una schedina con quote medie (vecchio metodo, preferire il menu)
- `/schedina_difficile` - Genera una schedina con quote alte (vecchio metodo, preferire il menu)
- `/schedina_fortunata` - Genera una schedina basata su analisi (vecchio metodo, preferire il menu)

### Menu interattivo
Il bot utilizza principalmente un'interfaccia a pulsanti che permette di:
- Selezionare il tipo di schedina (Facile, Media, Difficile, Fortunata)
- Scegliere il numero di partite (da 2 a 6)
- Visualizzare promozioni casinò
- Ottenere informazioni sul funzionamento del bot

## 🔧 Installazione locale

1. **Clona il repository o scarica i file**:
   ```bash
   git clone https://github.com/username/bot-schedine-calcio.git
   cd bot-schedine-calcio
   ```

2. **Crea un ambiente virtuale (opzionale ma consigliato)**:
   ```bash
   python -m venv venv
   
   # Su Windows
   venv\Scripts\activate
   
   # Su macOS/Linux
   source venv/bin/activate
   ```

3. **Installa le dipendenze**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura le API keys**:
   - Modifica i valori delle API keys in `bot/quote_scraper.py`
   - football-data.org: `api_key = "TUA_API_KEY_QUI"`  
   - API-Football: `api_key = "TUA_API_KEY_QUI"`
   - TheOddsAPI: `api_key = "TUA_API_KEY_QUI"`

5. **Configura il canale Telegram**:
   - Apri `bot/main.py`
   - Modifica `CHANNEL_ID = "@tuocanaletelegram"` con l'ID o username del tuo canale
   - Aggiungi il bot come amministratore del canale con permessi di invio messaggi

6. **Avvia il bot**:
   ```bash
   python bot/main.py
   ```

## 🌐 Installazione su PythonAnywhere

1. **Registrati o accedi a PythonAnywhere**:
   - Vai su [pythonanywhere.com](https://www.pythonanywhere.com)
   - Crea un account gratuito se non ne hai già uno

2. **Carica i file del bot**:
   
   **Via Git**:
   ```bash
   # Apri una console Bash
   git clone https://github.com/username/bot-schedine-calcio.git
   ```
   
   **Oppure carica manualmente**:
   - Vai alla sezione "Files" nel dashboard
   - Carica tutti i file del bot

3. **Installa le dipendenze**:
   ```bash
   pip install pyTelegramBotAPI==4.7.0 APScheduler==3.9.1 requests>=2.31.0 pytz --user
   ```

4. **Configura le API keys e il canale**:
   - Modifica i file come nelle istruzioni per l'installazione locale

5. **Crea un task sempre attivo**:
   - Vai alla sezione "Tasks" nel dashboard
   - Scegli "Add a scheduled task"
   - Seleziona "Always on" come tipo di task
   - Nel campo "Command", inserisci:
     ```
     python3 /home/tuousername/tuoprogetto/bot/main.py
     ```
   - Assicurati di usare il percorso completo al tuo file `main.py`
   - Clicca su "Create"

6. **Verifica il log**:
   - Nella sezione "Tasks", troverai il link al file di log
   - Monitoralo per assicurarti che il bot funzioni correttamente

## 🔍 Risoluzione problemi comuni

- **Quote non aggiornate**: Verifica che le API keys siano valide e che i limiti di richieste non siano stati superati
- **Bot non risponde**: Controlla che il token del bot sia corretto e che il bot non sia stato arrestato
- **Errori di connessione**: Assicurati che il server abbia accesso a internet
- **Problemi con fuso orario**: Verifica che il modulo `pytz` sia installato correttamente

## 📅 Manutenzione

- Controlla regolarmente i file di log per eventuali errori
- Verifica che le API keys non siano scadute
- Aggiorna periodicamente le dipendenze con `pip install -r requirements.txt --upgrade`

## 📄 File di configurazione

- `requirements.txt`: Dipendenze Python
```
pyTelegramBotAPI==4.7.0
APScheduler==3.9.1
requests>=2.31.0
pytz
```

- `bot/promo.txt`: File contenente le promozioni casinò (separare ogni promozione con `---`)

## 📱 Personalizzazione

- **Promozioni Casinò**: Modifica il file `bot/promo.txt` per aggiungere o modificare le promozioni. Separa ogni promozione con `---`.
- **Orari di invio**: Gli orari di invio automatico delle schedine possono essere modificati nel file `bot/main.py` nella sezione delle pianificazioni dello scheduler.
- **Token del bot**: Aggiorna il valore di `TOKEN` nel file `bot/main.py` con il token del tuo bot Telegram.

## 📝 Note legali

Questo bot è pensato per scopi informativi e ricreativi. Il gioco d'azzardo può creare dipendenza. Gioca responsabilmente e rispetta le leggi del tuo paese relative al gioco d'azzardo. 