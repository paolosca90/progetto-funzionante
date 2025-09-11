# 📈 Strategia di Generazione Segnali Trading - Documentazione Completa

## 🔍 Panoramica del Sistema

Il sistema di generazione segnali implementa un approccio multi-layered che combina analisi tecnica avanzata, intelligenza artificiale e gestione del rischio professionale per generare segnali di trading di alta qualità.

## 🏗️ Architettura del Sistema

### 📁 File Principali e Responsabilità

#### **1. `oanda_signal_engine.py` - Engine Principale OANDA**
- **Responsabilità**: Generazione segnali base con OANDA v20 API
- **Algoritmi implementati**:
  - Analisi tecnica multi-timeframe (RSI, MACD, Bollinger Bands, EMA/SMA)
  - Calcolo ATR per gestione volatilità
  - Rilevamento sessioni di mercato (Tokyo, London, New York, Sydney)
  - Risk management basato su ATR con ratio 1:2.5
- **Timeframes**: H1, H4, D1
- **Strumenti supportati**: 25 asset (forex, metalli, indici)

#### **2. `advanced_signal_analyzer.py` - Analizzatore Avanzato**
- **Responsabilità**: Analisi tecnica avanzata e algoritmi sofisticati
- **Algoritmi implementati**:
  - **Multi-Timeframe Analysis**: M1, M5, M15, M30 con confluenza
  - **Market Structure Analysis**: Trend detection tramite MA alignment
  - **Smart Money Detection**: Pattern accumulation/distribution
  - **Volume Profile Analysis**: POC, Value Area, Order Flow
  - **Key Levels Detection**: Support/Resistance dinamici
  - **Swing Points Analysis**: Highs/Lows per livelli precisi

#### **3. `quantistes_integration.py` - Integrazione Quantistes**
- **Responsabilità**: Predizioni avanzate per indici tramite ML
- **Algoritmi implementati**:
  - Machine Learning predictions per US30, NAS100, SPX500
  - Confidence scoring basato su modelli quantitativi
  - Integrazione con analisi tecnica tradizionale

#### **4. `main.py` - Orchestrazione e API**
- **Responsabilità**: Coordinamento tra engines e esposizione API
- **Funzioni chiave**:
  - Unified symbol mapping (OANDA ↔ Frontend)
  - Routing tra different engines
  - Database persistence
  - REST API endpoints

---

## 🧠 Strategia di Analisi Tecnica

### **Livello 1: Analisi Multi-Timeframe**

```python
# Timeframes analizzati con pesi diversi
timeframes = {
    TimeFrame.M1: peso=1,    # Micro trends - precisione entry
    TimeFrame.M5: peso=2,    # Conferma trend intraday  
    TimeFrame.M15: peso=3,   # Trend primario intraday
    TimeFrame.M30: peso=4    # Contesto e direzione mercato
}
```

**Indicatori per ogni timeframe**:
- **RSI (14)**: Momentum e ipercomprato/ipervenduto
- **MACD (12,26,9)**: Trend e momentum convergence
- **Bollinger Bands (20,2)**: Volatilità e mean reversion
- **EMA (9,21,50) + SMA (200)**: Trend alignment
- **ATR (14)**: Volatilità per risk management

### **Livello 2: Market Structure Analysis**

#### **Trend Detection Algorithm**:
```python
if current_price > sma_20 > sma_50:
    trend = BULLISH
elif current_price < sma_20 < sma_50:
    trend = BEARISH
else:
    trend = SIDEWAYS
```

#### **Confluence Score Calculation**:
```python
confluence_score = (agreement_count / total_timeframes) * 100
# Minimo 60% per segnali BUY/SELL, altrimenti HOLD
```

### **Livello 3: Smart Money Analysis**

**Pattern Detection**:
- **Accumulation**: Higher TF bullish + Lower TF bearish
- **Distribution**: Higher TF bearish + Lower TF bullish
- **Manipulation**: Quick spikes seguiti da reversal

---

## 🎯 Sistema di Calcolo SL/TP Professionale

### **Approccio ATR-Based con Market Structure**

#### **Step 1: Calcolo ATR Dinamico**
```python
# Multiplier basati sulla volatilità di mercato
if atr_percentage > 1.5%:    # Alta volatilità
    sl_multiplier = 1.5
    tp_multiplier = 3.0
elif atr_percentage > 0.8%:  # Media volatilità
    sl_multiplier = 2.0
    tp_multiplier = 4.0
else:                        # Bassa volatilità
    sl_multiplier = 2.5
    tp_multiplier = 5.0
```

#### **Step 2: Livelli Tecnici di Supporto/Resistenza**

**Per segnali BUY**:
1. **Stop Loss**: Nearest Support Level below price
   - Validazione: distanza 1.0-4.0 ATR dal prezzo
   - Fallback: current_price - (ATR × sl_multiplier)

2. **Take Profit**: Strongest Resistance Level above price
   - Validazione: distanza 2.0-8.0 ATR dal prezzo
   - Priorità per levels con strength maggiore

**Per segnali SELL**:
1. **Stop Loss**: Nearest Resistance Level above price
2. **Take Profit**: Strongest Support Level below price

#### **Step 3: Swing Points Integration**

```python
# Raccolta swing points da tutti i timeframes
for tf_data in timeframes:
    swing_highs = tf_data["swing_highs"]
    swing_lows = tf_data["swing_lows"]

# Selezione ottimale basata su:
# - Distanza dal prezzo corrente
# - Forza del livello (numero di test)
# - Allineamento con ATR
```

---

## 🤖 Integrazione Intelligenza Artificiale

### **Google Gemini AI Analysis**

**Prompt Structure**:
```python
prompt = f"""
Analizza questa situazione di trading per {instrument}:

DATI TECNICI:
- RSI: {rsi} ({rsi_signal})
- MACD: {macd_trend}
- Bollinger: prezzo {bb_position} le bande
- Trend MA: {ma_trend}

CONTESTO MERCATO:
- Sessione: {market_session} (overlap: {session_overlap})
- Volatilità attesa: {volatility_expected}

SEGNALE GENERATO: {signal_type}

Fornisci analisi professionale in italiano...
"""
```

**Output AI**:
- Spiegazione del segnale generato
- Fattori di supporto tecnici
- Analisi dei rischi
- Raccomandazione finale

---

## 📊 Gestione del Rischio

### **Position Sizing Algorithm**

```python
# Rischio fisso del 2% per trade
max_risk_per_trade = 0.02
position_size = risk_amount / (stop_loss_distance * pip_value)
```

### **Risk/Reward Optimization**

- **Target R/R**: 1:2.5 (default)
- **Minimum acceptable**: 1:1.0
- **Adjustment basato su**:
  - Market volatility (ATR)
  - Key levels strength
  - Session overlap factor

---

## 🔄 Flusso di Generazione Segnale

### **1. Initialization Phase**
```python
# main.py
async def generate_custom_signal(symbol: str):
    analyzer = AdvancedSignalAnalyzer(oanda_api_key, gemini_api_key)
    oanda_symbol = get_oanda_symbol(symbol)  # Unified mapping
```

### **2. Data Collection Phase**
```python
# advanced_signal_analyzer.py
for timeframe in [M1, M5, M15, M30]:
    df = await get_oanda_candles(symbol, timeframe, count=200)
    analysis = analyze_timeframe_structure(df, timeframe)
```

### **3. Technical Analysis Phase**
```python
# Multi-timeframe confluence
mtf_analysis = analyze_multi_timeframe(symbol)
overall_trend = calculate_trend_confluence(timeframes_data)
confluence_score = calculate_confluence_score(timeframes_data)
```

### **4. Level Calculation Phase**
```python
# ATR-based initial levels
atr = get_atr_from_M30_timeframe()
initial_sl = current_price ± (atr * multiplier)
initial_tp = current_price ± (atr * multiplier * 2)

# Refinement con key levels
refined_sl = find_best_support_resistance(key_levels, swing_points)
refined_tp = find_best_target_level(key_levels, swing_points)
```

### **5. AI Enhancement Phase**
```python
# Gemini AI analysis
ai_analysis = await generate_ai_analysis(
    instrument, technical_data, market_context, signal_type
)
```

### **6. Signal Assembly Phase**
```python
signal = TradingSignal(
    instrument=instrument,
    signal_type=signal_type,
    entry_price=current_price,
    stop_loss=calculated_sl,
    take_profit=calculated_tp,
    confidence_score=confluence_score,
    ai_analysis=ai_analysis,
    risk_reward_ratio=calculated_rr,
    technical_analysis=technical_data,
    market_context=market_data
)
```

### **7. Database Persistence Phase**
```python
# main.py
frontend_symbol = get_frontend_symbol(oanda_symbol)  # Unified mapping
db_signal = Signal(
    symbol=frontend_symbol,
    entry_price=signal.entry_price,
    stop_loss=signal.stop_loss,
    take_profit=signal.take_profit,
    # ... other fields
)
db.add(db_signal)
```

---

## 🛠️ Configurazione e Parametri

### **Environment Variables Required**
```bash
OANDA_API_KEY=your_oanda_key
OANDA_ACCOUNT_ID=your_account_id
OANDA_ENVIRONMENT=practice|live
GEMINI_API_KEY=your_gemini_key
```

### **Key Parameters**
```python
# Risk Management
max_risk_per_trade = 0.02        # 2%
default_rrr = 2.5               # 1:2.5
confidence_threshold = 0.60      # 60% minimum

# Technical Analysis
rsi_period = 14
macd_fast = 12, slow = 26, signal = 9
bb_period = 20, std_dev = 2
atr_period = 14

# Level Calculation
min_sl_distance_atr = 1.0       # Minimum 1 ATR
max_sl_distance_atr = 4.0       # Maximum 4 ATR
min_tp_distance_atr = 2.0       # Minimum 2 ATR
max_tp_distance_atr = 8.0       # Maximum 8 ATR
```

---

## 📈 Performance e Metriche

### **Signal Quality Metrics**
- **Confluence Score**: 0-100% (agreement tra timeframes)
- **Technical Score**: 0-100% (overall technical strength)
- **AI Confidence**: 55-95% (Gemini analysis confidence)
- **Risk/Reward Ratio**: Calculated based on actual levels

### **Supported Instruments (25 total)**

**Forex Major (7)**:
- EUR_USD, GBP_USD, USD_JPY, AUD_USD, USD_CAD, NZD_USD, EUR_GBP

**Forex Cross (12)**:
- EUR_AUD, EUR_CHF, GBP_JPY, AUD_JPY, EUR_JPY, GBP_AUD, USD_CHF, CHF_JPY, AUD_CAD, CAD_JPY, EUR_CAD, GBP_CAD

**Precious Metals (2)**:
- XAU_USD (Gold), XAG_USD (Silver)

**Major Indices (4)**:
- US30_USD (Dow Jones), NAS100_USD (NASDAQ), SPX500_USD (S&P 500), DE30_EUR (DAX)

---

## 🔧 Troubleshooting e Maintenance

### **Common Issues**

1. **Price Data Issues**: Risolto con fallback intelligente tra timeframes
2. **Symbol Mapping**: Unified mapping system tra OANDA e frontend
3. **Level Calculation**: ATR-based fallback se key levels non disponibili
4. **API Rate Limits**: Built-in delays e error handling

### **Monitoring**

```python
# Logging dettagliato per ogni fase
logger.info(f"Level analysis: ATR={atr_pct:.3f}%, Risk={risk_pct:.2f}%, R/R={rr:.2f}")
logger.warning(f"Using fallback levels due to insufficient key level data")
```

---

## 📝 Versioning e Updates

- **v1.0**: Basic OANDA integration
- **v2.0**: Advanced multi-timeframe analysis
- **v3.0**: Smart money detection
- **v4.0**: Professional level calculation (current)

**Prossimi sviluppi**:
- Machine Learning integration estesa
- Sentiment analysis
- News impact evaluation
- Portfolio correlation analysis

---

*Documentazione generata automaticamente - Sistema di Trading AI v4.0*