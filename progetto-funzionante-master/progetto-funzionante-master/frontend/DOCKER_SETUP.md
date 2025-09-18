# Docker Setup and Optimization Guide

This guide provides comprehensive instructions for setting up, optimizing, and deploying the FastAPI trading system using Docker.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Setup](#development-setup)
3. [Production Deployment](#production-deployment)
4. [Performance Optimization](#performance-optimization)
5. [Security Best Practices](#security-best-practices)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

## Quick Start

### Prerequisites

- Docker >= 20.10
- Docker Compose >= 2.0
- Python 3.11 (for local development)
- 4GB RAM minimum
- 10GB disk space minimum

### Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd progetto-funzionante-master/frontend
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start development environment**
```bash
docker-compose up -d
```

4. **Access the application**
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

## Development Setup

### Local Development

```bash
# Build and start all services
docker-compose up --build

# Start specific service
docker-compose up trading-api

# Start with monitoring stack
docker-compose --profile monitoring up -d

# View logs
docker-compose logs -f trading-api

# Stop services
docker-compose down
```

### Development with Hot Reload

```bash
# Mount local source code for development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## Production Deployment

### Production Build

```bash
# Build optimized production image
./scripts/docker-build.sh --target production --version v1.0.0

# Push to registry
./scripts/docker-build.sh --target production --version v1.0.0 --push
```

### Production Deployment

```bash
# Deploy to production
./scripts/docker-deploy.sh --env production --version v1.0.0 --backup

# Deploy with monitoring
docker-compose -f docker-compose.prod.yml --profile monitoring up -d
```

### Environment-specific Configuration

Create environment files:

**.env.production**
```env
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
JWT_SECRET_KEY=your-secret-key
OANDA_API_KEY=your-oanda-key
OANDA_ACCOUNT_ID=your-account-id
GEMINI_API_KEY=your-gemini-key
EMAIL_HOST=smtp.gmail.com
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SENTRY_DSN=your-sentry-dsn
```

## Performance Optimization

### Docker Image Optimization

The optimized Dockerfile includes:

- **Multi-stage builds** to reduce image size
- **Layer caching** for faster builds
- **Security hardening** with non-root user
- **Resource limits** and health checks
- **Optimized Python dependencies**

### Resource Allocation

**Development Resources:**
- API: 512MB RAM, 0.5 CPU
- PostgreSQL: 1GB RAM, 1.0 CPU
- Redis: 512MB RAM, 0.5 CPU

**Production Resources:**
- API: 1GB RAM, 1.0 CPU
- PostgreSQL: 2GB RAM, 2.0 CPU
- Redis: 768MB RAM, 0.8 CPU

### Performance Tuning

1. **System-level optimization:**
```bash
# Apply kernel tuning
sudo sysctl -p /etc/sysctl.d/99-docker.conf

# Optimize Docker daemon
sudo systemctl restart docker
```

2. **Application-level optimization:**
```bash
# Monitor performance
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Test performance
ab -n 1000 -c 100 http://localhost:8000/health
```

## Security Best Practices

### Container Security

- **Non-root user**: All containers run as non-root user
- **Read-only filesystem**: Where possible
- **Resource limits**: Memory and CPU constraints
- **Network isolation**: Custom networks with firewall rules
- **Secrets management**: Environment variables or Docker secrets

### Security Scanning

```bash
# Scan Docker image for vulnerabilities
./security/docker-scan.sh trading-system-api:latest

# Scan with Trivy
trivy image --severity CRITICAL,HIGH trading-system-api:latest

# Scan with Docker Scout
docker scout cves trading-system-api:latest
```

### Security Configuration

**Nginx Security:**
- HTTPS with modern ciphers
- Security headers (CSP, HSTS, X-Frame-Options)
- Rate limiting and DDoS protection
- WAF rules for common attacks

**Application Security:**
- JWT authentication
- Input validation and sanitization
- SQL injection prevention
- CORS configuration
- Request rate limiting

## Monitoring and Logging

### Monitoring Stack

1. **Prometheus**: Metrics collection and alerting
2. **Grafana**: Visualization and dashboards
3. **Alertmanager**: Alert notifications
4. **cAdvisor**: Container metrics
5. **Node Exporter**: System metrics

### Key Metrics

**Application Metrics:**
- HTTP request duration and count
- Error rates by status code
- Database query performance
- Cache hit/miss ratios
- OANDA API latency and errors

**System Metrics:**
- CPU and memory usage
- Network I/O
- Disk usage and I/O
- Container restarts

### Logging

**Structured Logging:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "message": "API request processed",
  "method": "GET",
  "path": "/health",
  "status": 200,
  "duration": 0.123,
  "user_id": null
}
```

**Log Aggregation:**
- ELK stack (Elasticsearch, Logstash, Kibana)
- Grafana Loki
- CloudWatch logs
- Splunk

### Alerting

**Critical Alerts:**
- Application down (health check failed)
- High error rates (>5%)
- Database connectivity issues
- Memory usage >90%
- Disk space >85%

**Warning Alerts:**
- High response times (>2s)
- CPU usage >80%
- Cache miss rate >50%
- OANDA API latency >5s

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check container logs
docker-compose logs trading-api

# Check health status
docker-compose ps

# Check resource usage
docker stats
```

**Database connection issues:**
```bash
# Test database connectivity
docker-compose exec postgres psql -U postgres -d trading_db

# Check database logs
docker-compose logs postgres
```

**Performance issues:**
```bash
# Monitor performance
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Check system resources
free -h
df -h
top
```

### Debug Commands

```bash
# Access running container
docker-compose exec trading-api bash

# Restart specific service
docker-compose restart trading-api

# Rebuild and restart
docker-compose up --build -d trading-api

# Clean up unused resources
docker system prune -f
docker volume prune -f
```

### Network Issues

```bash
# Check network connectivity
docker-compose exec trading-api ping postgres

# Check port exposure
docker-compose port trading-api 8000

# Check network configuration
docker network ls
docker network inspect trading-network
```

## Advanced Configuration

### Multi-Architecture Builds

```bash
# Build for multiple architectures
./scripts/docker-build.sh --platform linux/amd64,linux/arm64 --version v1.0.0 --push
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trading-api
  template:
    metadata:
      labels:
        app: trading-api
    spec:
      containers:
      - name: trading-api
        image: trading-system-api:v1.0.0
        resources:
          limits:
            memory: "1Gi"
            cpu: "1"
          requests:
            memory: "512Mi"
            cpu: "0.5"
        env:
        - name: ENVIRONMENT
          value: "production"
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### CI/CD Integration

**GitHub Actions:**
```yaml
name: Build and Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build Docker image
      run: ./scripts/docker-build.sh --target production --version ${{ github.sha }}
    - name: Deploy to production
      run: ./scripts/docker-deploy.sh --env production --version ${{ github.sha }}
```

### Backup and Recovery

```bash
# Create backup
./scripts/docker-backup.sh

# Restore from backup
./scripts/docker-restore.sh --backup-file backup_20240101_120000.tar.gz

# Scheduled backups (cron)
0 2 * * * /path/to/scripts/docker-backup.sh
```

## Maintenance

### Regular Maintenance Tasks

1. **Update base images:**
```bash
./scripts/docker-update.sh
```

2. **Clean up resources:**
```bash
docker system prune -f
docker volume prune -f
```

3. **Security scanning:**
```bash
./security/docker-scan.sh trading-system-api:latest
```

4. **Performance monitoring:**
```bash
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Scaling

**Horizontal Scaling:**
```bash
# Scale API service
docker-compose up -d --scale trading-api=3
```

**Vertical Scaling:**
```yaml
# Update docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

## Support

For issues and questions:
- Check the troubleshooting section
- Review logs: `docker-compose logs -f`
- Monitor metrics: http://localhost:3000
- Check health: http://localhost:8000/health