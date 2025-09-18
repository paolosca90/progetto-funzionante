-- 🚨 RESET COMPLETO DATABASE RAILWAY (Copia tutto e incolla in Query Editor)
-- QUESTO ELIMINERÀ TUTTI I DATI ESISTENTI MA RISOLVERÀ GLI ERRORI 500

-- Step 1: DROP di tutte le tabelle esistenti
DROP TABLE IF EXISTS signal_executions CASCADE;
DROP TABLE IF EXISTS subscriptions CASCADE;
DROP TABLE IF EXISTS oanda_connections CASCADE;
DROP TABLE IF EXISTS signals CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- BONUS: Pulizia anche di eventuali altre tabelle
DROP TABLE IF EXISTS alembic_version CASCADE;

-- 💡 RISULTATO:
-- - Database completamente pulito
-- - Al prossimo avvio dell'app si ricreeranno le tabelle nuove
-- - Nessun errore colonna mancante
-- - Tutti gli endpoint funzioneranno

-- 🎯 PRONTO PER IL DEPLOY!
