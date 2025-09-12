# 📊 Sistema di Generazione Segnali Trading

Questa cartella contiene tutti i file e moduli dedicati alla generazione di segnali di trading per la piattaforma AI Cash-Revolution.

## 🎯 Architettura del Sistema

Il sistema di generazione segnali è basato su **AdvancedSignalAnalyzer** come componente principale, supportato da moduli specializzati per analisi sentiment, integrazione OANDA e enhancement quantitativi.

---

## 📁 Descrizione dei File

### 🔥 **CORE - File Principale**

#### `advanced_signal_analyzer.py` ⭐ **FILE PRINCIPALE**
- **Funzione**: Motore principale per la generazione di segnali trading avanzati
- **Caratteristiche**:
  - Analisi multi-timeframe (M1, M5, M15, H1, H4, D1)  
  - Integrazione sentiment analysis completa
  - Smart money detection e volume profile analysis
  - Calcolo automatico entry/stop-loss/take-profit con ATR
  - Reasoning AI in italiano con dati 0DTE e sentiment
  - Gestione risk/reward ratio ottimizzata
- **Output**: Segnali BUY/SELL con analisi completa e AI reasoning
- **Status**: ✅ ATTIVO - Sistema principale in uso

---

### 📈 **SENTIMENT ANALYSIS - Modulo Completo**

#### `sentiment_analysis/` (Cartella)
Modulo completo v6.0 per analisi sentiment multi-fonte

##### `sentiment_analysis/__init__.py`
- **Funzione**: Inizializzazione modulo sentiment v6.0
- **Exports**: NewsProvider, SocialMediaAnalyzer, OptionsFlowAnalyzer, SentimentAggregator

##### `sentiment_analysis/sentiment_aggregator.py`
- **Funzione**: Aggregatore principale che combina tutte le fonti sentiment
- **Caratteristiche**:
  - Weighted scoring dinamico per strumento
  - Integrazione news + social + options flow
  - Confidence scoring e trading implications
  - Output formattato per AI reasoning
- **Input**: Dati da news, social media, options flow
- **Output**: MarketSentiment aggregato con score e confidence

##### `sentiment_analysis/news_sentiment.py`
- **Funzione**: Analisi sentiment notizie finanziarie in tempo reale
- **Fonti**: Yahoo Finance, Finviz
- **Caratteristiche**:
  - Keywords bullish/bearish per scoring
  - Instrument-specific keyword mapping
  - Relevance scoring per pertinenza notizie
  - Caching per performance
- **Output**: Sentiment news con score -1.0 a +1.0

##### `sentiment_analysis/social_sentiment.py`
- **Funzione**: Analisi sentiment social media (Twitter/X, Reddit)
- **Caratteristiche**:
  - Simulazione post social realistici con engagement
  - Emoji e hashtag analysis
  - Platform-specific sentiment calculation
  - Volume e reach metrics
- **Output**: Sentiment social aggregato per strumento

##### `sentiment_analysis/options_flow.py`
- **Funzione**: Analisi flussi opzioni e unusual activity
- **Caratteristiche**:
  - Calcolo Greeks (Delta, Gamma, Theta, Vega)
  - Unusual activity detection con significance scoring
  - Flow classification (sweeps, blocks, unusual)
  - Premium e volume analysis
- **Output**: Options flow data con significance metrics

---

### 🔌 **INTEGRAZIONE DATI**

#### `oanda_api_client.py`
- **Funzione**: Client ufficiale per OANDA v20 API
- **Caratteristiche**:
  - Connessione sicura a OANDA REST API
  - Fetch candlestick data multi-timeframe
  - Current pricing e spread information
  - Symbol mapping e validation
  - Error handling e rate limiting
- **Status**: ✅ ATTIVO - Fonte dati primaria

#### `quantistes_integration.py`
- **Funzione**: Integrazione avanzata per analisi quantitative indici
- **Caratteristiche**:
  - Zero-DTE options analysis per SPX/QQQ/DIA
  - Gamma exposure levels calculation
  - Dealer positioning simulation
  - Enhanced confidence scoring per indici
  - Put/Call ratio e volatility regimes
- **Target**: Indici US (SPX500, NAS100, US30)
- **Status**: ✅ ATTIVO - Enhancement per indici

---

### 🏛️ **LEGACY SYSTEM (Non in uso)**

#### `oanda_signal_engine.py` ⚠️ **DEPRECATO**
- **Funzione**: Vecchio engine di generazione segnali con Gemini AI
- **Motivo deprecazione**: Causava inconsistenze con AdvancedSignalAnalyzer
- **Problemi risolti**: 
  - Doppio sistema AI (Gemini + AdvancedSignalAnalyzer)
  - Descrizioni contraddittorie (SELL header vs HOLD description)
  - Mancanza integrazione sentiment
- **Status**: ❌ RIMOSSO dal sistema principale (main.py)

---

### 🧪 **TESTING E DEBUG**

#### `test_local_signal_generation.py`
- **Funzione**: Test locale per AdvancedSignalAnalyzer
- **Caratteristiche**:
  - Verifica inizializzazione sentiment analysis
  - Test symbols problematici (NAS100, SPX500, US30)
  - Debug content verification (0DTE, sentiment presence)
  - Error handling validation
- **Uso**: `python test_local_signal_generation.py`

---

## 🔄 Flusso di Generazione Segnale

```mermaid
graph TD
    A[Frontend Request] --> B[AdvancedSignalAnalyzer]
    B --> C[OANDA API Client]
    B --> D[Sentiment Aggregator]
    D --> E[News Sentiment]
    D --> F[Social Sentiment] 
    D --> G[Options Flow]
    B --> H[Quantistes Integration]
    B --> I[Multi-Timeframe Analysis]
    I --> J[Smart Money Detection]
    I --> K[Volume Profile]
    B --> L[Signal Generation]
    L --> M[AI Reasoning in Italiano]
    M --> N[Database Storage]
    N --> O[API Response]
```

## 📋 Status dei Componenti

| Componente | Status | Funzione |
|------------|--------|----------|
| AdvancedSignalAnalyzer | ✅ ATTIVO | Motore principale |
| Sentiment Analysis | ✅ ATTIVO | Analisi sentiment completa |
| OANDA API Client | ✅ ATTIVO | Fonte dati market |
| Quantistes Integration | ✅ ATTIVO | Enhancement indici |
| OANDASignalEngine | ❌ DEPRECATO | Vecchio sistema |

## 🎯 Caratteristiche Principali

### ✅ **Funzionalità Attive**
- **Multi-timeframe analysis** con confluence scoring
- **Sentiment analysis** da news + social + options
- **0DTE options analysis** per indici US
- **Smart money detection** con order blocks e FVG
- **AI reasoning** in italiano con dati contestuali
- **Risk management** automatico con ATR
- **Error handling** specifico per asset class

### 🔧 **Configurazione**
- **API Keys richieste**: OANDA_API_KEY, GEMINI_API_KEY
- **Timeframe supportati**: M1, M5, M15, H1, H4, D1
- **Asset supportati**: Forex, Metalli, Indici US/EUR
- **Output**: Segnali BUY/SELL con confidence 60%+

## 📚 **Note di Sviluppo**

- Il sistema usa **SOLO AdvancedSignalAnalyzer** dal commit 389a63a
- Tutti i riferimenti al vecchio OANDASignalEngine sono stati rimossi
- Il sentiment analysis è integrato nativamente nel flusso principale  
- I segnali HOLD sono automaticamente rifiutati (solo BUY/SELL actionable)

---

**Ultimo aggiornamento**: 2025-09-12  
**Versione sistema**: 2.0.1 - Single Source Signal Generation