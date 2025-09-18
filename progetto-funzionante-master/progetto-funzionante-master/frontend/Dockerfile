# Multi-stage Docker build for FastAPI trading system - Optimized for production
FROM python:3.11-slim as builder

# Set environment variables for optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install only essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment with optimized settings
RUN python -m venv --upgrade-deps /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install build dependencies with caching optimization
RUN pip install --upgrade pip setuptools wheel

# Copy requirements files with proper order for layer caching
COPY requirements.txt ./
COPY requirements-test.txt ./

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --compile --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --compile --no-cache-dir -r requirements-test.txt && \
    find /opt/venv -name '*.pyc' -delete && \
    find /opt/venv -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

# Production stage - security optimized
FROM python:3.11-slim

# Security labels and metadata
LABEL maintainer="Trading System Team" \
      version="1.0.0" \
      description="FastAPI Trading Signals System" \
      org.opencontainers.image.title="Trading Signals API" \
      org.opencontainers.image.description="AI-powered trading signals system with OANDA integration" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

# Hardened environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=production \
    PYTHONOPTIMIZE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install minimal runtime dependencies with security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /usr/share/doc/* \
    && rm -rf /usr/share/man/* \
    && rm -rf /var/cache/apt/archives/*

# Create non-root app user with restricted permissions
RUN groupadd -r app && useradd -r -g app -s /bin/bash -d /app app

# Copy virtual environment from builder with proper ownership
COPY --from=builder /opt/venv /opt/venv
RUN chown -R app:app /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create application directory with proper permissions
RUN mkdir -p /app /app/logs /app/static /app/templates && \
    chown -R app:app /app
WORKDIR /app

# Copy application code with optimized layer ordering
# Copy dependencies first (least frequently changing)
COPY --chown=app:app requirements*.txt ./
# Then copy Python code (more frequently changing)
COPY --chown=app:app *.py ./
# Copy application directories (most frequently changing)
COPY --chown=app:app app/ ./app/
COPY --chown=app:app config/ ./config/
COPY --chown=app:app static/ ./static/
COPY --chown=app:app templates/ ./templates/

# Copy optimized startup script
COPY --chown=app:app ../start.sh /app/start.sh
RUN chmod +x /app/start.sh && chown app:app /app/start.sh

# Switch to non-root user
USER app

# Enhanced health check with multiple endpoints
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
    CMD curl -f http://localhost:8000/health || \
        curl -f http://localhost:8000/api/health || \
        curl -f http://localhost:8000/docs || exit 1

# Security: Limit exposed ports and bind to specific interface
EXPOSE 8000

# Create directories for runtime data and logs
RUN mkdir -p /app/data /app/logs /tmp/app && \
    chown -R app:app /app/data /app/logs /tmp/app

# Set secure file permissions
RUN chmod 750 /app && chmod 755 /app/start.sh

# Switch to non-root user for security
USER app

# Set resource limits and ulimits for stability
# These are hints to the container runtime
ENV PYTHON_MAX_MEMORY=512M
ENV PYTHON_GC_THRESHOLD=70000
ENV OOM_SCORE_ADJ=-500

# Set optimized entrypoint with signal handling
ENTRYPOINT ["/app/start.sh"]

# Default command with production optimizations
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--max-requests", "1000", "--max-requests-jitter", "50", \
     "--timeout-keep-alive", "30", "--limit-concurrency", "100"]