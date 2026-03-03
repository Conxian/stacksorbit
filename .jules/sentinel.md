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

## 2026-02-17 - Local Server Anti-Caching and Defensive Sanitization
**Vulnerability:** The local wallet connection server lacked anti-caching headers, potentially persisting sensitive session tokens in browser caches. It also lacked client-side input sanitization before making external API calls.
**Learning:** Local development servers that manage sensitive state via URL parameters must explicitly prevent caching to minimize the "persistence footprint" of session tokens. Additionally, defense-in-depth requires sanitizing user-provided data (like blockchain addresses) at the earliest possible entry point, even in the frontend.
**Prevention:** Apply strict anti-caching headers (`Cache-Control: no-store`) to all authentication-related endpoints. Implement regex-based sanitization in client-side scripts before dispatching requests to external APIs. Expand global secret detection keyword lists as new sensitive data types (e.g., certificates, SSH keys) are identified.

## 2026-02-18 - Keyword Hardening & Secure Persistence
**Vulnerability:** Incomplete list of sensitive keywords in the central security module left potential secrets (like JWT tokens, salts, or API keys) unprotected during configuration persistence and logging. Additionally, .env values lacked newline escaping, which could be exploited for configuration injection.
**Learning:** Security keywords must be regularly audited and expanded to match modern development patterns (e.g., JWT, Access Tokens). Configuration persistence to plaintext formats like .env requires explicit escaping of control characters (like newlines) to prevent format-breaking injections.
**Prevention:** Maintain a comprehensive and centralized list of sensitive substrings for secret detection. Always sanitize and escape values when persisting configuration to disk to ensure file integrity and prevent injection attacks.

## 2026-02-24 - Symlink Resolution and Contextual Redaction
**Vulnerability:** A Path Traversal vulnerability existed in `is_safe_path` because it used `abspath` instead of `realpath`, allowing access to outside files via symlinks. Additionally, `redact_recursive` failed to redact nested secrets when they were contained within dictionaries that had generic keys but were children of a sensitive parent key.
**Learning:** Defense-in-depth requires anticipating how low-level OS features like symbolic links can bypass high-level path validation logic. Furthermore, recursive security operations must maintain state across different data types (dicts and lists) to ensure that the "sensitivity context" is never lost during deep traversal.
**Prevention:** Always use `os.path.realpath` for path validation to resolve symlinks before checking bounds. Ensure that recursive redaction logic explicitly passes down the sensitivity state to all children, regardless of their container type (dict or list), and use short-circuit logic to optimize performance when the state is already known.

## 2026-02-26 - BIP-39 Expansion & HTTP Request Hardening
**Vulnerability:** The secret detection engine only recognized 12 and 24-word mnemonics, missing other valid BIP-39 lengths (15, 18, 21). Additionally, the wallet connection server did not validate for negative `Content-Length`, which could be used to bypass size limits in some HTTP implementations.
**Learning:** Security detection patterns must be comprehensive and align with industry standards (like the full BIP-39 spec). Furthermore, input validation on low-level protocol headers (like `Content-Length`) is a critical layer of defense against Denial of Service and memory exhaustion attacks.
**Prevention:** Regularly audit and align security patterns with official specifications. Always implement bounds checking (including lower bounds) for all user-provided size or length parameters in network handlers.

## 2026-02-25 - Keyword Expansion & Standardized Redaction
**Vulnerability:** Incomplete secret detection keywords left common sensitive patterns (like Bearer tokens, recovery phrases, or session cookies) potentially unredacted in logs and configuration artifacts.
**Learning:** Security keywords must be proactively expanded as the application grows to cover diverse authentication and persistence patterns. Standardizing placeholders for all sensitive fields (including mnemonics) ensures that setup wizards and default templates don't trigger false-positive security blocks while still maintaining a strict "no-secrets-in-plaintext" policy.
**Prevention:** Regularly audit and broaden centralized secret detection lists (e.g., `SENSITIVE_SUBSTRINGS`). Maintain a matching list of safe placeholders to ensure that developer-friendly defaults are recognized and preserved by the security engine.

## 2026-02-27 - Surgical Secret Exclusion for Public Keys
**Vulnerability:** Overly broad sensitive keyword matching (e.g., matching 'KEY') caused false positives for public blockchain data like 'PUBLIC_KEY', leading to unnecessary redaction or blocked configuration loading.
**Learning:** Broad exclusions (e.g., ignoring any key containing 'PUBLIC') are unsafe as they can be bypassed by composite keys like 'PUBLIC_PRIVATE_KEY_PAIR'. A surgical approach is required: allow public identifiers only if they lack high-confidence secret indicators (like 'PRIV', 'SECRET', or 'AUTH').
**Prevention:** Implement a layered validation for sensitive keys. First, identify potential sensitivity using broad patterns, then apply a conditional exclusion that re-verifies the absence of high-risk keywords within the public context.

## 2026-02-28 - Hex Prefix Normalization in Secret Detection
**Vulnerability:** Value-based secret detection bypassed 0x-prefixed Stacks private keys when stored under generic key names, as the validation logic only accounted for raw 64/66-character hex strings.
**Learning:** Hex-based secret detection must account for common prefix variations (like `0x` or `0X`) used in the target ecosystem (Stacks/Clarity). Naive length checks are easily bypassed by standard formatting conventions.
**Prevention:** Always normalize hex strings by stripping common prefixes before performing length and character set validation in security-critical utilities.

## 2026-03-01 - Surgical Exclusion Hardening for Public Identifiers
**Vulnerability:** The surgical exclusion logic in `is_sensitive_key` was too permissive, allowing high-risk secrets like `PUBLIC_RECOVERY_PHRASE` or `ADDR_SEED_PHRASE` to bypass redaction. This occurred because the re-validation list for public-prefixed keys was missing critical keywords like `PHRASE`, `SEED`, `RECOVERY`, and `MASTER`.
**Learning:** When using exclusion patterns for public data (e.g., ignoring keys with 'PUBLIC' or 'ADDR'), the secondary "high-confidence" check must be comprehensive. Implementation drift between the main `SENSITIVE_SUBSTRINGS` list and this re-validation list creates security holes for misnamed secrets.
**Prevention:** Synchronize the high-confidence keywords used for public identifier re-validation with the most critical patterns in the global secret detection list. Proactively expand this list to include `PHRASE`, `SEED`, `RECOVERY`, `PWD`, `XPRV`, `MASTER`, `VAULT`, `ADMIN`, and `ROOT`.
