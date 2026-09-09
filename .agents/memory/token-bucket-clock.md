---
name: Token bucket clock source
description: Runtime rate-limit refill calculations must use one consistent monotonic clock.
---

Use `time.monotonic()` for both the initial timestamp and every refill calculation; never mix it with wall-clock `time.time()`.

**Why:** Mixing clock domains can make elapsed time a huge negative value, causing a fresh process to report an exhausted or negative token balance.

**How to apply:** When changing rate limits, budgets, leases, or TTL-like in-process state, verify the clock source at initialization and update sites together.