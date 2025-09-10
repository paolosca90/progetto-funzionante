#!/bin/bash

# Railway Startup Script for Trading Signals API
echo "🚀 Starting Trading Signals API on Railway..."

# Set defaults for required environment variables
export PORT="${PORT:-8000}"
export DATABASE_URL="${DATABASE_URL:-}"
export SECRET_KEY="${SECRET_KEY:-development-secret-key-change-in-production}"
export OANDA_API_KEY="${OANDA_API_KEY:-}"
export OANDA_ACCOUNT_ID="${OANDA_ACCOUNT_ID:-}"
export OANDA_ENVIRONMENT="${OANDA_ENVIRONMENT:-demo}"
export GEMINI_API_KEY="${GEMINI_API_KEY:-}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-${SECRET_KEY}}"
export EMAIL_HOST="${EMAIL_HOST:-}"
export EMAIL_USER="${EMAIL_USER:-}"
export EMAIL_PASSWORD="${EMAIL_PASSWORD:-}"

# Validate PORT is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "❌ Error: PORT '$PORT' is not a valid number, using default 8000"
    PORT=8000
fi

echo "📊 Configuration:"
echo "   PORT: $PORT"
echo "   DATABASE_URL Set: $([ -n "$DATABASE_URL" ] && echo '✅' || echo '❌')"
echo "   SECRET_KEY Set: $([ -n "$SECRET_KEY" ] && echo '✅' || echo '❌')"
echo "   OANDA_API_KEY Set: $([ -n "$OANDA_API_KEY" ] && echo '✅' || echo '❌')"
echo "   OANDA_ACCOUNT_ID Set: $([ -n "$OANDA_ACCOUNT_ID" ] && echo '✅' || echo '❌')"
echo "   GEMINI_API_KEY Set: $([ -n "$GEMINI_API_KEY" ] && echo '✅' || echo '❌')"
echo "   JWT_SECRET_KEY Set: $([ -n "$JWT_SECRET_KEY" ] && echo '✅' || echo '❌')"

# Start the application
echo "🔄 Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT