# 🚀 Guida al Deployment su Railway - AI Cash Revolution

## Prerequisiti
- Account GitHub
- Account Railway (https://railway.app)
- Repository Git del progetto

## 📋 Checklist Pre-Deployment

### ✅ Completato
- [x] Schema database Prisma creato
- [x] Docker configuration (Dockerfile, .dockerignore, railway.json)
- [x] Package.json con dipendenze
- [x] Entry point applicazione (src/index.js)
- [x] Sistema di logging
- [x] Integrazioni API reali (OANDA, Gemini)
- [x] Expert Advisor MT5
- [x] Configurazione ambiente produzione

### 🔧 Da Configurare su Railway

## 🚀 Step-by-Step Deployment

### 1. Setup Repository
```bash
cd "C:\Users\USER\Desktop\new project\aicash-revolution\server"
git init
git add .
git commit -m "Initial commit: AI Cash Revolution Trading System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/aicash-revolution.git
git push -u origin main
```

### 2. Deployment su Railway

1. **Vai su https://railway.app**
2. **Login con GitHub**
3. **New Project → Deploy from GitHub repo**
4. **Seleziona il repository aicash-revolution**

### 3. Configurazione Database

1. **Add Service → Database → PostgreSQL**
2. **Copia la CONNECTION_STRING fornita da Railway**
3. **Format**: `postgresql://username:password@host:port/database`

### 4. Configurazione Environment Variables

Nel dashboard Railway, vai su **Variables** e aggiungi:

```bash
# Database
DATABASE_URL=<copia da Railway PostgreSQL>

# App Settings
NODE_ENV=production
PORT=3000

# OANDA (già configurato)
OANDA_API_KEY=9b4d0a5b4275f2403fc93f087ceac88d-00a9307bfd9f8932874a36cb6f0c3286
OANDA_ACCOUNT_ID=101-004-37029911-001
OANDA_ENVIRONMENT=practice
OANDA_API_URL=https://api-fxpractice.oanda.com

# Gemini AI (già configurato)
GEMINI_API_KEY=AIzaSyAM0JZCXlxkhN_3shsVIEOfBOcKnqSWG38

# JWT (genera questi!)
JWT_SECRET=genera-una-chiave-sicura-di-32-caratteri
JWT_REFRESH_SECRET=genera-altra-chiave-sicura-di-32-caratteri

# MT5 Bridge
MT5_BRIDGE_PORT=9999
MT5_BRIDGE_HOST=0.0.0.0

# Sicurezza
BCRYPT_ROUNDS=12
TRUST_PROXY=true
```

### 5. Deploy Commands

Railway eseguirà automaticamente:
```bash
npm install          # Installa dipendenze
npx prisma generate  # Genera client Prisma
npm start           # Avvia applicazione
```

### 6. Database Migration

Dopo il primo deploy:
1. **Vai su Railway Dashboard**
2. **Seleziona il servizio del backend**
3. **Vai su Deploy Logs**
4. **Una volta che l'app è online, esegui:**

```bash
# Nel Railway console o localmente con DATABASE_URL
npx prisma db push
npx prisma db seed
```

## 🔧 Configurazioni Post-Deploy

### 1. Custom Domain (Opzionale)
- Railway Dashboard → Settings → Domains
- Aggiungi dominio personalizzato
- Configura DNS record

### 2. SSL Certificate
- Railway fornisce SSL automaticamente
- Verifica che HTTPS sia attivo

### 3. Monitoring
- Dashboard Railway per logs e metriche
- Setup Sentry (opzionale)

## 📱 Setup App Mobile

### 1. Aggiorna endpoint API nell'app mobile:
```javascript
// web/mobile/src/services/config.js
const API_BASE_URL = 'https://your-app-name.railway.app/api';
```

### 2. Deploy app mobile:
- **React Native**: Expo Build
- **iOS**: App Store Connect
- **Android**: Google Play Console

## 🔌 Setup MT5 Expert Advisor

### 1. Installa EA in MetaTrader 5:
```
1. Copia AICashRevolution_EA.mq5 in /MQL5/Experts/
2. Compila l'EA in MetaEditor
3. Applica al grafico con parametri:
   - ServerURL: wss://your-app.railway.app
   - UserID: tuo_user_id
   - APIKey: genera_in_app
```

### 2. Configura WebSocket nel backend:
```javascript
// Aggiorna src/index.js se necessario
const io = new Server(server, {
  cors: {
    origin: "*", // In produzione, specifica domini esatti
    methods: ["GET", "POST"]
  }
});
```

## 📊 Test di Funzionamento

### 1. Health Check
```bash
curl https://your-app.railway.app/api/health
```

### 2. Authentication Test
```bash
curl -X POST https://your-app.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

### 3. OANDA Integration Test
```bash
curl https://your-app.railway.app/api/instruments
```

## ⚡ Performance Optimization

### 1. Railway Scaling
- Railway scale automaticamente
- Monitor uso CPU/RAM nel dashboard

### 2. Database Optimization
```sql
-- Aggiungi indici per performance
CREATE INDEX CONCURRENTLY idx_signals_user_status ON trading_signals(user_id, status);
CREATE INDEX CONCURRENTLY idx_signals_expires ON trading_signals(expires_at);
```

### 3. Caching
- Redis add-on su Railway (opzionale)
- Cache response API frequenti

## 🚨 Troubleshooting

### Build Errors
```bash
# Se il build fallisce, controlla:
1. package.json dependencies corrette
2. Prisma schema valido
3. Environment variables impostate
```

### Database Connection Issues
```bash
# Verifica DATABASE_URL nel Railway dashboard
# Format corretto: postgresql://user:pass@host:port/db
```

### API Integration Issues
```bash
# Test OANDA connection:
curl -H "Authorization: Bearer YOUR_OANDA_KEY" \
  https://api-fxpractice.oanda.com/v3/accounts/YOUR_ACCOUNT_ID
```

## 📈 Monitoraggio Produzione

### 1. Logs
- Railway Dashboard → Deploy Logs
- Application Logs in real-time

### 2. Metrics
- CPU Usage
- Memory Usage
- Response Times
- Error Rates

### 3. Alerts
- Setup notification webhooks
- Monitor critical errors

## 🔐 Sicurezza Produzione

### 1. Environment Variables
- Mai esporre API keys
- Usa secrets management Railway

### 2. Rate Limiting
- Configurato automaticamente
- Monitor per abuse

### 3. CORS
- Configura domini specifici
- Non usare wildcard "*" in produzione

## 💰 Costi Stimati

### Railway Hobby Plan ($5/mese):
- 512MB RAM
- 1GB Storage
- PostgreSQL incluso
- SSL certificato incluso

### Railway Pro Plan ($20/mese):
- 8GB RAM
- Unlimited services
- Priority support

## 🎯 Next Steps

1. **Deploy su Railway** ✅
2. **Test integrazioni API** ✅
3. **Setup MT5 EA** ✅
4. **Deploy app mobile**
5. **User testing**
6. **Performance monitoring**
7. **Scale based on usage**

---

## 🆘 Support

Se hai problemi durante il deploy:
1. Controlla Railway deploy logs
2. Verifica environment variables
3. Test API connections singolarmente
4. Controlla database connectivity

**Il sistema è ora pronto per il deployment produzione!** 🚀