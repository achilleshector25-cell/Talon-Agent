"""TokenBucket + cache — fixes 10-100x burn"""
import time
from threading import RLock
from collections import OrderedDict

class TokenBucket:
    def __init__(self, daily_budget: int = 2_000_000, refill_rate: float = 23.14): # 2M/86400
        self.budget = daily_budget
        self.remaining = daily_budget
        self.refill_rate = refill_rate
        self.last = time.time()
        self.cache = OrderedDict()
        self.max_cache = 500
        self._lock = RLock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last
        self.remaining = min(self.budget, self.remaining + elapsed * self.refill_rate)
        self.last = now

    def consume(self, tokens: int) -> bool:
        with self._lock:
            self._refill()
            if self.remaining < tokens:
                return False
            self.remaining -= tokens
            return True

    def get_cached(self, key: str):
        with self._lock:
            value = self.cache.get(key)
            if value is not None:
                self.cache.move_to_end(key)
            return value

    def set_cached(self, key: str, val):
        with self._lock:
            if len(self.cache) >= self.max_cache:
                self.cache.popitem(last=False)
            self.cache[key] = val

    def estimate(self, text: str) -> int:
        return max(1, len(text)//4)
