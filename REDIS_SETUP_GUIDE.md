# Redis Message Queue Setup Guide

## Overview

The Agentic Quote-to-Underwrite system now uses Redis for production-grade message queuing, providing persistence, scalability, and reliability.

## Redis Installation

### **Option 1: Local Development (Docker)**
```bash
# Pull and run Redis
docker run -d --name redis-queue -p 6379:6379 redis:7-alpine

# Or with persistence
docker run -d --name redis-queue \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine redis-server --appendonly yes
```

### **Option 2: Local Installation**
```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server

# Windows (WSL)
sudo apt-get install redis-server
sudo service redis-server start
```

### **Option 3: Redis Cloud (Production)**
```bash
# Install Redis CLI
curl -fsSL https://packages.redis.io/redis-cli/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt-get update
sudo apt-get install redis-tools

# Connect to Redis Cloud
redis-cli -u redis://username:password@host:port
```

## Configuration

### **Environment Variables**
Add to your `.env` file:
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_password  # Optional
REDIS_DB=0                    # Database number
```

### **Redis Configuration (redis.conf)**
```conf
# Memory Management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1    # Save after 900 seconds if 1 key changed
save 300 10   # Save after 300 seconds if 10 keys changed
save 60 10000 # Save after 60 seconds if 10000 keys changed

# Security
requirepass your_password
bind 127.0.0.1

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

## Application Integration

### **Automatic Redis Detection**
The application automatically detects Redis availability:

```python
# On startup
@app.on_event("startup")
async def startup_event():
    try:
        await redis_message_queue.initialize()
        logger.info("Redis message queue initialized")
    except Exception as e:
        logger.error(f"Redis not available: {e}")
        # Falls back to in-memory queue
```

### **Health Check**
```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "message": "Complete app working with Redis queue",
  "timestamp": "2026-02-20T...",
  "redis": {
    "connected": true,
    "queue_stats": {
      "pending_count": 0,
      "processing_count": 0,
      "completed_count": 0
    }
  }
}
```

## Queue Operations

### **1. Submit Quote to Queue**
```bash
curl -X POST http://localhost:8000/quote/submit \
  -H "Content-Type: application/json" \
  -d '{
    "submission": {
      "applicant_name": "John Doe",
      "address": "123 Main St",
      "coverage_amount": 250000
    },
    "use_agentic": false
  }'
```

### **2. Check Queue Status**
```bash
curl http://localhost:8000/queue/stats
```

### **3. Monitor Message Status**
```bash
curl http://localhost:8000/queue/{message_id}
```

## Redis Data Structures

### **Queue Storage**
```redis
# Sorted set for pending messages (priority-based)
ZADD quote_processing_queue -3 '{"id":"msg123","priority":3,"status":"pending"}'

# Hash for processing messages
HSET quote_processing_processing msg123 '{"id":"msg123","status":"processing"}'

# Hash for completed messages
HSET quote_processing_completed msg123 '{"id":"msg123","status":"completed"}'

# Hash for statistics
HSET quote_processing_stats total_enqueued 150
```

### **Key Expiration**
- **Processing messages**: 6 minutes (timeout + buffer)
- **Completed messages**: 24 hours (automatic cleanup)
- **Statistics**: Persistent

## Production Considerations

### **1. High Availability**
```yaml
# docker-compose.yml
version: '3.8'
services:
  redis-master:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-master-data:/data
    command: redis-server --appendonly yes

  redis-replica:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    volumes:
      - redis-replica-data:/data
    command: redis-server --replicaof redis-master 6379 --appendonly yes
    depends_on:
      - redis-master

volumes:
  redis-master-data:
  redis-replica-data:
```

### **2. Monitoring**
```bash
# Redis CLI monitoring
redis-cli monitor

# Redis info
redis-cli info memory
redis-cli info stats
redis-cli info replication

# Application queue stats
curl http://localhost:8000/queue/stats
```

### **3. Backup and Recovery**
```bash
# Manual backup
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb /backup/redis-$(date +%Y%m%d).rdb

# Restore
redis-cli FLUSHALL
redis-cli --rdb /backup/redis-20260220.rdb
```

### **4. Performance Tuning**
```conf
# redis.conf optimizations
tcp-keepalive 300
timeout 0
tcp-backlog 511
databases 16

# Memory optimization
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
```

## Troubleshooting

### **Common Issues**

#### **1. Connection Refused**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
docker start redis-queue   # Docker
```

#### **2. Memory Issues**
```bash
# Check Redis memory usage
redis-cli info memory | grep used_memory_human

# Clear old data
redis-cli FLUSHDB  # Clear current database
```

#### **3. Queue Not Processing**
```bash
# Check queue stats
curl http://localhost:8000/queue/stats

# Check Redis keys
redis-cli KEYS "quote_processing_*"

# Monitor Redis
redis-cli monitor
```

### **Debug Commands**
```bash
# Check all queue keys
redis-cli KEYS "quote_processing_*"

# View pending messages
redis-cli ZRANGE quote_processing_queue 0 -1

# View processing messages
redis-cli HGETALL quote_processing_processing

# View completed messages
redis-cli HGETALL quote_processing_completed

# Check statistics
redis-cli HGETALL quote_processing_stats
```

## Migration from In-Memory Queue

The upgrade is seamless - just start Redis and the application will automatically detect and use it:

1. **Install Redis** (see options above)
2. **Start Redis service**
3. **Restart application**
4. **Verify with health check**

All existing API endpoints work exactly the same, but now with Redis persistence and scalability!

## Benefits of Redis Queue

### **✅ Production Features**
- **Persistence**: Messages survive server restarts
- **Scalability**: Multiple consumers can process from same queue
- **Monitoring**: Built-in Redis monitoring tools
- **Performance**: Sub-millisecond operations
- **Reliability**: Proven battle-tested technology

### **✅ Operational Benefits**
- **Zero Code Changes**: Same API interface
- **Easy Deployment**: Docker or native installation
- **Monitoring**: Rich metrics and observability
- **Backup**: Simple data persistence
- **High Availability**: Master-replica configuration

The Redis message queue provides enterprise-grade reliability while maintaining the simple, clean interface of the original in-memory implementation.
