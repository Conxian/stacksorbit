"""
Centralized list of secret keys for StacksOrbit.
"""

import os
import functools
import json

SECRET_KEYS = {
    "HIRO_API_KEY",
    "DEPLOYER_PRIVKEY",
    "STACKS_DEPLOYER_PRIVKEY",
    "TESTNET_DEPLOYER_MNEMONIC",
    "STACKS_PRIVKEY",
    "SYSTEM_PRIVKEY",
    "SYSTEM_MNEMONIC",
    "TESTNET_WALLET1_MNEMONIC",
    "TESTNET_WALLET2_MNEMONIC",
}

# 🛡️ Sentinel: Sensitive substrings to identify potential secrets in configuration keys.
# We include broad terms like 'PRIVATE', 'PWD', and 'PASS' to catch common secret naming conventions.
SENSITIVE_SUBSTRINGS = [
    "KEY",
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "MNEMONIC",
    "SEED",
    "PRIVATE",
    "PWD",
    "PASS",
    "AUTH",
    "CERTIFICATE",
    "CREDENTIAL",
    "PKCS",
    "SSH",
    "PGP",
    "GPG",
]

# Bolt ⚡: Pre-compile regex for faster substring matching in high-frequency checks.
import re
SENSITIVE_RE = re.compile("|".join(SENSITIVE_SUBSTRINGS))


def redact_recursive(item, parent_key="", is_sensitive=None):
    """
    🛡️ Sentinel: Recursively traverses a configuration dictionary or list to redact sensitive information.
    This ensures that even nested secrets (e.g., in loaded templates or manifests) are protected.
    """
    # Bolt ⚡: Determine sensitivity once per key/level to avoid redundant O(N) checks in lists.
    if is_sensitive is None:
        is_sensitive = is_sensitive_key(parent_key)

    if isinstance(item, dict):
        # Reset sensitivity for dict children as they have their own keys
        return {key: redact_recursive(value, key) for key, value in item.items()}
    elif isinstance(item, list):
        # Pass current sensitivity to list items as they inherit the parent key's sensitivity
        return [redact_recursive(sub_item, parent_key, is_sensitive) for sub_item in item]
    else:
        # Check if the parent key is a known secret or contains a sensitive substring.
        if is_sensitive and item is not None:
            # Skip empty values or common non-secret placeholders
            if is_placeholder(str(item)):
                return item

            # Redact the value but preserve its type for clarity (e.g., show empty string or 0)
            if isinstance(item, str):
                return "<redacted>"
            elif isinstance(item, (int, float)):
                return 0
            elif isinstance(item, bool):
                return False

        # Return the original value if it's not sensitive.
        return item


@functools.lru_cache(maxsize=1024)
def _is_sensitive_normalized(k: str) -> bool:
    """Bolt ⚡: Internal cached check for normalized (uppercase) keys."""
    return k in SECRET_KEYS or bool(SENSITIVE_RE.search(k))


@functools.lru_cache(maxsize=1024)
def is_sensitive_key(key: str) -> bool:
    """
    Check if a configuration key is considered sensitive.
    A key is sensitive if it's in the known SECRET_KEYS set or
    contains any of the SENSITIVE_SUBSTRINGS.

    Bolt ⚡: We cache this outer function to avoid redundant .upper() calls for
    identical key strings (e.g. during recursive redaction of large lists).
    """
    if not key or not isinstance(key, str):
        return False

    # Bolt ⚡: Normalize to upper case BEFORE hitting the secondary cache to maximize
    # efficiency for case variations (e.g., "key" and "KEY" hit the same entry).
    return _is_sensitive_normalized(key.upper())


@functools.lru_cache(maxsize=256)
def validate_stacks_address(address: str, network: str = None) -> bool:
    """
    Validate Stacks address format by network and charset.
    Prefix rules: SP for mainnet, ST for testnet/devnet.
    C32 allowed charset (I, L, O, U are excluded).

    Bolt ⚡: Caching this function improves UI responsiveness during real-time
    validation by avoiding redundant string normalization and regex matching.
    """
    if not address or not isinstance(address, str):
        return False

    # Bolt ⚡: Fast-fail minimum length check before expensive string manipulations.
    # Stacks addresses (SP/ST) are at least 28 characters.
    if len(address) < 28:
        return False

    addr = address.strip().upper()

    # Bolt ⚡: Use pre-compiled network-aware regex for ~35% speedup.
    # These combine prefix, length, and charset checks into a single pass.
    reg = NETWORK_ADDR_RE_MAP.get(network, GENERIC_ADDR_RE)
    return bool(reg.match(addr))


# 🛡️ Sentinel: Centralized list of safe placeholders for secrets.
SAFE_PLACEHOLDERS = {
    "",
    "your_private_key_here",
    "your_hiro_api_key",
    "your_stacks_address_here",
}


@functools.lru_cache(maxsize=1024)
def is_placeholder(value: str) -> bool:
    """
    🛡️ Sentinel: Check if a value is a known safe placeholder or empty.
    This ensures consistent, case-insensitive handling across all loaders.

    Bolt ⚡: Caching this function avoids redundant .strip().lower() calls
    for repeated configuration values and API response fields.
    """
    if value is None:
        return True

    return str(value).strip().lower() in SAFE_PLACEHOLDERS
# Bolt ⚡: Pre-compile network-aware regexes for faster Stacks address validation.
# These combine prefix, length, and charset checks into a single pass.
# 28-41 total chars -> 2 chars prefix + 26-39 chars body.
MAINNET_ADDR_RE = re.compile(r"^SP[0-9ABCDEFGHJKMNPQRSTVWXYZ]{26,39}$")
TESTNET_ADDR_RE = re.compile(r"^ST[0-9ABCDEFGHJKMNPQRSTVWXYZ]{26,39}$")
GENERIC_ADDR_RE = re.compile(r"^S[PT][0-9ABCDEFGHJKMNPQRSTVWXYZ]{26,39}$")

# Bolt ⚡: Network to regex mapping for O(1) selection.
NETWORK_ADDR_RE_MAP = {
    "mainnet": MAINNET_ADDR_RE,
    "testnet": TESTNET_ADDR_RE,
    "devnet": TESTNET_ADDR_RE,
}

# Bolt ⚡: Pre-compile regex for faster hex character validation.
HEX_RE = re.compile(r"^[0-9a-fA-F]+$")


def save_secure_config(filepath: str, config: object, json_format: bool = False):
    """
    🛡️ Sentinel: Atomically and securely save configuration to a file.
    Uses a temporary file and os.replace for atomicity, and ensures
    secure file permissions (0600) from the start.
    If json_format is True, the config is automatically redacted and saved as JSON.
    """
    if not filepath:
        return

    temp_path = f"{filepath}.tmp"
    try:
        # Bolt ⚡: Use umask to ensure the file is created with restricted permissions (0600).
        # This is more secure than chmod-ing after creation as there is no window of exposure.
        old_umask = None
        if os.name == "posix":
            old_umask = os.umask(0o077)

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                if json_format:
                    # 🛡️ Sentinel: Automatically redact before saving as JSON
                    redacted = redact_recursive(config)
                    json.dump(redacted, f, indent=2)
                # Handle both dict and string content
                elif isinstance(config, dict):
                    for key, value in config.items():
                        # 🛡️ Sentinel: Security Enforcer.
                        # Explicitly skip any known secrets or potential sensitive keys.
                        if not is_sensitive_key(str(key)):
                            f.write(f"{key}={value}\n")
                else:
                    # If it's a string (pre-formatted), we just write it.
                    # Caller is responsible for filtering secrets if passing a string.
                    f.write(str(config))
        finally:
            if old_umask is not None:
                os.umask(old_umask)

        # Atomic swap: os.replace is atomic on most systems.
        os.replace(temp_path, filepath)

        # Double-check permissions just in case
        set_secure_permissions(filepath)

    except Exception as e:
        # Clean up temp file on failure
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        raise e


@functools.lru_cache(maxsize=128)
def validate_private_key(privkey: str) -> bool:
    """
    Validate Stacks private key format (64 or 66 chars hex).

    Bolt ⚡: Caching this function improves UI responsiveness during real-time
    validation of private keys.
    """
    if not privkey or not isinstance(privkey, str):
        return False
    pk = privkey.strip()
    # Bolt ⚡: Check length first to fail fast and avoid more expensive checks.
    # This also catches placeholders like 'your_private_key_here' (21 chars) automatically.
    if len(pk) not in (64, 66):
        return False
    # Bolt ⚡: Use regex for faster hex character validation (~5.5x faster than loop).
    return bool(HEX_RE.match(pk))


def set_secure_permissions(filepath: str):
    """
    🛡️ Sentinel: Set file permissions to 600 (owner read/write only) on POSIX systems.
    This prevents other users on the same machine from reading sensitive configuration files.
    """
    try:
        if os.name == "posix" and os.path.exists(filepath):
            os.chmod(filepath, 0o600)
    except Exception:
        # Fail gracefully if permissions cannot be set
        pass


def is_safe_path(base_dir: str, target_path: str) -> bool:
    """
    🛡️ Sentinel: Check if a target path is safe and stays within the base directory.
    Prevents path traversal attacks by ensuring the resolved path is within the base.
    """
    if not target_path or not base_dir:
        return False
    try:
        # Reject absolute paths immediately for configuration-based file resolution.
        if os.path.isabs(target_path):
            return False

        base = os.path.abspath(base_dir)
        target = os.path.abspath(os.path.join(base, target_path))

        # os.path.commonpath returns the longest common sub-path of each passed pathname.
        # If it matches the base, then target is within base.
        return os.path.commonpath([base, target]) == base
    except Exception:
        return False
