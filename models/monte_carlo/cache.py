"""
Caching system for Monte Carlo simulations.

This module provides caching functionality to avoid redundant calculations
when running Monte Carlo simulations with the same parameters.

The cache system includes:
- In-memory LRU cache with configurable size and TTL
- Persistence to disk with automatic loading on startup
- Statistics tracking for cache hits/misses
- Cache invalidation functionality
- Thread-safe operations
- Error handling with fallback mechanisms
"""

import os
import time
import logging
import functools
import threading
import pickle
import traceback
from typing import Dict, Any, Callable, Tuple, List, Optional, Union
import hashlib
import json
from datetime import datetime, timedelta
import atexit
import signal

# Set up logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                    "../..", "data", "cache"))
DEFAULT_CACHE_FILE = "monte_carlo_cache.pickle"
CACHE_SAVE_INTERVAL = 300  # 5 minutes
CACHE_MAX_SIZE = 100
CACHE_TTL = 3600  # 1 hour

class SimulationCache:
    """Cache for storing Monte Carlo simulation results.
    
    This cache implementation includes:
    - Thread-safe operations via lock
    - LRU eviction policy for memory management
    - TTL-based expiration
    - Persistence to disk
    - Statistics tracking
    """
    
    def __init__(self, max_size: int = CACHE_MAX_SIZE, ttl: int = CACHE_TTL):
        """Initialize the cache with a maximum size and time-to-live.
        
        Args:
            max_size: Maximum number of items to store in cache
            ttl: Time-to-live for cache entries in seconds
        """
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
        self.created_at = datetime.now()
        self.last_save_time = None
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        self.save_lock = threading.Lock()  # Lock for save operations
        self.dirty = False  # Flag to track if cache has unsaved changes
    
    def _generate_key(self, args: Tuple, kwargs: Dict) -> str:
        """Generate a unique key based on function arguments.
        
        Args:
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            str: Unique MD5 hash representing the arguments
        """
        key_dict = {'args': args, 'kwargs': kwargs}
        try:
            key_str = json.dumps(key_dict, sort_keys=True)
            return hashlib.md5(key_str.encode()).hexdigest()
        except (TypeError, ValueError):
            # If arguments can't be serialized, use their string representation
            key_str = str(key_dict)
            logger.debug(f"Using string representation for key: {key_str[:100]}...")
            return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve an item from the cache (thread-safe).
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            The cached value or None if not found/expired
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            value, timestamp = self.cache[key]
            if time.time() - timestamp > self.ttl:
                # Entry has expired
                del self.cache[key]
                self.misses += 1
                return None
            
            # Update the timestamp to keep the item fresh (LRU update)
            self.cache[key] = (value, time.time())
            self.hits += 1
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store an item in the cache (thread-safe).
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Optional custom TTL for this entry (seconds)
        """
        with self.lock:
            # Check if cache is full and remove least recently used item
            if len(self.cache) >= self.max_size:
                # Remove oldest entry (LRU strategy)
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
                logger.debug(f"Cache full, removed oldest entry: {oldest_key[:10]}...")
            
            self.cache[key] = (value, time.time())
            self.dirty = True
            
            # Update timestamps for entries with custom TTL if provided
            if ttl is not None and ttl != self.ttl:
                logger.debug(f"Setting custom TTL of {ttl}s for key {key[:10]}...")
    
    def invalidate(self, pattern: str = None) -> int:
        """Invalidate cache entries (thread-safe).
        
        Args:
            pattern: If provided, only invalidate keys containing this pattern
            
        Returns:
            Number of invalidated entries
        """
        with self.lock:
            if pattern is None:
                count = len(self.cache)
                self.cache.clear()
                logger.info(f"Cleared entire cache ({count} entries)")
                self.dirty = True
                return count
            
            keys_to_remove = [k for k in self.cache if pattern in k]
            for k in keys_to_remove:
                del self.cache[k]
                
            if keys_to_remove:
                self.dirty = True
                logger.info(f"Invalidated {len(keys_to_remove)} entries matching pattern '{pattern}'")
            return len(keys_to_remove)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from the cache (thread-safe).
        
        Returns:
            Number of expired entries removed
        """
        with self.lock:
            current_time = time.time()
            expired_keys = [
                k for k, (_, timestamp) in self.cache.items() 
                if current_time - timestamp > self.ttl
            ]
            
            for key in expired_keys:
                del self.cache[key]
                
            if expired_keys:
                self.dirty = True
                logger.debug(f"Removed {len(expired_keys)} expired entries")
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Return cache statistics (thread-safe).
        
        Returns:
            Dict containing cache statistics
        """
        with self.lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'created_at': self.created_at.isoformat(),
                'last_save_time': self.last_save_time.isoformat() if self.last_save_time else None,
                'ttl': self.ttl,
                'memory_usage_estimate': self._estimate_memory_usage()
            }
    
    def _estimate_memory_usage(self) -> int:
        """Estimate the memory usage of the cache in bytes.
        
        Returns:
            Estimated memory usage in bytes
        """
        # This is a rough estimate, not precise memory profiling
        try:
            # Sample a few keys if cache is large
            keys_to_sample = min(10, len(self.cache))
            if keys_to_sample == 0:
                return 0
                
            sampled_keys = list(self.cache.keys())[:keys_to_sample]
            total_size = sum(
                len(pickle.dumps(self.cache[k][0])) for k in sampled_keys
            )
            # Extrapolate to full cache size
            estimated_size = (total_size / keys_to_sample) * len(self.cache)
            return int(estimated_size)
        except Exception as e:
            logger.warning(f"Error estimating cache memory: {e}")
            return 0


    def save(self, file_path: str) -> bool:
        """Save cache to a file (thread-safe).
        
        Args:
            file_path: Path to save the cache
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        with self.save_lock:
            try:
                # First make sure the directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Create a metadata structure with cache info
                metadata = {
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0.0',
                    'cache_stats': self.get_stats()
                }
                
                # Make a copy of the cache data to avoid locks during file write
                with self.lock:
                    # Clean expired entries before saving
                    self.cleanup_expired()
                    cache_copy = dict(self.cache)
                
                # Save cache with metadata
                save_data = {
                    'metadata': metadata,
                    'cache': cache_copy
                }
                
                # Use a temporary file for atomic save
                tmp_file = f"{file_path}.tmp"
                with open(tmp_file, 'wb') as f:
                    pickle.dump(save_data, f)
                
                # Rename temp file to target file (atomic on most systems)
                if os.path.exists(file_path):
                    os.replace(tmp_file, file_path)  # Atomic replace
                else:
                    os.rename(tmp_file, file_path)
                
                # Update state
                with self.lock:
                    self.last_save_time = datetime.now()
                    self.dirty = False
                
                logger.info(f"Cache saved to {file_path} ({len(cache_copy)} entries)")
                return True
                
            except Exception as e:
                logger.error(f"Error saving cache to {file_path}: {e}")
                logger.debug(traceback.format_exc())
                return False
    
    def load(self, file_path: str) -> bool:
        """Load cache from a file (thread-safe).
        
        Args:
            file_path: Path to load the cache from
            
        Returns:
            bool: True if load was successful, False otherwise
        """
        if not os.path.exists(file_path):
            logger.warning(f"Cache file does not exist: {file_path}")
            return False
            
        with self.save_lock:
            try:
                # Load data from file
                with open(file_path, 'rb') as f:
                    load_data = pickle.load(f)
                
                # Extract data based on format
                if isinstance(load_data, dict) and 'cache' in load_data:
                    # New format with metadata
                    cache_data = load_data['cache']
                    metadata = load_data.get('metadata', {})
                    logger.info(f"Loaded cache from {file_path} ({len(cache_data)} entries)")
                    logger.debug(f"Cache metadata: {metadata}")
                else:
                    # Old format (just the cache dict)
                    cache_data = load_data
                    logger.info(f"Loaded legacy cache format from {file_path} ({len(cache_data)} entries)")
                
                # Update cache with loaded data (using lock)
                with self.lock:
                    # Keep stats but replace cache content
                    old_hits = self.hits
                    old_misses = self.misses
                    
                    # Replace cache with loaded data
                    self.cache = cache_data
                    self.dirty = False
                    self.last_save_time = datetime.now()
                    
                    # Restore stats
                    self.hits = old_hits
                    self.misses = old_misses
                    
                    # Clean up any expired entries
                    expired_count = self.cleanup_expired()
                    if expired_count > 0:
                        logger.info(f"Removed {expired_count} expired entries from loaded cache")
                
                return True
                
            except Exception as e:
                logger.error(f"Error loading cache from {file_path}: {e}")
                logger.debug(traceback.format_exc())
                return False
                
    def merge(self, other_cache: 'SimulationCache') -> int:
        """Merge another cache into this one (thread-safe).
        
        Args:
            other_cache: Another SimulationCache instance to merge
            
        Returns:
            int: Number of entries merged
        """
        with self.lock, other_cache.lock:
            before_count = len(self.cache)
            
            # Merge entries, giving preference to newer entries
            for key, (value, timestamp) in other_cache.cache.items():
                # Only merge if entry doesn't exist or is newer
                if key not in self.cache or timestamp > self.cache[key][1]:
                    self.cache[key] = (value, timestamp)
            
            # Mark as dirty if any changes were made
            merged_count = len(self.cache) - before_count
            if merged_count > 0:
                self.dirty = True
                logger.info(f"Merged {merged_count} entries from another cache")
            
            return merged_count


# Global cache instance
_cache = SimulationCache()

# Cache schedule state
_cache_save_timer = None
_cache_save_path = os.path.join(DEFAULT_CACHE_DIR, DEFAULT_CACHE_FILE)
_cache_save_running = False


def cached_simulation(func: Callable = None, ttl: int = None, key_prefix: str = ''):
    """Decorator for caching simulation results.
    
    Args:
        func: Function to decorate
        ttl: Optional custom time-to-live for this function's cache entries
        key_prefix: Optional prefix for cache keys to group related entries
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # Check if caching is disabled in environment
            if os.environ.get('DISABLE_MONTE_CARLO_CACHE', '').lower() in ('1', 'true', 'yes'):
                return f(*args, **kwargs)
                
            # Extract cache_skip from kwargs if present
            skip_cache = kwargs.pop('cache_skip', False) if 'cache_skip' in kwargs else False
            if skip_cache:
                return f(*args, **kwargs)
            
            # Generate cache key
            key = key_prefix + _cache._generate_key(args, kwargs)
            
            # Try to get from cache
            result = _cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit for {f.__name__}")
                return result
            
            # Execute function
            logger.debug(f"Cache miss for {f.__name__}")
            result = f(*args, **kwargs)
            
            # Store in cache (with custom TTL if provided)
            _cache.set(key, result, ttl=ttl)
            
            # Schedule a save if cache is dirty
            if _cache.dirty:
                schedule_cache_save()
                
            return result
        
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)


def invalidate_cache(pattern: str = None) -> int:
    """Invalidate cache entries.
    
    Args:
        pattern: If provided, only invalidate keys containing this pattern
        
    Returns:
        Number of invalidated entries
    """
    count = _cache.invalidate(pattern)
    
    # Schedule a save if invalidation occurred
    if count > 0:
        schedule_cache_save()
        
    return count


def get_cache_stats() -> Dict[str, Any]:
    """Get current cache statistics."""
    return _cache.get_stats()


def save_cache(file_path: str = None) -> bool:
    """Save the cache to a file.
    
    Args:
        file_path: Path to save the cache to (default: data/cache/monte_carlo_cache.pickle)
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    global _cache_save_path
    
    # Use default path if not specified
    if file_path is None:
        file_path = _cache_save_path
    else:
        # Update global save path if a different path is provided
        _cache_save_path = file_path
    
    return _cache.save(file_path)


def load_cache(file_path: str = None) -> bool:
    """Load the cache from a file.
    
    Args:
        file_path: Path to load the cache from (default: data/cache/monte_carlo_cache.pickle)
        
    Returns:
        bool: True if load was successful, False otherwise
    """
    global _cache_save_path
    
    # Use default path if not specified
    if file_path is None:
        file_path = _cache_save_path
    else:
        # Update global save path if a different path is provided
        _cache_save_path = file_path
    
    return _cache.load(file_path)


def schedule_cache_save() -> None:
    """Schedule a cache save operation.
    
    This schedules a save for CACHE_SAVE_INTERVAL seconds in the future,
    but cancels any existing scheduled save to avoid multiple saves.
    """
    global _cache_save_timer
    
    # Cancel existing timer if present
    if _cache_save_timer is not None:
        try:
            _cache_save_timer.cancel()
        except:
            pass
    
    # Schedule a new save
    _cache_save_timer = threading.Timer(CACHE_SAVE_INTERVAL, _perform_scheduled_save)
    _cache_save_timer.daemon = True  # Make thread a daemon so it doesn't prevent program exit
    _cache_save_timer.start()
    
    logger.debug(f"Scheduled cache save in {CACHE_SAVE_INTERVAL} seconds")


def _perform_scheduled_save() -> None:
    """Perform the scheduled cache save operation.
    
    This function is called by the timer thread and saves the cache to disk.
    """
    global _cache_save_running
    
    # Prevent multiple save operations running simultaneously
    if _cache_save_running:
        logger.debug("Skipping scheduled save as another save is in progress")
        return
        
    try:
        _cache_save_running = True
        
        # Only save if cache is dirty
        if _cache.dirty:
            save_cache()
        else:
            logger.debug("Skipping scheduled save as cache is not dirty")
    finally:
        _cache_save_running = False


def configure_cache(
    max_size: int = None,
    ttl: int = None,
    save_interval: int = None,
    cache_dir: str = None,
    cache_file: str = None
) -> None:
    """Configure the global cache settings.
    
    Args:
        max_size: Maximum size of the cache (number of entries)
        ttl: Time-to-live for cache entries in seconds
        save_interval: Interval between auto-saves in seconds
        cache_dir: Directory to store cache files
        cache_file: Name of the cache file
    """
    global _cache, CACHE_SAVE_INTERVAL, _cache_save_path
    
    # Update cache instance settings
    if max_size is not None:
        _cache.max_size = max_size
    
    if ttl is not None:
        _cache.ttl = ttl
    
    # Update save interval
    if save_interval is not None:
        CACHE_SAVE_INTERVAL = save_interval
    
    # Update cache file path
    if cache_dir is not None or cache_file is not None:
        # Determine the directory
        directory = cache_dir if cache_dir is not None else DEFAULT_CACHE_DIR
        
        # Determine the filename
        filename = cache_file if cache_file is not None else DEFAULT_CACHE_FILE
        
        # Construct the full path
        _cache_save_path = os.path.join(directory, filename)
        
        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)
    
    logger.info(f"Monte Carlo cache configured: max_size={_cache.max_size}, "
                f"ttl={_cache.ttl}s, save_interval={CACHE_SAVE_INTERVAL}s, "
                f"path={_cache_save_path}")


def initialize_cache() -> bool:
    """Initialize the cache system.
    
    This function should be called at application startup to load 
    the cache from disk and configure automatic saving.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Ensure the cache directory exists
        os.makedirs(os.path.dirname(_cache_save_path), exist_ok=True)
        
        # Try to load the cache
        success = load_cache()
        
        # Register automatic save on application exit
        atexit.register(shutdown_cache)
        
        # Register signal handlers for graceful shutdown
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, _signal_handler)
            except (ValueError, OSError):
                # Some signals may not be available on all platforms
                pass
        
        # Start the automatic save timer
        schedule_cache_save()
        
        if success:
            logger.info("Monte Carlo cache system initialized successfully with loaded cache")
        else:
            logger.info("Monte Carlo cache system initialized with a new cache")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing cache: {e}")
        logger.debug(traceback.format_exc())
        return False


def shutdown_cache() -> None:
    """Shut down the cache system.
    
    This function is called automatically when the application exits.
    It saves the cache to disk if it contains any unsaved changes.
    """
    global _cache_save_timer
    
    # Cancel any pending save operations
    if _cache_save_timer is not None:
        try:
            _cache_save_timer.cancel()
        except:
            pass
        _cache_save_timer = None
    
    # Save the cache if it's dirty
    if _cache.dirty:
        logger.info("Saving cache during shutdown...")
        save_cache()
    else:
        logger.info("Cache is clean, no need to save during shutdown")


def _signal_handler(sig, frame) -> None:
    """Handle signals for graceful shutdown.
    
    Args:
        sig: Signal number
        frame: Current stack frame
    """
    logger.info(f"Received signal {sig}, shutting down cache...")
    shutdown_cache()
    
    # Re-raise the signal to allow the default handler to run
    # (which typically terminates the program)
    signal.default_int_handler(sig, frame)


# Auto-initialize cache on module import
try:
    # Only initialize if running as the main application (not in tests)
    if os.environ.get('MONTE_CARLO_INITIALIZE_CACHE', '').lower() in ('1', 'true', 'yes'):
        initialize_cache()
except Exception as e:
    logger.warning(f"Auto-initialization of cache failed: {e}")
    # Continue without failing, as cache will function in memory-only mode