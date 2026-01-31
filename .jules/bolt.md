# Bolt's Journal ⚡

## 2024-09-06 - Uncached API Calls in Polling Loops

**Learning:** I discovered a critical performance anti-pattern in `deployment_monitor.py`. The `wait_for_transaction` function repeatedly polls the `get_transaction_info` method without caching. This results in numerous redundant network requests for the same transaction ID, increasing latency, wasting bandwidth, and putting unnecessary load on the external Hiro API.

**Action:** When optimizing in this codebase, I must always inspect methods involved in loops or frequent UI updates for missing caching. The project already has a `@cache_api_call` decorator, which is the preferred, idiomatic solution. My first step for any performance task should be to scan for and apply this decorator to any uncached, idempotent API-bound functions.

## 2026-01-31 - Lazy Loading for CLI Startup Optimization
**Learning:** Top-level imports of heavy libraries (like `textual`, `rich`, and `psutil`) can significantly increase CLI startup time, even for commands that don't use those libraries.
**Action:** Move heavy imports inside the methods that use them and refactor shared objects (like `DeploymentMonitor`) to use lazy initialization (e.g., via a `@property`) to minimize overhead for simple commands.
