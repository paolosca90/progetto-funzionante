#!/bin/bash
# AI Cash Revolution SSL Certificate Setup
# Automated Let's Encrypt SSL certificate generation and renewal

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="${DOMAIN:-aicash-revolution.com}"
EMAIL="${EMAIL:-admin@aicash-revolution.com}"
STAGING="${STAGING:-false}"
CERT_DIR="/etc/ssl/certs"
WEBROOT_PATH="/var/www/certbot"

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
    log_info "Checking prerequisites for SSL setup..."

    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi

    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        log_info "Installing certbot..."

        # Install certbot based on OS
        if command -v apt-get &> /dev/null; then
            apt-get update
            apt-get install -y certbot python3-certbot-nginx
        elif command -v yum &> /dev/null; then
            yum install -y certbot python3-certbot-nginx
        else
            log_error "Unable to install certbot. Please install manually."
            exit 1
        fi
    fi

    # Check if nginx is installed
    if ! command -v nginx &> /dev/null; then
        log_error "Nginx is not installed. Please install nginx first."
        exit 1
    fi

    # Create webroot directory
    mkdir -p "$WEBROOT_PATH"
    chown -R nginx:nginx "$WEBROOT_PATH" 2>/dev/null || chown -R www-data:www-data "$WEBROOT_PATH" 2>/dev/null || true

    log_success "Prerequisites check passed"
}

setup_initial_nginx() {
    log_info "Setting up initial nginx configuration for certificate generation..."

    # Create temporary nginx config for certificate generation
    cat > /etc/nginx/sites-available/aicash-ssl-temp << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location /.well-known/acme-challenge/ {
        root $WEBROOT_PATH;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

    # Enable the temporary site
    ln -sf /etc/nginx/sites-available/aicash-ssl-temp /etc/nginx/sites-enabled/aicash-ssl-temp 2>/dev/null || true

    # Test and reload nginx
    if nginx -t; then
        systemctl reload nginx
        log_success "Initial nginx configuration activated"
    else
        log_error "Nginx configuration test failed"
        exit 1
    fi
}

generate_certificates() {
    log_info "Generating SSL certificates with Let's Encrypt..."

    local certbot_args=(
        "certonly"
        "--webroot"
        "--webroot-path=$WEBROOT_PATH"
        "--email=$EMAIL"
        "--agree-tos"
        "--no-eff-email"
        "--domains=$DOMAIN,www.$DOMAIN"
        "--non-interactive"
    )

    # Use staging environment for testing
    if [[ "$STAGING" == "true" ]]; then
        log_warning "Using Let's Encrypt staging environment"
        certbot_args+=("--staging")
    fi

    # Generate certificates
    if certbot "${certbot_args[@]}"; then
        log_success "SSL certificates generated successfully"
    else
        log_error "Failed to generate SSL certificates"
        exit 1
    fi
}

install_certificates() {
    log_info "Installing SSL certificates..."

    # Create certificate directory
    mkdir -p "$CERT_DIR"

    # Copy certificates to expected location
    local le_cert_dir="/etc/letsencrypt/live/$DOMAIN"

    if [[ -d "$le_cert_dir" ]]; then
        cp "$le_cert_dir/fullchain.pem" "$CERT_DIR/fullchain.pem"
        cp "$le_cert_dir/privkey.pem" "$CERT_DIR/privkey.pem"
        cp "$le_cert_dir/chain.pem" "$CERT_DIR/chain.pem"

        # Set proper permissions
        chmod 644 "$CERT_DIR/fullchain.pem"
        chmod 644 "$CERT_DIR/chain.pem"
        chmod 600 "$CERT_DIR/privkey.pem"
        chown root:root "$CERT_DIR"/*.pem

        log_success "SSL certificates installed"
    else
        log_error "Certificate directory not found: $le_cert_dir"
        exit 1
    fi
}

setup_production_nginx() {
    log_info "Setting up production nginx configuration with SSL..."

    # Remove temporary configuration
    rm -f /etc/nginx/sites-enabled/aicash-ssl-temp

    # The production nginx.conf should already be in place
    # Just test and reload
    if nginx -t; then
        systemctl reload nginx
        log_success "Production nginx configuration activated with SSL"
    else
        log_error "Production nginx configuration test failed"
        exit 1
    fi
}

setup_certificate_renewal() {
    log_info "Setting up automatic certificate renewal..."

    # Create renewal script
    cat > /usr/local/bin/renew-aicash-ssl.sh << 'EOF'
#!/bin/bash
# AI Cash Revolution SSL Certificate Renewal Script

# Renew certificates
/usr/bin/certbot renew --quiet

# Reload nginx if certificates were renewed
if [[ $? -eq 0 ]]; then
    # Copy renewed certificates
    DOMAIN="aicash-revolution.com"
    CERT_DIR="/etc/ssl/certs"
    LE_CERT_DIR="/etc/letsencrypt/live/$DOMAIN"

    if [[ -d "$LE_CERT_DIR" ]]; then
        cp "$LE_CERT_DIR/fullchain.pem" "$CERT_DIR/fullchain.pem"
        cp "$LE_CERT_DIR/privkey.pem" "$CERT_DIR/privkey.pem"
        cp "$LE_CERT_DIR/chain.pem" "$CERT_DIR/chain.pem"

        # Reload nginx
        systemctl reload nginx

        echo "SSL certificates renewed and nginx reloaded"
    fi
fi
EOF

    # Make renewal script executable
    chmod +x /usr/local/bin/renew-aicash-ssl.sh

    # Add cron job for automatic renewal (twice daily)
    cat > /etc/cron.d/aicash-ssl-renewal << EOF
# AI Cash Revolution SSL Certificate Renewal
# Runs twice daily at random times to avoid rate limiting
17 2,14 * * * root /usr/local/bin/renew-aicash-ssl.sh >/var/log/le-renew.log 2>&1
EOF

    log_success "Automatic certificate renewal configured"
}

verify_ssl_setup() {
    log_info "Verifying SSL setup..."

    # Check if certificates exist
    if [[ -f "$CERT_DIR/fullchain.pem" && -f "$CERT_DIR/privkey.pem" ]]; then
        log_success "SSL certificates found"
    else
        log_error "SSL certificates not found"
        exit 1
    fi

    # Check certificate validity
    local cert_info
    cert_info=$(openssl x509 -in "$CERT_DIR/fullchain.pem" -text -noout)

    if echo "$cert_info" | grep -q "$DOMAIN"; then
        log_success "Certificate is valid for domain: $DOMAIN"
    else
        log_error "Certificate validation failed"
        exit 1
    fi

    # Check nginx status
    if systemctl is-active --quiet nginx; then
        log_success "Nginx is running"
    else
        log_error "Nginx is not running"
        exit 1
    fi

    # Test HTTPS connection
    log_info "Testing HTTPS connection..."
    if curl -I --connect-timeout 10 "https://$DOMAIN/health" &>/dev/null; then
        log_success "HTTPS connection test passed"
    else
        log_warning "HTTPS connection test failed (this may be normal if the application is not running)"
    fi
}

show_ssl_info() {
    log_info "SSL Certificate Information:"

    openssl x509 -in "$CERT_DIR/fullchain.pem" -text -noout | grep -E "(Subject|Issuer|Not Before|Not After)"

    log_info "Certificate files location: $CERT_DIR"
    log_info "Automatic renewal: Configured to run twice daily"
    log_info "Manual renewal command: /usr/local/bin/renew-aicash-ssl.sh"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Setup SSL certificates for AI Cash Revolution using Let's Encrypt.

Options:
    -h, --help          Show this help message
    -d, --domain        Domain name (default: aicash-revolution.com)
    -e, --email         Email for Let's Encrypt (default: admin@aicash-revolution.com)
    -s, --staging       Use Let's Encrypt staging environment for testing
    --verify-only       Only verify existing SSL setup

Environment Variables:
    DOMAIN             Domain name to secure
    EMAIL              Email address for Let's Encrypt notifications
    STAGING            Use staging environment (true/false)

Examples:
    $0                                          # Setup SSL for default domain
    $0 -d mydomain.com -e admin@mydomain.com    # Setup SSL for custom domain
    $0 -s                                       # Setup SSL using staging environment
    $0 --verify-only                            # Verify existing SSL setup

EOF
}

# Parse command line arguments
VERIFY_ONLY="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        -s|--staging)
            STAGING="true"
            shift
            ;;
        --verify-only)
            VERIFY_ONLY="true"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    log_info "Starting SSL setup for AI Cash Revolution..."
    log_info "Domain: $DOMAIN"
    log_info "Email: $EMAIL"

    if [[ "$VERIFY_ONLY" == "true" ]]; then
        verify_ssl_setup
        show_ssl_info
        exit 0
    fi

    check_prerequisites
    setup_initial_nginx
    generate_certificates
    install_certificates
    setup_production_nginx
    setup_certificate_renewal
    verify_ssl_setup
    show_ssl_info

    log_success "SSL setup completed successfully!"
    log_info "Your site is now secured with HTTPS"
}

# Execute main function
main "$@"