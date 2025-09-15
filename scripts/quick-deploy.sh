#!/bin/bash
# AI Cash Revolution - Quick Deployment Script
# Fast deployment for immediate testing and demonstration

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-local}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_banner() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}║           AI CASH REVOLUTION                              ║${NC}"
    echo -e "${GREEN}║           Quick Deployment Script                         ║${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}║   Production-Ready Trading System Deployment             ║${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi

    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Set Docker Compose command
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        DOCKER_COMPOSE_CMD="docker compose"
    fi

    # Check if we're in the correct directory
    if [ ! -f "$PROJECT_ROOT/docker-compose.production.yml" ]; then
        log_error "Production Docker Compose file not found. Are you in the correct directory?"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

setup_environment() {
    log_info "Setting up environment configuration..."

    # Create .env file from template if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        if [ -f "$PROJECT_ROOT/environments/.env.staging" ]; then
            log_info "Creating .env from staging template..."
            cp "$PROJECT_ROOT/environments/.env.staging" "$PROJECT_ROOT/.env"
        else
            log_warning "No environment template found. You'll need to configure environment variables manually."
            return
        fi
    fi

    # Update environment for quick deployment
    cat >> "$PROJECT_ROOT/.env" << EOF

# Quick Deployment Overrides
NODE_ENV=staging
LOG_LEVEL=debug
CORS_ORIGIN=http://localhost:3000,http://localhost:8080
ENABLE_API_DOCS=true
ENABLE_TEST_DATA=true

# Demo API Keys (replace with real ones for production)
OANDA_API_KEY=demo_key_change_me
GEMINI_API_KEY=demo_gemini_key_change_me
GOOGLE_CLIENT_ID=demo_google_client_id
JWT_SECRET=quick_deploy_jwt_secret_change_for_production
SESSION_SECRET=quick_deploy_session_secret_change_for_production

EOF

    log_success "Environment configuration completed"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure with Docker Compose..."

    cd "$PROJECT_ROOT"

    # Pull latest images
    log_info "Pulling latest Docker images..."
    $DOCKER_COMPOSE_CMD -f docker-compose.production.yml pull --ignore-pull-failures

    # Build and start services
    log_info "Building and starting services..."
    $DOCKER_COMPOSE_CMD -f docker-compose.production.yml up -d --build

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30

    # Check service health
    check_service_health
}

check_service_health() {
    log_info "Checking service health..."

    local services=("postgres" "redis" "api")
    local healthy_services=0

    for service in "${services[@]}"; do
        if $DOCKER_COMPOSE_CMD -f docker-compose.production.yml ps "$service" | grep -q "Up (healthy)"; then
            log_success "$service is healthy"
            ((healthy_services++))
        else
            log_warning "$service may not be fully ready yet"
        fi
    done

    if [ $healthy_services -eq ${#services[@]} ]; then
        log_success "All core services are healthy!"
    else
        log_warning "Some services may still be starting up. Check logs if issues persist."
    fi
}

setup_database() {
    log_info "Setting up database..."

    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    sleep 10

    # Run database migrations
    log_info "Running database migrations..."
    $DOCKER_COMPOSE_CMD -f docker-compose.production.yml exec -T api npx prisma migrate deploy || {
        log_warning "Database migrations may have failed. Checking if database needs initialization..."

        # Try to generate Prisma client and push schema
        $DOCKER_COMPOSE_CMD -f docker-compose.production.yml exec -T api npx prisma generate
        $DOCKER_COMPOSE_CMD -f docker-compose.production.yml exec -T api npx prisma db push --force-reset
    }

    # Seed database if needed
    log_info "Seeding database with test data..."
    $DOCKER_COMPOSE_CMD -f docker-compose.production.yml exec -T api npx prisma db seed || {
        log_warning "Database seeding skipped (seed script may not exist)"
    }

    log_success "Database setup completed"
}

verify_deployment() {
    log_info "Verifying deployment..."

    # Check API health endpoint
    local api_url="http://localhost:3000/api/health"
    local max_attempts=10
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$api_url" > /dev/null; then
            log_success "API health check passed"
            break
        else
            log_info "Attempt $attempt/$max_attempts: Waiting for API to be ready..."
            sleep 5
            ((attempt++))
        fi
    done

    if [ $attempt -gt $max_attempts ]; then
        log_error "API health check failed after $max_attempts attempts"
        show_logs_info
        return 1
    fi

    # Test API endpoints
    log_info "Testing API endpoints..."

    # Test authentication status
    if curl -f -s "http://localhost:3000/api/auth/status" > /dev/null; then
        log_success "Authentication endpoint is working"
    else
        log_warning "Authentication endpoint may not be ready"
    fi

    # Test instruments endpoint
    if curl -f -s "http://localhost:3000/api/instruments" > /dev/null; then
        log_success "Instruments endpoint is working"
    else
        log_warning "Instruments endpoint may not be ready"
    fi

    log_success "Deployment verification completed"
}

show_deployment_info() {
    log_info "Deployment completed successfully!"
    echo ""
    echo -e "${GREEN}🚀 AI Cash Revolution is now running!${NC}"
    echo ""
    echo -e "${BLUE}Available Services:${NC}"
    echo "• API Server:      http://localhost:3000"
    echo "• API Health:      http://localhost:3000/api/health"
    echo "• API Docs:        http://localhost:3000/api/docs (if enabled)"
    echo "• Grafana:         http://localhost:3001 (admin/admin)"
    echo "• Prometheus:      http://localhost:9090"
    echo ""
    echo -e "${BLUE}Management Commands:${NC}"
    echo "• View logs:       cd '$PROJECT_ROOT' && $DOCKER_COMPOSE_CMD -f docker-compose.production.yml logs -f"
    echo "• Stop services:   cd '$PROJECT_ROOT' && $DOCKER_COMPOSE_CMD -f docker-compose.production.yml down"
    echo "• Restart API:     cd '$PROJECT_ROOT' && $DOCKER_COMPOSE_CMD -f docker-compose.production.yml restart api"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Configure real API keys in .env file"
    echo "2. Test mobile app connection to http://localhost:3000"
    echo "3. Set up SSL certificates for production domain"
    echo "4. Configure monitoring alerts"
    echo ""
    echo -e "${GREEN}Happy Trading! 🎯📈${NC}"
    echo ""
}

show_logs_info() {
    echo ""
    log_info "To view logs for troubleshooting:"
    echo "  cd '$PROJECT_ROOT'"
    echo "  $DOCKER_COMPOSE_CMD -f docker-compose.production.yml logs api"
    echo "  $DOCKER_COMPOSE_CMD -f docker-compose.production.yml logs postgres"
    echo "  $DOCKER_COMPOSE_CMD -f docker-compose.production.yml logs redis"
    echo ""
}

cleanup_on_error() {
    log_error "Deployment failed. Cleaning up..."
    cd "$PROJECT_ROOT"
    $DOCKER_COMPOSE_CMD -f docker-compose.production.yml down
    show_logs_info
    exit 1
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Quick deployment script for AI Cash Revolution trading system.

Options:
    -h, --help          Show this help message
    -t, --type TYPE     Deployment type (local, staging, production)
    --clean             Clean previous deployment before starting
    --logs              Show logs after deployment

Environment Variables:
    DEPLOYMENT_TYPE     Deployment type (default: local)

Examples:
    $0                  # Quick local deployment
    $0 --clean          # Clean deployment
    $0 --logs           # Show logs after deployment

EOF
}

# Parse command line arguments
CLEAN_DEPLOYMENT="false"
SHOW_LOGS="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        --clean)
            CLEAN_DEPLOYMENT="true"
            shift
            ;;
        --logs)
            SHOW_LOGS="true"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Set up error handling
trap cleanup_on_error ERR

# Main deployment flow
main() {
    show_banner

    log_info "Starting AI Cash Revolution quick deployment..."
    log_info "Deployment type: $DEPLOYMENT_TYPE"

    check_prerequisites

    # Clean previous deployment if requested
    if [ "$CLEAN_DEPLOYMENT" = "true" ]; then
        log_info "Cleaning previous deployment..."
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE_CMD -f docker-compose.production.yml down -v
        docker system prune -f
    fi

    setup_environment
    deploy_infrastructure
    setup_database
    verify_deployment
    show_deployment_info

    # Show logs if requested
    if [ "$SHOW_LOGS" = "true" ]; then
        log_info "Showing service logs..."
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE_CMD -f docker-compose.production.yml logs -f
    fi
}

# Execute main function
main "$@"