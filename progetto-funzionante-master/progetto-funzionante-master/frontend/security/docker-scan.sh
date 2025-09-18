#!/bin/bash

# Docker Security Scanning Script
# This script performs comprehensive security scanning of Docker images

set -euo pipefail

# Configuration
IMAGE_NAME=${1:-"trading-system-api:latest"}
REGISTRY=${2:-"docker.io"}
SCAN_DIR="${SCAN_DIR:-./security/scans}"
REPORT_DIR="${REPORT_DIR:-./security/reports}"
DATE=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Create directories
mkdir -p "$SCAN_DIR" "$REPORT_DIR"

log "Starting Docker security scan for image: $IMAGE_NAME"

# 1. Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    error "Docker is not running or not accessible"
    exit 1
fi

# 2. Pull the latest image
log "Pulling Docker image: $IMAGE_NAME"
docker pull "$IMAGE_NAME" || warn "Failed to pull image, using local version"

# 3. Run Docker Scout scan (if available)
if command -v docker-scout >/dev/null 2>&1; then
    log "Running Docker Scout vulnerability scan..."
    docker scout cves "$IMAGE_NAME" > "$SCAN_DIR/scout_scan_$DATE.txt" 2>&1 || \
        warn "Docker Scout scan failed"

    # Generate Scout report
    docker scout quickview "$IMAGE_NAME" > "$REPORT_DIR/scout_report_$DATE.json" 2>&1 || \
        warn "Docker Scout report generation failed"
fi

# 4. Run Trivy scan (if available)
if command -v trivy >/dev/null 2>&1; then
    log "Running Trivy vulnerability scan..."
    trivy image --format json --output "$REPORT_DIR/trivy_report_$DATE.json" "$IMAGE_NAME" || \
        warn "Trivy scan failed"

    # Generate summary report
    trivy image --severity CRITICAL,HIGH "$IMAGE_NAME" > "$REPORT_DIR/trivy_summary_$DATE.txt" 2>&1 || \
        warn "Trivy summary failed"
else
    warn "Trivy not found. Install with: brew install trivy"
fi

# 5. Run Snyk scan (if available)
if command -v snyk >/dev/null 2>&1; then
    log "Running Snyk vulnerability scan..."
    snyk container test "$IMAGE_NAME" --json-file-output="$REPORT_DIR/snyk_report_$DATE.json" || \
        warn "Snyk scan failed"
else
    warn "Snyk not found. Install with: npm install -g snyk"
fi

# 6. Run Hadolint (Dockerfile linting)
if command -v hadolint >/dev/null 2>&1; then
    log "Running Hadolint Dockerfile analysis..."
    hadolint Dockerfile > "$REPORT_DIR/hadolint_report_$DATE.txt" 2>&1 || \
        warn "Hadolint analysis failed"
else
    warn "Hadolint not found. Install with: brew install hadolint"
fi

# 7. Check image size and layers
log "Analyzing Docker image size and layers..."
docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" > "$REPORT_DIR/image_info_$DATE.txt"

docker history "$IMAGE_NAME" --format "table {{.CreatedBy}}\t{{.Size}}\t{{.CreatedAt}}" > "$REPORT_DIR/layers_$DATE.txt"

# 8. Check for exposed ports and volumes
log "Checking exposed ports and volumes..."
docker inspect --format='{{range .Config.ExposedPorts}}{{.Port}} {{end}}' "$IMAGE_NAME" > "$REPORT_DIR/exposed_ports_$DATE.txt"
docker inspect --format='{{range .Config.Volumes}}{{.}} {{end}}' "$IMAGE_NAME" > "$REPORT_DIR/volumes_$DATE.txt"

# 9. Run custom security checks
log "Running custom security checks..."

# Check for non-root user
USER_CHECK=$(docker inspect --format='{{.Config.User}}' "$IMAGE_NAME")
if [[ "$USER_CHECK" == "0" ]] || [[ -z "$USER_CHECK" ]]; then
    warn "Container runs as root user"
    echo "ROOT_USER_DETECTED=true" >> "$REPORT_DIR/security_issues_$DATE.txt"
fi

# Check for health checks
HEALTH_CHECK=$(docker inspect --format='{{json .Config.Healthcheck}}' "$IMAGE_NAME")
if [[ "$HEALTH_CHECK" == "null" ]]; then
    warn "No health check configured"
    echo "NO_HEALTH_CHECK=true" >> "$REPORT_DIR/security_issues_$DATE.txt"
fi

# Check environment variables
ENV_VARS=$(docker inspect --format='{{range .Config.Env}}{{.}} {{end}}' "$IMAGE_NAME")
if echo "$ENV_VARS" | grep -qi "password\|secret\|key"; then
    warn "Potential secrets in environment variables"
    echo "SECRETS_IN_ENV=true" >> "$REPORT_DIR/security_issues_$DATE.txt"
fi

# 10. Generate summary report
log "Generating summary report..."
cat > "$REPORT_DIR/summary_$DATE.txt" << EOF
Docker Security Scan Summary
============================
Date: $(date)
Image: $IMAGE_NAME

Security Tools Used:
- Docker Scout: $(command -v docker-scout >/dev/null 2>&1 && echo "Available" || echo "Not Available")
- Trivy: $(command -v trivy >/dev/null 2>&1 && echo "Available" || echo "Not Available")
- Snyk: $(command -v snyk >/dev/null 2>&1 && echo "Available" || echo "Not Available")
- Hadolint: $(command -v hadolint >/dev/null 2>&1 && echo "Available" || echo "Not Available")

Image Information:
$(cat "$REPORT_DIR/image_info_$DATE.txt")

Security Issues Found:
$(test -f "$REPORT_DIR/security_issues_$DATE.txt" && cat "$REPORT_DIR/security_issues_$DATE.txt" || echo "No issues detected")

Recommendations:
1. Always run containers as non-root users
2. Use multi-stage builds to reduce image size
3. Regularly update base images
4. Implement health checks
5. Use environment variables instead of hardcoding secrets
6. Limit container capabilities
7. Use read-only filesystems where possible

Scan Results Location:
- Scout Scan: $SCAN_DIR/scout_scan_$DATE.txt
- Trivy Report: $REPORT_DIR/trivy_report_$DATE.json
- Snyk Report: $REPORT_DIR/snyk_report_$DATE.json
- Hadolint Report: $REPORT_DIR/hadolint_report_$DATE.txt
- Summary: $REPORT_DIR/summary_$DATE.txt
EOF

log "Security scan completed successfully!"
log "Summary report available at: $REPORT_DIR/summary_$DATE.txt"

# Display critical issues if any
if [[ -f "$REPORT_DIR/security_issues_$DATE.txt" ]]; then
    error "Critical security issues detected:"
    cat "$REPORT_DIR/security_issues_$DATE.txt"
fi

exit 0