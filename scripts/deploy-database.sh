#!/bin/bash
# AI Cash Revolution Database Deployment Script
# Handles Prisma migrations, seeding, and database setup for production

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
SERVER_DIR="$PROJECT_ROOT/server"

# Default values
ENVIRONMENT="${ENVIRONMENT:-production}"
SKIP_BACKUP="${SKIP_BACKUP:-false}"
FORCE_RESET="${FORCE_RESET:-false}"

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

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if we're in the correct directory
    if [ ! -f "$SERVER_DIR/package.json" ]; then
        log_error "Server package.json not found. Are you in the correct directory?"
        exit 1
    fi

    # Check if Prisma is installed
    if ! command -v npx &> /dev/null; then
        log_error "npx not found. Please install Node.js and npm."
        exit 1
    fi

    # Check environment variables
    if [ -z "${DATABASE_URL:-}" ]; then
        log_error "DATABASE_URL environment variable is required"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

backup_database() {
    if [ "$SKIP_BACKUP" = "true" ]; then
        log_warning "Skipping database backup (SKIP_BACKUP=true)"
        return 0
    fi

    log_info "Creating database backup..."

    local backup_dir="$PROJECT_ROOT/backups"
    local backup_file="$backup_dir/backup_$(date +%Y%m%d_%H%M%S).sql"

    mkdir -p "$backup_dir"

    # Extract database connection details from DATABASE_URL
    local db_url="${DATABASE_URL}"
    local pg_dump_cmd="pg_dump"

    # Use Docker if running in containerized environment
    if command -v docker &> /dev/null && docker ps | grep -q postgres; then
        pg_dump_cmd="docker exec aicash-postgres pg_dump"
    fi

    if $pg_dump_cmd "$db_url" > "$backup_file"; then
        log_success "Database backup created: $backup_file"

        # Keep only last 10 backups
        ls -t "$backup_dir"/backup_*.sql | tail -n +11 | xargs -r rm
    else
        log_error "Failed to create database backup"
        exit 1
    fi
}

deploy_migrations() {
    log_info "Deploying database migrations..."

    cd "$SERVER_DIR"

    # Generate Prisma client
    log_info "Generating Prisma client..."
    npx prisma generate

    # Deploy migrations
    log_info "Deploying migrations to database..."
    if npx prisma migrate deploy; then
        log_success "Database migrations deployed successfully"
    else
        log_error "Failed to deploy database migrations"
        exit 1
    fi
}

seed_database() {
    log_info "Seeding database with initial data..."

    cd "$SERVER_DIR"

    # Check if seed script exists
    if [ ! -f "prisma/seed.js" ]; then
        log_warning "No seed script found (prisma/seed.js), skipping seeding"
        return 0
    fi

    # Run seed script
    if npx prisma db seed; then
        log_success "Database seeded successfully"
    else
        log_warning "Database seeding failed or partially completed"
    fi
}

verify_deployment() {
    log_info "Verifying database deployment..."

    cd "$SERVER_DIR"

    # Check database connection
    if npx prisma db status; then
        log_success "Database connection verified"
    else
        log_error "Database connection verification failed"
        exit 1
    fi

    # Validate schema
    log_info "Validating database schema..."
    if npx prisma validate; then
        log_success "Database schema validation passed"
    else
        log_error "Database schema validation failed"
        exit 1
    fi
}

reset_database() {
    if [ "$FORCE_RESET" != "true" ]; then
        log_error "Database reset requires FORCE_RESET=true"
        exit 1
    fi

    log_warning "Resetting database (FORCE_RESET=true)..."

    cd "$SERVER_DIR"

    # Reset database
    npx prisma migrate reset --force

    log_success "Database reset completed"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy AI Cash Revolution database with Prisma migrations.

Options:
    -h, --help          Show this help message
    -e, --environment   Set environment (default: production)
    -s, --skip-backup   Skip database backup
    -r, --reset         Reset database (requires confirmation)
    -f, --force         Force operations without prompts

Environment Variables:
    DATABASE_URL        PostgreSQL connection string (required)
    SKIP_BACKUP         Skip backup creation (default: false)
    FORCE_RESET         Allow database reset (default: false)

Examples:
    $0                                  # Standard deployment
    $0 --skip-backup                    # Deploy without backup
    $0 --environment staging            # Deploy to staging
    FORCE_RESET=true $0 --reset         # Reset database

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--skip-backup)
            SKIP_BACKUP="true"
            shift
            ;;
        -r|--reset)
            reset_database
            exit 0
            ;;
        -f|--force)
            FORCE_RESET="true"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main deployment flow
main() {
    log_info "Starting AI Cash Revolution database deployment..."
    log_info "Environment: $ENVIRONMENT"

    check_prerequisites
    backup_database
    deploy_migrations
    seed_database
    verify_deployment

    log_success "Database deployment completed successfully!"
    log_info "Database is ready for application startup"
}

# Execute main function
main "$@"