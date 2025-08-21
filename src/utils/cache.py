"""
Caching utilities for improving performance of repeated calculations and file loading.
Provides decorators and utilities for result caching with configurable TTL and size limits.
"""

import hashlib
import json
import pickle
import time
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
import os

from .exceptions import CalculationError


class CacheStatistics:
    """Track cache performance metrics"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_time_saved = 0.0
        self.start_time = time.time()
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def runtime(self) -> float:
        """Get total runtime since cache creation"""
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': f"{self.hit_rate:.1%}",
            'time_saved': f"{self.total_time_saved:.2f}s",
            'runtime': f"{self.runtime:.2f}s"
        }
    
    def __str__(self) -> str:
        """String representation of cache statistics"""
        return (f"Cache Stats: {self.hits} hits, {self.misses} misses "
                f"({self.hit_rate:.1%} hit rate), {self.total_time_saved:.2f}s saved")


# Global cache statistics
_cache_stats = CacheStatistics()


def get_cache_statistics() -> CacheStatistics:
    """Get global cache statistics"""
    return _cache_stats


def reset_cache_statistics():
    """Reset global cache statistics"""
    global _cache_stats
    _cache_stats = CacheStatistics()


def cache_key_from_dict(data: Dict[str, Any]) -> str:
    """
    Generate a stable cache key from a dictionary.
    
    Args:
        data: Dictionary to generate key from
        
    Returns:
        Hexadecimal cache key string
    """
    # Sort keys for stability
    sorted_data = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(sorted_data.encode()).hexdigest()[:16]


def cache_key_from_args(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Hexadecimal cache key string
    """
    key_data = {
        'args': args,
        'kwargs': kwargs
    }
    return cache_key_from_dict(key_data)


class ResultCache:
    """
    File-based result cache for expensive computations.
    Stores results in a temporary directory with automatic cleanup.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_seconds: int = 3600):
        """
        Initialize result cache.
        
        Args:
            cache_dir: Directory for cache storage (default: temp directory)
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        if cache_dir is None:
            cache_dir = Path.home() / '.ai_impact_cache'
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self._cleanup_old_entries()
    
    def _cleanup_old_entries(self):
        """Remove expired cache entries"""
        current_time = time.time()
        for cache_file in self.cache_dir.glob('*.cache'):
            try:
                if current_time - cache_file.stat().st_mtime > self.ttl_seconds:
                    cache_file.unlink()
                    _cache_stats.evictions += 1
            except OSError:
                pass  # File might have been deleted by another process
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        cache_file = self.cache_dir / f"{key}.cache"
        
        if not cache_file.exists():
            return None
        
        # Check if expired
        if time.time() - cache_file.stat().st_mtime > self.ttl_seconds:
            cache_file.unlink()
            _cache_stats.evictions += 1
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except (pickle.PickleError, EOFError):
            # Corrupted cache file
            cache_file.unlink()
            return None
    
    def set(self, key: str, value: Any):
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        cache_file = self.cache_dir / f"{key}.cache"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
        except (pickle.PickleError, OSError) as e:
            # Log error but don't fail
            print(f"Warning: Failed to cache result: {e}")
    
    def clear(self):
        """Clear all cache entries"""
        for cache_file in self.cache_dir.glob('*.cache'):
            try:
                cache_file.unlink()
            except OSError:
                pass


# Global result cache instance
_result_cache = ResultCache()


def cached_result(ttl_seconds: int = 3600):
    """
    Decorator for caching function results to disk.
    
    Args:
        ttl_seconds: Time-to-live for cached results
        
    Returns:
        Decorated function with result caching
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__module__}.{func.__name__}_{cache_key_from_args(*args, **kwargs)}"
            
            # Check cache
            start_time = time.time()
            cached_value = _result_cache.get(cache_key)
            
            if cached_value is not None:
                _cache_stats.hits += 1
                _cache_stats.total_time_saved += time.time() - start_time
                return cached_value
            
            # Cache miss - compute result
            _cache_stats.misses += 1
            result = func(*args, **kwargs)
            
            # Store in cache
            _result_cache.set(cache_key, result)
            
            return result
        
        # Add cache control methods
        wrapper.cache_clear = lambda: _result_cache.clear()
        wrapper.cache_info = lambda: _cache_stats.to_dict()
        
        return wrapper
    return decorator


def memoized_method(maxsize: int = 128):
    """
    Decorator for memoizing class methods.
    Properly handles 'self' parameter.
    
    Args:
        maxsize: Maximum cache size
        
    Returns:
        Decorated method with memoization
    """
    def decorator(method: Callable) -> Callable:
        # Create a separate cache for each instance
        cache_attr = f'_memoized_cache_{method.__name__}'
        
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            # Get or create cache for this instance
            if not hasattr(self, cache_attr):
                setattr(self, cache_attr, {})
            
            cache = getattr(self, cache_attr)
            
            # Generate cache key
            cache_key = cache_key_from_args(*args, **kwargs)
            
            # Check cache
            if cache_key in cache:
                _cache_stats.hits += 1
                return cache[cache_key]
            
            # Compute and cache result
            _cache_stats.misses += 1
            result = method(self, *args, **kwargs)
            
            # Limit cache size
            if len(cache) >= maxsize:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(cache))
                del cache[oldest_key]
                _cache_stats.evictions += 1
            
            cache[cache_key] = result
            return result
        
        # Add cache control method
        def clear_cache(self):
            if hasattr(self, cache_attr):
                delattr(self, cache_attr)
        
        wrapper.cache_clear = clear_cache
        
        return wrapper
    return decorator


def conditional_cache(condition_func: Callable[[Any], bool]):
    """
    Decorator that only caches results when condition is met.
    
    Args:
        condition_func: Function that takes result and returns True if should cache
        
    Returns:
        Decorated function with conditional caching
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_key_from_args(*args, **kwargs)
            
            # Check cache
            if cache_key in cache:
                _cache_stats.hits += 1
                return cache[cache_key]
            
            # Compute result
            _cache_stats.misses += 1
            result = func(*args, **kwargs)
            
            # Cache if condition met
            if condition_func(result):
                cache[cache_key] = result
            
            return result
        
        wrapper.cache_clear = cache.clear
        wrapper.cache_info = lambda: {'size': len(cache), **_cache_stats.to_dict()}
        
        return wrapper
    return decorator


# Environment variable to disable caching
CACHE_ENABLED = os.environ.get('AI_IMPACT_CACHE_ENABLED', 'true').lower() == 'true'


def smart_cache(func: Callable) -> Callable:
    """
    Smart caching decorator that respects environment settings.
    
    Args:
        func: Function to wrap
        
    Returns:
        Cached or uncached function based on settings
    """
    if CACHE_ENABLED:
        return lru_cache(maxsize=128)(func)
    return func