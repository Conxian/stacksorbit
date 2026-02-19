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

## 2026-02-23 - Parallelization of I/O Bound Verification Checks
**Learning:** Sequential network calls for deployment verification (e.g., API status, account info, contract interface) create significant latency that scales linearly with the number of checks. Parallelizing these I/O-bound operations using `ThreadPoolExecutor` can reduce total latency from $O(\sum latency)$ to $O(\max latency)$, achieving over 70% reduction in verification time.
**Action:** Always identify independent, network-bound or I/O-bound loops and parallelize them using `ThreadPoolExecutor`. When doing so, implement a `threading.Lock` and a `_safe_print` wrapper to ensure CLI output remains readable and non-interleaved.

## 2026-02-21 - Optimization of Core Utilities and Verification Flow

**Learning:** High-frequency utility functions (like `is_sensitive_key` or `validate_stacks_address`) can become significant bottlenecks when called in recursive processes (like config redaction) or UI event loops. Additionally, direct usage of `requests.get` bypassing available service-level caches (like in `DeploymentMonitor`) leads to redundant network I/O and slower verification cycles.

**Action:** Always use `@functools.lru_cache` and $O(1)$ data structures (sets/dicts) for high-frequency utility functions. When working with external APIs, check for existing service classes that implement caching before making direct network calls. Hoist expensive calls (like `datetime.now(timezone.utc)`) out of loops to minimize redundant system calls and ensure consistency.

## 2026-02-11 - Lifecycle and I/O Performance Consolidation

**Learning:** I identified three high-frequency performance bottlenecks: 1) Redundant synchronous disk I/O in inner loops (contract hashing and API polling), 2) Algorithmic (N^2)$ complexity in verification lookups, and 3) Expensive redundant subprocess calls for tool version checking. These patterns are particularly impactful in Textual TUIs where background workers run frequently.

**Action:** 1) Always batch disk writes to the end of a high-level operation or only trigger them on data change. 2) Prefer sets for (1)$ lookups when comparing large lists (e.g., expected vs. deployed contracts). 3) Implement process-wide or global caches for static information like external tool versions to avoid the overhead of spawning multiple subprocesses.

## 2026-03-01 - Optimized Project Scanning and Secret Detection
**Learning:** Replacing `os.walk` and `pathlib.Path` with a recursive `os.scandir` implementation significantly reduces overhead in project discovery by leveraging cached `DirEntry` stat information and avoiding slow object instantiation. Additionally, using a pre-compiled regex for multi-substring secret detection (`is_sensitive_key`) is faster than iterative `any()` checks in high-frequency validation loops.
**Action:** Always prefer `os.scandir` for recursive filesystem traversals where performance is critical. Use pre-compiled regular expressions for multi-pattern matching in hot paths.

## 2026-03-05 - Regex-Optimized Pattern Matching and Categorization

**Learning:** Iterative pattern matching using `fnmatch.fnmatch` in a loop and linear string searches for categorization/sorting are significant bottlenecks in project discovery, especially as the number of files and contracts grows. Replacing these loops with pre-compiled, consolidated regular expressions (using `re.IGNORECASE` for cross-platform consistency) can provide a ~2.5x speedup in pattern matching operations. Additionally, increasing the file hashing chunk size from 4KB to 64KB improves throughput on modern I/O systems.

**Action:** Always pre-compile consolidated regexes for multiple glob patterns or string keywords in hot paths like filesystem scanners and categorizers. Use memoization for expensive per-item calculations like contract priority to ensure the logic runs only once per unique identifier.

## 2026-03-10 - Regex-Optimized Multi-Network Address Validation

**Learning:** Stacks address validation () that involves multiple steps (strip, upper, length check, prefix check, and body regex) can be significantly improved by using a mapping of pre-compiled, network-aware regexes. These regexes can combine prefix, length (26-39 chars for body), and charset (C32) validation into a single  pass. This achieved a ~35% speedup in benchmarks and reduced UI latency during high-frequency typing events. Additionally, redundant placeholder checks in utilities (like ) are unnecessary if they are already caught by strict format/length checks.

**Action:** Always prefer a single regex match over multiple sequential string checks (prefix, length, charset) in high-frequency validation functions. Use a dictionary mapping to select specialized regexes for different modes (e.g., networks) to maintain O(1) performance.

## 2026-03-10 - Regex-Optimized Multi-Network Address Validation

**Learning:** Stacks address validation (`validate_stacks_address`) that involves multiple steps (strip, upper, length check, prefix check, and body regex) can be significantly improved by using a mapping of pre-compiled, network-aware regexes. These regexes can combine prefix, length (26-39 chars for body), and charset (C32) validation into a single `match()` pass. This achieved a ~35% speedup in benchmarks and reduced UI latency during high-frequency typing events. Additionally, redundant placeholder checks in utilities (like `validate_private_key`) are unnecessary if they are already caught by strict format/length checks.

**Action:** Always prefer a single regex match over multiple sequential string checks (prefix, length, charset) in high-frequency validation functions. Use a dictionary mapping to select specialized regexes for different modes (e.g., networks) to maintain O(1) performance.
