# Production Deployment Guide

## Overview

This guide covers deploying the Agentic Quote-to-Underwrite system to production with comprehensive security, monitoring, and performance optimizations.

## Prerequisites

### Infrastructure Requirements
- **Docker & Docker Compose** (latest versions)
- **Redis** (for caching and rate limiting)
- **Nginx** (reverse proxy and load balancing)
- **SSL Certificates** (for HTTPS)
- **Monitoring Stack** (Prometheus + Grafana)

### System Requirements
- **CPU**: 4+ cores recommended
- **Memory**: 8GB+ RAM recommended
- **Storage**: 50GB+ SSD storage
- **Network**: Stable internet connection

## Quick Start

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd AgenticQuote

# Copy production environment template
cp .env.production.example .env.production

# Edit environment variables
nano .env.production
```

### 2. Deploy with Docker Compose
```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy to production
./deploy.sh production
```

### 3. Verify Deployment
```bash
# Check application health
curl http://localhost:8000/health

# Access dashboard
open http://localhost:8000/dashboard

# Check metrics
curl http://localhost:8000/metrics
```

## Configuration

### Environment Variables

Key production settings in `.env.production`:

```bash
# Security
SECRET_KEY=your-super-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/underwriting

# Redis
REDIS_URL=redis://localhost:6379

# CORS
CORS_ORIGINS=https://yourdomain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_PASSWORD=your-grafana-password
```

### Security Configuration

#### SSL/TLS Setup
```bash
# Generate SSL certificates (Let's Encrypt recommended)
certbot --nginx -d yourdomain.com

# Or use self-signed for development
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem
```

#### Security Headers
The system includes comprehensive security headers:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security
- Content-Security-Policy

#### Authentication
- JWT-based authentication
- Bcrypt password hashing
- Session management with Redis
- Rate limiting per user/IP

## Performance Optimization

### Caching Strategy
- **Redis**: Primary cache backend
- **Local Cache**: In-memory fallback
- **TTL Configuration**: 30min-2hours based on data type

### Database Optimization
- **Connection Pooling**: 20 max connections
- **SQLite WAL Mode**: Better concurrency
- **Strategic Indexes**: Common query patterns
- **Query Optimization**: Efficient data access

### Application Performance
- **Async Processing**: Concurrent workflow execution
- **Gunicorn**: 4 worker processes
- **Response Compression**: Gzip enabled
- **Static Asset Caching**: Long-term caching

## Monitoring & Alerting

### Metrics Collection
- **Prometheus**: Metrics storage
- **Grafana**: Visualization dashboards
- **Custom Metrics**: Application-specific KPIs

### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/health | jq '.checks.database'

# Redis connectivity
curl http://localhost:8000/health | jq '.checks.redis'
```

### Alert Rules
- **High Error Rate**: >10 errors/minute
- **High Memory Usage**: >90%
- **Low Disk Space**: <15% free
- **Service Unavailability**: Health check failures

### Log Management
- **Structured JSON Logging**: Parseable format
- **Log Rotation**: 10MB max, 5 backups
- **Centralized Collection**: Email alerts for critical errors

## Scaling Considerations

### Horizontal Scaling
```yaml
# docker-compose.yml scaling
services:
  app:
    deploy:
      replicas: 3
    environment:
      - REDIS_URL=redis://redis:6379
```

### Load Balancing
- **Nginx**: Round-robin load balancing
- **Health Checks**: Automatic failover
- **Session Affinity**: Sticky sessions if needed

### Database Scaling
- **Read Replicas**: For read-heavy workloads
- **Connection Pooling**: Efficient resource usage
- **Query Optimization**: Index tuning

## Backup & Recovery

### Automated Backups
```bash
# Database backups (daily)
0 2 * * * /path/to/backup-script.sh

# Log backups (weekly)
0 3 * * 0 /path/to/log-backup.sh
```

### Disaster Recovery
1. **Restore Database**: From latest backup
2. **Restore Configuration**: Environment files
3. **Restart Services**: `docker-compose up -d`
4. **Verify**: Health checks and functionality

## Security Best Practices

### Network Security
- **Firewall Rules**: Restrict access ports
- **VPN Access**: Secure admin access
- **Fail2Ban**: Brute force protection
- **Regular Updates**: Security patches

### Application Security
- **Input Validation**: All user inputs
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Output encoding
- **CSRF Protection**: Token validation

### Data Protection
- **Encryption**: Data at rest and in transit
- **Access Controls**: Role-based permissions
- **Audit Logging**: All access attempts
- **Data Retention**: Policy compliance

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
docker-compose logs app

# Verify configuration
docker-compose config

# Check port conflicts
netstat -tulpn | grep :8000
```

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Restart services
docker-compose restart app

# Clear cache
redis-cli FLUSHALL
```

#### Database Issues
```bash
# Check database status
sqlite3 storage/underwriting.db ".schema"

# Repair database
sqlite3 storage/underwriting.db "PRAGMA integrity_check;"
```

### Performance Tuning

#### Slow Response Times
1. **Check Metrics**: Grafana dashboards
2. **Analyze Logs**: Error patterns
3. **Profile Code**: Performance bottlenecks
4. **Optimize Queries**: Database tuning

#### High CPU Usage
1. **Scale Workers**: Increase Gunicorn workers
2. **Optimize Code**: Async operations
3. **Add Caching**: Reduce computation
4. **Scale Horizontally**: More instances

## Maintenance

### Regular Tasks
- **Weekly**: Security updates, log rotation
- **Monthly**: Performance review, backup verification
- **Quarterly**: Security audit, capacity planning

### Updates & Patches
```bash
# Update Docker images
docker-compose pull

# Restart with new images
docker-compose up -d

# Verify functionality
./health-check.sh
```

## Support

### Monitoring Dashboards
- **Main Dashboard**: http://localhost:8000/dashboard
- **Metrics**: http://localhost:8000/metrics
- **Grafana**: http://localhost:3000

### Log Locations
- **Application Logs**: `./logs/app.log`
- **Access Logs**: Nginx access logs
- **Error Logs**: Application error logs
- **System Logs**: Docker container logs

### Emergency Contacts
- **Technical Lead**: [Contact Information]
- **Infrastructure Team**: [Contact Information]
- **Security Team**: [Contact Information]

---

For additional support or questions, refer to the project documentation or create an issue in the repository.
