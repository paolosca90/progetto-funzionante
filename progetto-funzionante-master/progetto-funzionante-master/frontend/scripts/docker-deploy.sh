#!/bin/bash

# Docker Deployment Script for Trading System
# This script handles deployment to different environments

set -euo pipefail

# Configuration
PROJECT_NAME="trading-system"
ENVIRONMENT=${ENVIRONMENT:-"development"}
DOCKER_USER=${DOCKER_USER:-""}
IMAGE_NAME="trading-system-api"
VERSION=${VERSION:-"latest"}
COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
    tee -a "$LOG_DIR/deploy.log"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
    tee -a "$LOG_DIR/deploy.log"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    tee -a "$LOG_DIR/deploy.log"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --backup)
            BACKUP=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --env ENV          Deployment environment (development, staging, production)"
            echo "  --version VERSION  Image version to deploy"
            echo "  --backup           Create backup before deployment"
            echo "  --rollback         Rollback to previous version"
            echo "  --force           Force deployment without confirmation"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set compose file based on environment
case "$ENVIRONMENT" in
    "production")
        COMPOSE_FILE="docker-compose.prod.yml"
        ;;
    "staging")
        COMPOSE_FILE="docker-compose.staging.yml"
        ;;
    "development")
        COMPOSE_FILE="docker-compose.yml"
        ;;
    *)
        error "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Create necessary directories
mkdir -p "$BACKUP_DIR" "$LOG_DIR"

# Load environment variables
if [[ -f ".env.$ENVIRONMENT" ]]; then
    log "Loading environment variables from .env.$ENVIRONMENT"
    set -a
    source ".env.$ENVIRONMENT"
    set +a
else
    warn "No environment file found: .env.$ENVIRONMENT"
fi

# Function to backup current deployment
backup_deployment() {
    log "Creating backup of current deployment..."

    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"

    mkdir -p "$BACKUP_PATH"

    # Backup docker-compose file
    cp "$COMPOSE_FILE" "$BACKUP_PATH/"

    # Backup database if it's a local volume
    if docker volume ls | grep -q "${PROJECT_NAME}_postgres_data"; then
        log "Backing up database volume..."
        docker run --rm \
            -v "${PROJECT_NAME}_postgres_data:/data" \
            -v "$BACKUP_PATH:/backup" \
            postgres:15-alpine \
            tar czf /backup/postgres_backup.tar.gz -C /data .
    fi

    # Backup Redis data
    if docker volume ls | grep -q "${PROJECT_NAME}_redis_data"; then
        log "Backing up Redis volume..."
        docker run --rm \
            -v "${PROJECT_NAME}_redis_data:/data" \
            -v "$BACKUP_PATH:/backup" \
            redis:7-alpine \
            tar czf /backup/redis_backup.tar.gz -C /data .
    fi

    # Save current container status
    docker-compose -f "$COMPOSE_FILE" ps > "$BACKUP_PATH/container_status.txt"

    log "Backup created at: $BACKUP_PATH"
}

# Function to rollback deployment
rollback_deployment() {
    log "Starting rollback process..."

    # Find the latest backup
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR" | grep "backup_" | head -n 1)

    if [[ -z "$LATEST_BACKUP" ]]; then
        error "No backup found for rollback"
        exit 1
    fi

    BACKUP_PATH="$BACKUP_DIR/$LATEST_BACKUP"
    log "Rolling back to backup: $LATEST_BACKUP"

    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down

    # Restore database backup
    if [[ -f "$BACKUP_PATH/postgres_backup.tar.gz" ]]; then
        log "Restoring database backup..."
        docker run --rm \
            -v "${PROJECT_NAME}_postgres_data:/data" \
            -v "$BACKUP_PATH:/backup" \
            alpine:latest \
            tar xzf /backup/postgres_backup.tar.gz -C /data
    fi

    # Restore Redis backup
    if [[ -f "$BACKUP_PATH/redis_backup.tar.gz" ]]; then
        log "Restoring Redis backup..."
        docker run --rm \
            -v "${PROJECT_NAME}_redis_data:/data" \
            -v "$BACKUP_PATH:/backup" \
            alpine:latest \
            tar xzf /backup/redis_backup.tar.gz -C /data
    fi

    # Restart services
    docker-compose -f "$COMPOSE_FILE" up -d

    log "Rollback completed successfully!"
}

# Function to deploy new version
deploy_version() {
    log "Starting deployment of version $VERSION to $ENVIRONMENT..."

    # Pull the latest image
    FULL_IMAGE_NAME="$IMAGE_NAME"
    if [[ -n "$DOCKER_USER" ]]; then
        FULL_IMAGE_NAME="$DOCKER_USER/$IMAGE_NAME"
    fi
    FULL_IMAGE_NAME="$FULL_IMAGE_NAME:$VERSION"

    log "Pulling image: $FULL_IMAGE_NAME"
    docker pull "$FULL_IMAGE_NAME"

    # Update docker-compose file with new image version
    if [[ -f "$COMPOSE_FILE" ]]; then
        log "Updating docker-compose file with new image version..."
        sed -i.bak "s|image: $IMAGE_NAME:.*|image: $FULL_IMAGE_NAME|g" "$COMPOSE_FILE"
    fi

    # Stop services gracefully
    log "Stopping current services..."
    docker-compose -f "$COMPOSE_FILE" down

    # Start services with new version
    log "Starting services with new version..."
    docker-compose -f "$COMPOSE_FILE" up -d

    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30

    # Check service health
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up (healthy)"; then
        log "Services are healthy!"
    else
        warn "Some services may not be healthy. Checking status..."
        docker-compose -f "$COMPOSE_FILE" ps
    fi

    log "Deployment completed successfully!"
}

# Function to monitor deployment
monitor_deployment() {
    log "Monitoring deployment..."

    # Monitor for 5 minutes
    for i in {1..30}; do
        log "Check $i/30 - Service status:"
        docker-compose -f "$COMPOSE_FILE" ps

        # Check if all services are healthy
        HEALTHY_COUNT=$(docker-compose -f "$COMPOSE_FILE" ps | grep -c "Up (health" || echo "0")
        TOTAL_COUNT=$(docker-compose -f "$COMPOSE_FILE" ps | grep -c "Up" || echo "0")

        if [[ "$HEALTHY_COUNT" == "$TOTAL_COUNT" ]] && [[ "$TOTAL_COUNT" -gt 0 ]]; then
            log "All services are healthy!"
            return 0
        fi

        sleep 10
    done

    warn "Some services are not healthy after 5 minutes"
    return 1
}

# Main deployment logic
log "Starting deployment to $ENVIRONMENT environment"
log "Version: $VERSION"
log "Compose file: $COMPOSE_FILE"

# Confirmation prompt
if [[ "$FORCE" != true ]]; then
    echo -n "${YELLOW}Are you sure you want to deploy to $ENVIRONMENT? (y/N): ${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log "Deployment cancelled"
        exit 0
    fi
fi

# Create backup if requested
if [[ "$BACKUP" == true ]]; then
    backup_deployment
fi

# Handle rollback
if [[ "$ROLLBACK" == true ]]; then
    rollback_deployment
    exit 0
fi

# Deploy new version
deploy_version

# Monitor deployment
if monitor_deployment; then
    log "Deployment monitoring completed successfully!"

    # Log deployment details
    cat >> "$LOG_DIR/deployment_history.log" << EOF
$(date): Deployed version $VERSION to $ENVIRONMENT
Image: $FULL_IMAGE_NAME
Status: Success
EOF
else
    error "Deployment monitoring failed"
    cat >> "$LOG_DIR/deployment_history.log" << EOF
$(date): Deployed version $VERSION to $ENVIRONMENT
Image: $FULL_IMAGE_NAME
Status: Failed
EOF
    exit 1
fi

log "Deployment process completed!"
exit 0