"""
Performance optimization: caching, async processing, database optimization.
"""

import asyncio
import json
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
from datetime import datetime, timedelta
import redis
import sqlite3
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Advanced caching with Redis backend."""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis = redis.from_url(redis_url, decode_responses=False)
        self.default_ttl = default_ttl
        self.local_cache = {}  # In-memory fallback
        self.local_cache_ttl = {}
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            # Try Redis first
            if self.redis:
                value = self.redis.get(key)
                if value:
                    return pickle.loads(value)
            
            # Fallback to local cache
            if key in self.local_cache:
                if datetime.now() < self.local_cache_ttl.get(key, datetime.min):
                    return self.local_cache[key]
                else:
                    del self.local_cache[key]
                    if key in self.local_cache_ttl:
                        del self.local_cache_ttl[key]
            
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            ttl = ttl or self.default_ttl
            
            # Set in Redis
            if self.redis:
                serialized = pickle.dumps(value)
                self.redis.setex(key, ttl, serialized)
            
            # Set in local cache as backup
            self.local_cache[key] = value
            self.local_cache_ttl[key] = datetime.now() + timedelta(seconds=ttl)
            
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if self.redis:
                self.redis.delete(key)
            
            if key in self.local_cache:
                del self.local_cache[key]
            if key in self.local_cache_ttl:
                del self.local_cache_ttl[key]
            
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern."""
        try:
            count = 0
            if self.redis:
                keys = self.redis.keys(pattern)
                if keys:
                    count = self.redis.delete(*keys)
            
            # Clear local cache
            keys_to_delete = [k for k in self.local_cache.keys() if pattern.replace('*', '') in k]
            for key in keys_to_delete:
                del self.local_cache[key]
                if key in self.local_cache_ttl:
                    del self.local_cache_ttl[key]
            
            return count
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0


# Global cache manager
cache_manager = None

def init_cache(redis_url: str):
    """Initialize cache manager."""
    global cache_manager
    cache_manager = CacheManager(redis_url)


def cached(prefix: str, ttl: Optional[int] = None):
    """Decorator for caching function results."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not cache_manager:
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = cache_manager._make_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


class DatabaseOptimizer:
    """Database performance optimizations."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def optimize_sqlite(self):
        """Apply SQLite performance optimizations."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys=ON")
            
            # Optimize for SSD storage
            conn.execute("PRAGMA synchronous=NORMAL")
            
            # Increase cache size (10MB)
            conn.execute("PRAGMA cache_size=10000")
            
            # Optimize for read-heavy workloads
            conn.execute("PRAGMA temp_store=MEMORY")
            
            # Create indexes for common queries
            self._create_indexes(conn)
            
            conn.commit()
    
    def _create_indexes(self, conn):
        """Create performance indexes."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_run_records_created_at ON run_records(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_run_records_status ON run_records(status)",
            "CREATE INDEX IF NOT EXISTS idx_run_records_created_status ON run_records(created_at, status)",
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(index_sql)
            except sqlite3.Error as e:
                logger.warning(f"Index creation failed: {e}")
    
    @asynccontextmanager
    async def get_connection(self):
        """Async database connection context manager."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        try:
            yield conn
        finally:
            conn.close()
    
    async def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute query with connection pooling."""
        async with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> bool:
        """Execute multiple queries efficiently."""
        async with self.get_connection() as conn:
            conn.executemany(query, params_list)
            conn.commit()
            return True


class AsyncProcessor:
    """Async processing for concurrent operations."""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def process_concurrent(self, tasks: List[Callable], *args, **kwargs) -> List[Any]:
        """Process multiple tasks concurrently with semaphore control."""
        async def limited_task(task):
            async with self.semaphore:
                if asyncio.iscoroutinefunction(task):
                    return await task(*args, **kwargs)
                else:
                    return task(*args, **kwargs)
        
        return await asyncio.gather(
            *[limited_task(task) for task in tasks],
            return_exceptions=True
        )
    
    async def batch_process(self, items: List[Any], processor: Callable, 
                         batch_size: int = 10) -> List[Any]:
        """Process items in batches for better performance."""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_tasks = [processor(item) for item in batch]
            batch_results = await self.process_concurrent(batch_tasks)
            results.extend(batch_results)
        
        return results


class PerformanceMonitor:
    """Monitor and log performance metrics."""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.start_times[operation] = datetime.now()
    
    def end_timer(self, operation: str) -> float:
        """End timing and return duration."""
        if operation in self.start_times:
            duration = (datetime.now() - self.start_times[operation]).total_seconds()
            self.record_metric(operation, duration)
            del self.start_times[operation]
            return duration
        return 0.0
    
    def record_metric(self, metric: str, value: float):
        """Record a performance metric."""
        if metric not in self.metrics:
            self.metrics[metric] = []
        self.metrics[metric].append(value)
    
    def get_stats(self, metric: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        if metric not in self.metrics or not self.metrics[metric]:
            return {}
        
        values = self.metrics[metric]
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "recent": values[-10:]  # Last 10 measurements
        }


# Global performance monitor
perf_monitor = PerformanceMonitor()


def performance_monitor(operation_name: str):
    """Decorator to monitor function performance."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            perf_monitor.start_timer(operation_name)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                perf_monitor.end_timer(operation_name)
        return wrapper
    return decorator


class ConnectionPool:
    """Database connection pool for better performance."""
    
    def __init__(self, db_path: str, max_connections: int = 20):
        self.db_path = db_path
        self.max_connections = max_connections
        self.pool = asyncio.Queue(maxsize=max_connections)
        self.created_connections = 0
    
    async def get_connection(self) -> sqlite3.Connection:
        """Get connection from pool."""
        try:
            # Try to get existing connection
            conn = self.pool.get_nowait()
            return conn
        except asyncio.QueueEmpty:
            # Create new connection if under limit
            if self.created_connections < self.max_connections:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                self.created_connections += 1
                return conn
            else:
                # Wait for available connection
                return await self.pool.get()
    
    async def return_connection(self, conn: sqlite3.Connection):
        """Return connection to pool."""
        try:
            self.pool.put_nowait(conn)
        except asyncio.QueueFull:
            # Pool is full, close connection
            conn.close()
            self.created_connections -= 1


# Initialize performance components
db_optimizer = None
async_processor = None
connection_pool = None

def init_performance(db_path: str, redis_url: str):
    """Initialize performance components."""
    global db_optimizer, async_processor, connection_pool
    
    db_optimizer = DatabaseOptimizer(db_path)
    db_optimizer.optimize_sqlite()
    
    async_processor = AsyncProcessor()
    connection_pool = ConnectionPool(db_path)


# Example usage for RAG caching
@cached("rag_retrieval", ttl=1800)  # 30 minutes
async def cached_rag_retrieval(query: str, n_results: int = 5):
    """Cached RAG retrieval."""
    # Your RAG retrieval logic here
    pass

@cached("address_normalization", ttl=3600)  # 1 hour
async def cached_address_normalization(address: str):
    """Cached address normalization."""
    # Your address normalization logic here
    pass

@cached("hazard_scores", ttl=7200)  # 2 hours
async def cached_hazard_scores(lat: float, lon: float):
    """Cached hazard score calculation."""
    # Your hazard scoring logic here
    pass
