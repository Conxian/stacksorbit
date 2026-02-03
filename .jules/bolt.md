# Bolt's Journal ⚡

## 2024-09-06 - Uncached API Calls in Polling Loops

**Learning:** I discovered a critical performance anti-pattern in `deployment_monitor.py`. The `wait_for_transaction` function repeatedly polls the `get_transaction_info` method without caching. This results in numerous redundant network requests for the same transaction ID, increasing latency, wasting bandwidth, and putting unnecessary load on the external Hiro API.

**Action:** When optimizing in this codebase, I must always inspect methods involved in loops or frequent UI updates for missing caching. The project already has a `@cache_api_call` decorator, which is the preferred, idiomatic solution. My first step for any performance task should be to scan for and apply this decorator to any uncached, idempotent API-bound functions.

## 2025-01-31 - CLI Startup Latency and Lazy Imports

**Learning:** Heavy dependencies like `textual` and `psutil`, along with immediate initialization of complex objects (like `DeploymentMonitor`) in the CLI entry point, can significantly increase startup latency (e.g., from ~0.3s to ~1.3s). This makes even simple commands like `--help` feel sluggish.

**Action:** Always move heavy module imports inside the methods or classes that require them. Use lazy initialization (e.g., Python `@property`) for shared service objects in CLI classes to avoid unnecessary overhead for commands that don't use those services.

## 2025-02-14 - Redundant Directory Scans and Pruning

**Learning:** Recursive directory scans (e.g., `glob("**/*.clar")` or `os.walk`) can be extremely slow and memory-intensive if they traverse heavy directories like `node_modules`, `.git`, or build artifacts. Performing multiple independent scans for different file patterns or project structures also leads to redundant I/O and CPU work.

**Action:** Consolidate multiple recursive scans into a single, efficient pass using `os.walk`. Always prune irrelevant or heavy directories by modifying the `dirs` list in-place (`dirs[:] = [...]`) within the walk loop. This ensures the scanner never even enters those directories, providing a massive performance boost for projects with many dependencies.
