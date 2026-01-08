## 2024-05-20 - Mismatch in Secret Handling Guidance

**Vulnerability:** The `stacksorbit_cli.py` setup wizard advises users to set `DEPLOYER_PRIVKEY` as an environment variable for security, but the `EnhancedConfigManager` in `enhanced_conxian_deployment.py` loads this secret directly from the `.env` file.

**Learning:** This discrepancy creates a security risk by encouraging users to store plaintext secrets in `.env` files, despite guidance to the contrary. The root cause is a lack of a single, enforced standard for secret management across the application.

**Prevention:** All components must adhere to a strict secret management policy: prioritize environment variables for all secrets. The configuration loader should be updated to reflect this and issue warnings if secrets are found in insecure locations like `.env` files. Future security reviews must audit for consistent secret handling across the entire codebase.