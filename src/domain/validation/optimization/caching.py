"""
Caching system for validation performance optimization.

Provides intelligent caching of validation results, rules, and
frequently accessed data to improve performance.
"""

import hashlib
import pickle
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from ..rules.base_rules import ValidationResult


@dataclass
class CacheConfig:
    """Configuration for validation caching."""

    max_cache_size: int = 10000  # Maximum number of cached items
    ttl_seconds: int = 3600  # Time to live for cache entries (1 hour)
    enable_persistence: bool = True
    cache_dir: Optional[Path] = None
    compression_enabled: bool = False
    memory_limit_mb: int = 100  # Memory limit for cache


class ValidationCache:
    """
    Intelligent caching system for validation results.

    Caches validation results, rule evaluations, and frequently accessed
    data to improve performance and reduce redundant computations.
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()

        # In-memory cache storage
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, datetime] = {}
        self._hit_counts: Dict[str, int] = {}

        # Cache statistics
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "size": 0}

        # Load persistent cache if enabled
        if self.config.enable_persistence:
            self._load_persistent_cache()

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve an item from the cache.

        Args:
            key: Cache key

        Returns:
            Cached item or None if not found
        """
        if key in self._cache:
            # Check TTL
            if self._is_expired(key):
                self._remove_entry(key)
                self.stats["misses"] += 1
                return None

            # Update access time and hit count
            self._access_times[key] = datetime.now()
            self._hit_counts[key] = self._hit_counts.get(key, 0) + 1
            self.stats["hits"] += 1

            return self._cache[key]["value"]

        self.stats["misses"] += 1
        return None

    def put(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None):
        """
        Store an item in the cache.

        Args:
            key: Cache key
            value: Item to cache
            metadata: Optional metadata
        """
        # Check cache size limit
        if len(self._cache) >= self.config.max_cache_size:
            self._evict_entries()

        # Calculate item size (rough estimate)
        item_size = self._estimate_size(value)
        if self._would_exceed_memory_limit(item_size):
            return  # Don't cache if it would exceed memory limit

        # Store item
        self._cache[key] = {
            "value": value,
            "metadata": metadata or {},
            "created_at": datetime.now(),
            "size": item_size,
        }

        self._access_times[key] = datetime.now()
        self.stats["size"] += item_size

    def invalidate(self, key: str):
        """Remove an item from the cache."""
        if key in self._cache:
            item_size = self._cache[key]["size"]
            self.stats["size"] -= item_size
            self._remove_entry(key)

    def invalidate_pattern(self, pattern: str):
        """Remove all items matching a pattern."""
        keys_to_remove = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_remove:
            self.invalidate(key)

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._access_times.clear()
        self._hit_counts.clear()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "size": 0}

    def get_or_compute(
        self,
        key: str,
        compute_func: Callable[[], Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Get cached value or compute and cache it.

        Args:
            key: Cache key
            compute_func: Function to compute value if not cached
            metadata: Optional metadata for cached item

        Returns:
            Cached or computed value
        """
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value

        # Compute value
        value = compute_func()

        # Cache the result
        self.put(key, value, metadata)

        return value

    def get_cache_key(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        rule_selection: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a cache key for validation operations.

        Args:
            entity_type: Type of entity
            entity_data: Entity data
            rule_selection: Optional selected rules

        Returns:
            Cache key string
        """
        # Create a deterministic key based on entity content
        key_components = [
            entity_type,
            str(sorted(entity_data.items())),  # Sort for consistency
            str(sorted(rule_selection or [])),
        ]

        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()

    def cache_validation_result(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        result: ValidationResult,
        rule_selection: Optional[List[str]] = None,
    ):
        """
        Cache a validation result.

        Args:
            entity_type: Type of entity
            entity_data: Entity data
            result: Validation result
            rule_selection: Optional selected rules
        """
        key = self.get_cache_key(entity_type, entity_data, rule_selection)
        metadata = {
            "entity_type": entity_type,
            "rule_selection": rule_selection,
            "quality_score": result.score,
            "issue_count": len(result.issues),
            "cached_at": datetime.now(),
        }

        self.put(key, result, metadata)

    def get_cached_validation_result(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        rule_selection: Optional[List[str]] = None,
    ) -> Optional[ValidationResult]:
        """
        Get a cached validation result.

        Args:
            entity_type: Type of entity
            entity_data: Entity data
            rule_selection: Optional selected rules

        Returns:
            Cached ValidationResult or None
        """
        key = self.get_cache_key(entity_type, entity_data, rule_selection)
        return self.get(key)

    def _is_expired(self, key: str) -> bool:
        """Check if a cache entry is expired."""
        if key not in self._cache:
            return True

        created_at = self._cache[key]["created_at"]
        ttl = timedelta(seconds=self.config.ttl_seconds)

        return datetime.now() - created_at > ttl

    def _remove_entry(self, key: str):
        """Remove a cache entry."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_times:
            del self._access_times[key]
        if key in self._hit_counts:
            del self._hit_counts[key]

    def _evict_entries(self):
        """Evict entries to free up space using LRU strategy."""
        if not self._access_times:
            return

        # Find least recently used entries
        sorted_keys = sorted(
            self._access_times.keys(), key=lambda k: self._access_times[k]
        )

        # Remove oldest entries until we're under the limit
        keys_to_remove = sorted_keys[
            : max(1, len(sorted_keys) - self.config.max_cache_size + 100)
        ]

        for key in keys_to_remove:
            self.stats["evictions"] += 1
            self.invalidate(key)

    def _estimate_size(self, obj: Any) -> int:
        """Estimate the memory size of an object in bytes."""
        try:
            # Use pickle to estimate size
            return len(pickle.dumps(obj))
        except Exception:
            # Fallback: rough estimate based on type
            if isinstance(obj, dict):
                return sum(self._estimate_size(v) for v in obj.values()) + len(obj) * 50
            elif isinstance(obj, list):
                return sum(self._estimate_size(item) for item in obj) + len(obj) * 20
            elif isinstance(obj, str):
                return len(obj) * 2  # UTF-8 estimate
            else:
                return 100  # Default estimate

    def _would_exceed_memory_limit(self, item_size: int) -> bool:
        """Check if adding an item would exceed memory limit."""
        return (
            self.stats["size"] + item_size > self.config.memory_limit_mb * 1024 * 1024
        )

    def _load_persistent_cache(self):
        """Load cache from persistent storage."""
        if not self.config.cache_dir:
            self.config.cache_dir = Path.home() / ".med13_cache"

        cache_file = self.config.cache_dir / "validation_cache.pkl"

        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    persistent_data = pickle.load(f)

                # Restore cache data (with TTL check)
                for key, data in persistent_data.get("cache", {}).items():
                    if not self._is_expired(key):
                        self._cache[key] = data
                        self.stats["size"] += data.get("size", 0)

            except Exception as e:
                print(f"Failed to load persistent cache: {e}")

    def save_persistent_cache(self):
        """Save cache to persistent storage."""
        if not self.config.enable_persistence or not self.config.cache_dir:
            return

        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.config.cache_dir / "validation_cache.pkl"

        try:
            persistent_data = {
                "cache": self._cache,
                "stats": self.stats,
                "saved_at": datetime.now(),
            }

            with open(cache_file, "wb") as f:
                pickle.dump(persistent_data, f)

        except Exception as e:
            print(f"Failed to save persistent cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "total_entries": len(self._cache),
            "total_size_bytes": self.stats["size"],
            "total_size_mb": self.stats["size"] / (1024 * 1024),
            "hit_rate": hit_rate,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "memory_limit_mb": self.config.memory_limit_mb,
            "memory_usage_percent": (
                self.stats["size"] / (self.config.memory_limit_mb * 1024 * 1024)
            )
            * 100,
            "ttl_seconds": self.config.ttl_seconds,
            "persistence_enabled": self.config.enable_persistence,
        }

    def get_most_accessed(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most frequently accessed cache entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of most accessed entries with metadata
        """
        # Sort by hit count
        sorted_entries = sorted(
            [
                (k, self._hit_counts.get(k, 0), self._access_times.get(k))
                for k in self._cache.keys()
            ],
            key=lambda x: x[1],
            reverse=True,
        )

        result = []
        for key, hits, last_access in sorted_entries[:limit]:
            cache_entry = self._cache[key]
            result.append(
                {
                    "key": key,
                    "hits": hits,
                    "last_access": last_access,
                    "size": cache_entry.get("size", 0),
                    "created_at": cache_entry.get("created_at"),
                    "metadata": cache_entry.get("metadata", {}),
                }
            )

        return result

    def optimize_cache(self):
        """Optimize cache by removing expired entries and compacting."""
        # Remove expired entries
        expired_keys = [k for k in self._cache.keys() if self._is_expired(k)]
        for key in expired_keys:
            self.invalidate(key)

        # Remove least recently used entries if still over limit
        while len(self._cache) > self.config.max_cache_size * 0.9:  # Keep 90% capacity
            self._evict_entries()

        # Save persistent cache
        if self.config.enable_persistence:
            self.save_persistent_cache()

    def preload_frequent_patterns(self, patterns: List[Dict[str, Any]]):
        """
        Preload frequently used validation patterns.

        Args:
            patterns: List of pattern definitions with entity data
        """
        for pattern in patterns:
            entity_type = pattern.get("entity_type", "unknown")
            entity_data = pattern.get("entity_data", {})
            rule_selection = pattern.get("rule_selection")

            # Generate key and check if already cached
            key = self.get_cache_key(entity_type, entity_data, rule_selection)
            if key not in self._cache:
                # Pre-compute and cache
                # Note: This would need the actual rule engine to compute results
                pass
