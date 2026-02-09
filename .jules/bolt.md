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

## 2026-02-05 - Single-Pass Project Discovery and JSON Caching
**Learning:** Multiple independent recursive `glob` or `os.walk` calls in a project discovery system (like `GenericStacksAutoDetector`) lead to massive I/O redundancy. Consolidating these into a single-pass scan with pattern matching (`fnmatch`) drastically improves performance. Additionally, caching JSON parsing results with `mtime` validation prevents expensive re-parsing of static manifests.
**Action:** Always prefer a single `os.walk` that populates a project-wide file cache. Use this cache for all subsequent pattern matching instead of calling `glob` repeatedly. Implement `mtime`-aware JSON caching for frequently accessed configuration and manifest files.

## 2026-02-19 - GUI Data Refresh Optimization
**Learning:** Periodically refreshing a Textual TUI by clearing and repopulating DataTables causes visual flickering and redundant main-thread CPU usage. Even with cached API results, the DOM manipulation for clearing and re-adding dozens of rows is expensive.
**Action:** Always implement state tracking (e.g., `self._last_data`) and compare new data against the previous state before updating UI components. Move `table.clear()` to immediately precede the population logic to ensure the UI stays responsive and flickering is eliminated.

## 2026-02-07 - API Caching Latency in Polling Loops

**Learning:** I discovered that aggressive API caching (e.g., 5-minute expiry) in polling loops (like `wait_for_transaction`) and monitoring background tasks causes massive latency in status detection. A transaction that confirms in 10 seconds might not be detected for 300 seconds because the poller keeps hitting the stale cache.

**Action:** Always implement an explicit `bypass_cache` mechanism in caching decorators. Use `bypass_cache=True` for all critical polling operations and manual user refreshes to ensure immediate responsiveness, while maintaining cache benefits for non-critical background updates.

## 2026-02-08 - Optimized Project Discovery and Contract Hashing
**Learning:** Redundant filesystem operations and cryptographic hashing are major bottlenecks in project discovery. Consolidating all file metadata (`mtime`, `size`) into a single-pass `os.walk` scan and using that metadata to gate expensive `stat()` calls and `hashlib` operations significantly improves performance.
**Action:** Always prefer a single-pass scan that populates a comprehensive metadata cache. Use this cache to implement `mtime`-aware gating for any expensive per-file operations like content hashing or parsing.
