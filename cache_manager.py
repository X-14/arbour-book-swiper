# cache_manager.py
"""
Simple in-memory cache to reduce Firebase Firestore reads.
Caches user data, preferences, and friends data with TTL (time-to-live).
"""

from datetime import datetime, timedelta
from threading import Lock

class CacheManager:
    def __init__(self):
        self.cache = {}
        self.lock = Lock()
        self.default_ttl = 300  # 5 minutes default TTL
    
    def get(self, key):
        """Get value from cache if not expired."""
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if datetime.now() < expiry:
                    return value
                else:
                    # Expired, remove it
                    del self.cache[key]
            return None
    
    def set(self, key, value, ttl=None):
        """Set value in cache with TTL in seconds."""
        if ttl is None:
            ttl = self.default_ttl
        
        with self.lock:
            expiry = datetime.now() + timedelta(seconds=ttl)
            self.cache[key] = (value, expiry)
    
    def delete(self, key):
        """Delete a specific key from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear_user_cache(self, user_id):
        """Clear all cache entries for a specific user."""
        with self.lock:
            keys_to_delete = [k for k in self.cache.keys() if k.startswith(f"user:{user_id}:")]
            for key in keys_to_delete:
                del self.cache[key]
    
    def clear_all(self):
        """Clear entire cache."""
        with self.lock:
            self.cache.clear()
    
    def cleanup_expired(self):
        """Remove all expired entries."""
        with self.lock:
            now = datetime.now()
            expired_keys = [k for k, (_, expiry) in self.cache.items() if now >= expiry]
            for key in expired_keys:
                del self.cache[key]

# Global cache instance
cache = CacheManager()
