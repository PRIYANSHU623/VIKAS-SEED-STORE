import time
import threading
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class SimpleCache:
    def __init__(self, name: str):
        self.name = name
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                logger.info(f"[CACHE MISS] {self.name} cache miss for key: {key[:50]}...")
                return None
            val, expiry = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                self.misses += 1
                logger.info(f"[CACHE MISS/EXPIRED] {self.name} cache expired for key: {key[:50]}...")
                return None
            self.hits += 1
            logger.info(f"[CACHE HIT] {self.name} cache hit for key: {key[:50]}...")
            return val

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        with self._lock:
            self._cache[key] = (value, time.time() + ttl_seconds)
            logger.info(f"[CACHE SET] {self.name} cache set for key: {key[:50]}... TTL: {ttl_seconds}s")

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0
            logger.info(f"[CACHE CLEAR] {self.name} cache cleared.")

# Define global cache instances with their respective TTLs
planner_cache = SimpleCache("Planner")
response_cache = SimpleCache("Response")
knowledge_cache = SimpleCache("Knowledge")
product_cache = SimpleCache("Product")
weather_cache = SimpleCache("Weather")
recommendation_cache = SimpleCache("Recommendation")

def get_stats() -> Dict[str, Any]:
    return {
        "planner": {"hits": planner_cache.hits, "misses": planner_cache.misses},
        "response": {"hits": response_cache.hits, "misses": response_cache.misses},
        "knowledge": {"hits": knowledge_cache.hits, "misses": knowledge_cache.misses},
        "product": {"hits": product_cache.hits, "misses": product_cache.misses},
        "weather": {"hits": weather_cache.hits, "misses": weather_cache.misses},
        "recommendation": {"hits": recommendation_cache.hits, "misses": recommendation_cache.misses},
    }
