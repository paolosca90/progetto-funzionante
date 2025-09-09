#!/bin/bash

# Railway Startup Script for Trading Signals API
echo "🚀 Starting Trading Signals API on Railway..."

# Set defaults for required environment variables
export PORT="${PORT:-8000}"
export DATABASE_URL="${DATABASE_URL:-}"
export SECRET_KEY="${SECRET_KEY:-development-secret-key-change-in-production}"
export MT5_SECRET_KEY="${MT5_SECRET_KEY:-}"
export VPS_API_KEY="${VPS_API_KEY:-default-vps-key}"
export BRIDGE_API_KEY="${BRIDGE_API_KEY:-default-bridge-key}"
export RESEND_API_KEY="${RESEND_API_KEY:-}"

# Validate PORT is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "❌ Error: PORT '$PORT' is not a valid number, using default 8000"
    PORT=8000
fi

echo "📊 Configuration:"
echo "   PORT: $PORT"
echo "   DATABASE_URL Set: $([ -n "$DATABASE_URL" ] && echo '✅' || echo '❌')"
echo "   SECRET_KEY Set: $([ -n "$SECRET_KEY" ] && echo '✅' || echo '❌')"
echo "   MT5_SECRET_KEY Set: $([ -n "$MT5_SECRET_KEY" ] && echo '✅' || echo '❌')"

# Start the application
echo "🔄 Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT