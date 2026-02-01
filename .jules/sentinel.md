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
