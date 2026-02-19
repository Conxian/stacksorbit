## 2024-05-20 - Prioritize Environment Variables for Secrets
**Vulnerability:** The application was loading the `DEPLOYER_PRIVKEY` from a plaintext `.env` file, creating a risk of secret exposure.
**Learning:** The previous security fix attempted to guide users to use environment variables but didn't enforce it in the code. This created a situation where the application would still read the secret from the `.env` file, undermining the security advice.
**Prevention:** When implementing security controls, ensure they are enforced programmatically. For secret management, always prioritize loading secrets from environment variables and provide clear, actionable warnings if insecure configurations are detected.

## 2025-01-31 - Prevent Secret Exposure in TUI Settings
**Vulnerability:** The Textual TUI was allowing users to save sensitive private keys to a plaintext `.env` file, which contradicts the application's security policy and creates a risk of secret exposure.
**Learning:** Even when security policies are enforced in the backend (e.g., in configuration loaders), TUI components must be explicitly updated to respect these policies and prevent users from inadvertently creating insecure configurations. Additionally, accessing TUI widgets from background threads during IO operations is a thread-safety risk.
**Prevention:** Always filter out known secret keys before writing configuration to disk. Collect sensitive data in the main thread before starting background operations. Use clear, prominent notifications to guide users toward secure practices like using environment variables.
## 2026-02-01 - Secure Secret Persistence and Error Masking
**Vulnerability:** Secrets loaded from environment variables were being inadvertently saved to the plaintext `.env` file when updating configuration (e.g., via templates). Additionally, verbose exception messages were leaking internal details in non-verbose CLI output.
**Learning:** Preventing secret loading from disk is not enough; saving operations must also be explicitly filtered to maintain a secure state. Centralizing error handling or following a consistent masking pattern is crucial for preventing information disclosure.
**Prevention:** Always use a block-list (like `SECRET_KEYS`) in all configuration saving methods. Ensure that top-level exception handlers in CLI tools default to generic error messages, only revealing details when a `--verbose` flag is explicitly provided.

## 2026-02-02 - Centralized Secret Detection and Robust Address Validation
**Vulnerability:** Inconsistent secret filtering and weak address validation across different parts of the application. Specifically, the TUI was missing pattern-based secret filtering (e.g., for keys containing 'TOKEN'), and the CLI used a naive address validation that allowed invalid characters and ignored network prefixes.
**Learning:** Security logic (like secret identification and input validation) must be centralized and reused across all interfaces (CLI, GUI, API) to prevent "implementation drift" where one interface becomes less secure than others.
**Prevention:** Maintain a single source of truth for security-sensitive logic and constants (e.g., in `stacksorbit_secrets.py`). Prefer shared utility functions (`is_sensitive_key`, `validate_address`) over local re-implementations.

## 2026-02-03 - Local Server Hardening and Centralized Validation
**Vulnerability:** A local HTTP server for wallet connection was unauthenticated, allowing unauthorized processes or websites to spoof wallet connections. Additionally, address validation was inconsistent and missing in some interfaces.
**Learning:** Local development servers must still implement basic authentication (e.g., via session tokens in the URL) to prevent spoofing. Centralizing input validation ensures consistent security enforcement across CLI, GUI, and API interfaces.
**Prevention:** Always use a session token for local servers that perform sensitive actions. Maintain a single source of truth for validation logic and reuse it everywhere.

## 2026-02-04 - Standardized Secret Detection in Configuration Loaders
**Vulnerability:** Inconsistent and incomplete secret detection in configuration loaders across the codebase. Some loaders used a hardcoded list of secrets, missing pattern-matched secrets (e.g., keys containing 'PASSWORD' or 'TOKEN'), while others performed no secret checks at all when loading from disk.
**Learning:** Implementation drift in security logic (like secret detection) can create holes where one interface is less secure than others. Pattern-based detection (e.g., `is_sensitive_key`) is more robust than hardcoded lists and should be enforced across all data entry points.
**Prevention:** Always use the centralized `is_sensitive_key(key)` utility for all configuration loading and saving operations. Ensure that all loaders consistently reject non-placeholder sensitive values in plaintext files like `.env`.

## 2026-02-05 - Local Server Hardening and Defensive Persistence
**Vulnerability:** The local wallet connection server was leaking the session token via the `Referer` header to external APIs (e.g., Hiro API). Additionally, the `save_wallet_address` function lacked secret filtering, potentially preserving plaintext secrets in `.env` files.
**Learning:** Local development servers with session tokens in the URL must explicitly set `Referrer-Policy: no-referrer` to prevent token leakage to 3rd-party APIs. Furthermore, every function that writes to configuration files must enforce the project's "no-secrets-in-plaintext" policy to maintain a consistent security posture.
**Prevention:** Use restrictive security headers (`Referrer-Policy`, `X-Frame-Options`) on all local servers. Standardize all configuration-saving logic to utilize centralized secret detection (e.g., `is_sensitive_key`) for automatic cleanup of sensitive data.

## 2026-02-06 - Context Loss in Recursive Redaction
**Vulnerability:** The `redact_recursive` function failed to redact sensitive values when they were contained within lists. This happened because the recursive call for list items did not pass the `parent_key` context, causing the sensitive key detection to fail for the list's contents.
**Learning:** Context-aware recursive functions must explicitly preserve and pass down the context (e.g., the parent key) to all child elements, including those in lists, to ensure security policies are applied consistently across nested data structures.
**Prevention:** Always pass the identifying key or context into recursive calls for both dictionary values and list elements. Test redaction logic specifically with nested lists and complex data structures to ensure no context is lost during traversal.

## 2026-02-13 - Path Traversal in Clarinet.toml Parsing
**Vulnerability:** The application was resolving contract paths from `Clarinet.toml` without validation, allowing a malicious configuration file to point to sensitive files outside the project directory (e.g., `../../etc/passwd`).
**Learning:** Configuration files that specify file paths are a common vector for path traversal attacks. Path joining alone is not secure as it can resolve to absolute paths or traverse upwards.
**Prevention:** Always use a safety utility (like `is_safe_path`) that resolves paths and ensures they stay within an intended base directory using `os.path.commonpath` or equivalent. Reject absolute paths in configuration-based file resolution.

## 2026-02-14 - Timing Attack Mitigation and Resource Integrity
**Vulnerability:** The local wallet connection server used standard string comparison (`!=`) for session tokens, potentially exposing the application to timing attacks. Additionally, external CDN-hosted scripts were loaded without integrity checks, posing a risk of supply chain attacks.
**Learning:** Security tokens must always be compared using constant-time functions (like `secrets.compare_digest`) to prevent side-channel leaks. Furthermore, third-party resources from CDNs should be protected by Subresource Integrity (SRI) hashes to ensure that the delivered content matches the expected version and hasn't been tampered with.
**Prevention:** Use `secrets.compare_digest` for all authentication token comparisons. Always include `integrity` and `crossorigin` attributes when including scripts from external CDNs.

## 2026-02-15 - Atomic Persistence and Secure Creation
**Vulnerability:** Configuration updates followed a "truncate and write" pattern, which is not atomic and can lead to file corruption on failure. Additionally, the "create then chmod" pattern for securing files leaves a small window of exposure where the file has default world-readable permissions.
**Learning:** Robust security architecture requires atomic operations for sensitive data persistence. Furthermore, file permissions should be restricted at the moment of creation (e.g., via `os.umask`) rather than after the fact, to eliminate race conditions. Centralizing this logic ensures consistent enforcement across CLI, GUI, and API interfaces.
**Prevention:** Always use a centralized utility for configuration saving that implements atomic writes (via `os.replace` on a temporary file) and pre-emptive permission restriction (via `os.umask` on POSIX).

## 2026-02-16 - Hardened Data Persistence & Logging
**Vulnerability:** Application-generated files like API caches, monitoring summaries, and PID files were being created with default world-readable permissions (0o664/0o644) using standard `json.dump` or `open("w")` calls. This posed a risk of sensitive state disclosure on multi-user systems.
**Learning:** Every file persisted by the application—including temporary state and logs—must be treated as sensitive. Inconsistent use of secure persistence utilities (like `save_secure_config`) can leave gaps in the application's defense-in-depth posture. Standardizing on a centralized secure saver ensures that all artifacts benefit from atomic writes, automatic redaction, and restricted 0600 permissions.
**Prevention:** Standardize all file persistence to use `save_secure_config` for structured data and `set_secure_permissions` for logs and system files (like PIDs). Avoid manual `json.dump` or `open("w")` for persistent state; instead, pass the data directly to a secure utility that enforces the project's security standards by default.
