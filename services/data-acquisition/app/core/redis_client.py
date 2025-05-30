"""
Redis client and caching utilities for Data Acquisition Service
"""

import json
import logging
from typing import Any, Optional, Union, Dict
from datetime import datetime, timedelta

import aioredis
from aioredis import Redis

from app.core.config import get_settings, get_cache_key

logger = logging.getLogger(__name__)

# Global Redis connection
_redis_client: Optional[Redis] = None


async def create_redis_client() -> Redis:
    """Create Redis client connection"""
    global _redis_client
    
    if _redis_client is None:
        settings = get_settings()
        
        try:
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await _redis_client.ping()
            logger.info("Redis client connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    return _redis_client


async def get_redis_client() -> Redis:
    """Get Redis client instance"""
    if _redis_client is None:
        return await create_redis_client()
    return _redis_client


class CacheManager:
    """Redis cache manager for market data"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.settings = get_settings()
    
    async def initialize(self):
        """Initialize cache manager"""
        self.redis = await get_redis_client()
    
    async def set_cache(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        key_type: Optional[str] = None
    ) -> bool:
        """
        Set cache value with optional TTL
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds
            key_type: Type of cache key for default TTL
        """
        try:
            if self.redis is None:
                await self.initialize()
            
            # Determine TTL
            if ttl is None and key_type:
                ttl = self._get_default_ttl(key_type)
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)
            
            # Set cache
            if ttl:
                await self.redis.setex(key, ttl, serialized_value)
            else:
                await self.redis.set(key, serialized_value)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            return False
    
    async def get_cache(self, key: str, default: Any = None) -> Any:
        """
        Get cache value
        
        Args:
            key: Cache key
            default: Default value if key not found
        
        Returns:
            Cached value or default
        """
        try:
            if self.redis is None:
                await self.initialize()
            
            value = await self.redis.get(key)
            
            if value is None:
                return default
            
            # Try to deserialize as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return default
    
    async def delete_cache(self, key: str) -> bool:
        """Delete cache key"""
        try:
            if self.redis is None:
                await self.initialize()
            
            result = await self.redis.delete(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if cache key exists"""
        try:
            if self.redis is None:
                await self.initialize()
            
            result = await self.redis.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error checking cache existence for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key"""
        try:
            if self.redis is None:
                await self.initialize()
            
            ttl = await self.redis.ttl(key)
            return ttl if ttl > 0 else None
            
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return None
    
    async def set_hash(self, key: str, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set hash data in cache"""
        try:
            if self.redis is None:
                await self.initialize()
            
            # Serialize hash values
            serialized_mapping = {}
            for field, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized_mapping[field] = json.dumps(value, default=str)
                else:
                    serialized_mapping[field] = str(value)
            
            await self.redis.hset(key, mapping=serialized_mapping)
            
            if ttl:
                await self.redis.expire(key, ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting hash for key {key}: {e}")
            return False
    
    async def get_hash(self, key: str, field: Optional[str] = None) -> Any:
        """Get hash data from cache"""
        try:
            if self.redis is None:
                await self.initialize()
            
            if field:
                value = await self.redis.hget(key, field)
                if value:
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value
                return None
            else:
                hash_data = await self.redis.hgetall(key)
                if not hash_data:
                    return {}
                
                # Deserialize values
                result = {}
                for field, value in hash_data.items():
                    try:
                        result[field] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[field] = value
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting hash for key {key}: {e}")
            return {} if field is None else None
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        try:
            if self.redis is None:
                await self.initialize()
            
            return await self.redis.incr(key, amount)
            
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            return 0
    
    async def set_with_timestamp(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cache value with timestamp"""
        data = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "ttl": ttl
        }
        return await self.set_cache(key, data, ttl)
    
    async def get_with_timestamp(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cache value with timestamp info"""
        return await self.get_cache(key)
    
    async def is_fresh(self, key: str, max_age_seconds: int) -> bool:
        """Check if cached data is fresh (within max age)"""
        try:
            data = await self.get_with_timestamp(key)
            if not data or "timestamp" not in data:
                return False
            
            cached_time = datetime.fromisoformat(data["timestamp"])
            age = (datetime.now() - cached_time).total_seconds()
            
            return age <= max_age_seconds
            
        except Exception as e:
            logger.error(f"Error checking freshness for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        try:
            if self.redis is None:
                await self.initialize()
            
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing pattern {pattern}: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.redis is None:
                await self.initialize()
            
            info = await self.redis.info()
            
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), 
                    info.get("keyspace_misses", 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def _get_default_ttl(self, key_type: str) -> int:
        """Get default TTL for cache key type"""
        ttl_mapping = {
            "index_data": self.settings.INDEX_DATA_CACHE_TTL,
            "options_chain": self.settings.OPTIONS_CHAIN_CACHE_TTL,
            "candle_data": self.settings.CANDLE_DATA_CACHE_TTL,
            "indicators": self.settings.INDICATORS_CACHE_TTL,
            "historical_data": self.settings.HISTORICAL_DATA_CACHE_TTL
        }
        return ttl_mapping.get(key_type, 300)  # Default 5 minutes
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions
async def cache_market_data(symbol: str, timeframe: str, data: Any, ttl: Optional[int] = None) -> bool:
    """Cache market data for symbol and timeframe"""
    key = get_cache_key("candle_data", symbol=symbol, timeframe=timeframe)
    return await cache_manager.set_with_timestamp(key, data, ttl or cache_manager.settings.CANDLE_DATA_CACHE_TTL)


async def get_cached_market_data(symbol: str, timeframe: str) -> Optional[Any]:
    """Get cached market data"""
    key = get_cache_key("candle_data", symbol=symbol, timeframe=timeframe)
    cached_data = await cache_manager.get_with_timestamp(key)
    return cached_data["value"] if cached_data else None


async def cache_options_chain(symbol: str, data: Any, ttl: Optional[int] = None) -> bool:
    """Cache options chain data"""
    key = get_cache_key("options_chain", symbol=symbol)
    return await cache_manager.set_with_timestamp(key, data, ttl or cache_manager.settings.OPTIONS_CHAIN_CACHE_TTL)


async def get_cached_options_chain(symbol: str) -> Optional[Any]:
    """Get cached options chain data"""
    key = get_cache_key("options_chain", symbol=symbol)
    cached_data = await cache_manager.get_with_timestamp(key)
    return cached_data["value"] if cached_data else None


async def cache_index_snapshot(symbol: str, data: Any, ttl: Optional[int] = None) -> bool:
    """Cache index snapshot data"""
    key = get_cache_key("index_snapshot", symbol=symbol)
    return await cache_manager.set_with_timestamp(key, data, ttl or cache_manager.settings.INDEX_DATA_CACHE_TTL)


async def get_cached_index_snapshot(symbol: str) -> Optional[Any]:
    """Get cached index snapshot"""
    key = get_cache_key("index_snapshot", symbol=symbol)
    cached_data = await cache_manager.get_with_timestamp(key)
    return cached_data["value"] if cached_data else None


async def health_check_redis() -> Dict[str, Any]:
    """Perform Redis health check"""
    try:
        redis = await get_redis_client()
        
        # Test basic operations
        test_key = "health_check_test"
        await redis.set(test_key, "test_value", ex=60)
        result = await redis.get(test_key)
        await redis.delete(test_key)
        
        if result != "test_value":
            return {"status": "unhealthy", "error": "Basic operations failed"}
        
        # Get cache stats
        stats = await cache_manager.get_cache_stats()
        
        return {
            "status": "healthy",
            "stats": stats
        }
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def close_redis_connections():
    """Close Redis connections"""
    global _redis_client
    
    try:
        if _redis_client:
            await _redis_client.close()
            _redis_client = None
        
        logger.info("Redis connections closed successfully")
        
    except Exception as e:
        logger.error(f"Error closing Redis connections: {e}")


# Initialize cache manager
async def init_cache():
    """Initialize cache manager"""
    try:
        await cache_manager.initialize()
        logger.info("Cache manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize cache manager: {e}")
        raise