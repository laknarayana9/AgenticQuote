#!/bin/bash

# Production deployment script for Agentic Quote-to-Underwrite

set -e

echo "🚀 Starting production deployment..."

# Configuration
ENVIRONMENT=${1:-production}
BACKUP_DIR="./backups"
LOG_DIR="./logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create necessary directories
mkdir -p $BACKUP_DIR
mkdir -p $LOG_DIR

echo "📦 Building Docker images..."

# Build application image
docker build -t agentic-quote:latest .

echo "🗄️ Backing up data..."

# Backup database
if [ -f "storage/underwriting.db" ]; then
    cp storage/underwriting.db $BACKUP_DIR/underwriting_$TIMESTAMP.db
    echo "✅ Database backed up"
fi

# Backup logs
if [ -d "$LOG_DIR" ]; then
    tar -czf $BACKUP_DIR/logs_$TIMESTAMP.tar.gz $LOG_DIR/
    echo "✅ Logs backed up"
fi

echo "🔄 Deploying new version..."

# Stop existing services
docker-compose down

# Pull latest images (if using external services)
docker-compose pull

# Start services
docker-compose up -d

echo "⏳ Waiting for services to start..."

# Wait for application to be healthy
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Application is healthy!"
        break
    fi
    echo "⏳ Waiting for application... ($i/30)"
    sleep 10
done

if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Application failed to start!"
    echo "📋 Showing logs:"
    docker-compose logs app
    exit 1
fi

echo "🧪 Running health checks..."

# Check all services
docker-compose ps

# Test API endpoints
echo "Testing API endpoints..."

# Health check
curl -f http://localhost:8000/health || echo "❌ Health check failed"

# Metrics endpoint
curl -f http://localhost:8000/metrics || echo "❌ Metrics endpoint failed"

# Dashboard
curl -f http://localhost:8000/dashboard || echo "❌ Dashboard failed"

echo "📊 Deployment summary:"
echo "Environment: $ENVIRONMENT"
echo "Timestamp: $TIMESTAMP"
echo "Application URL: http://localhost:8000"
echo "Dashboard URL: http://localhost:8000/dashboard"
echo "Metrics URL: http://localhost:8000/metrics"

# Show resource usage
echo "📈 Resource usage:"
docker stats --no-stream

echo "🎉 Deployment completed successfully!"

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "🧹 Old backups cleaned up"

echo "📝 Post-deployment checklist:"
echo "□ Monitor application logs: docker-compose logs -f app"
echo "□ Check metrics dashboard: http://localhost:3000 (Grafana)"
echo "□ Monitor system resources: docker stats"
echo "□ Test full workflow with sample data"
echo "□ Verify all integrations are working"

echo "✨ Deployment finished at $(date)"
