# Custom Dockerfile for Railway - FXCM Trading App
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy all files first
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r frontend/requirements.txt

# Expose port (Railway provides $PORT)
EXPOSE 8000

# Railway needs to import the app from main:app
# Our main.py in root imports from frontend.main
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]