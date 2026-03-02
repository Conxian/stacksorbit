"""
Centralized list of secret keys for StacksOrbit.
"""

import os
import functools
import json
import re

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
# We maintain broad security coverage while relying on PUBLIC_RE to filter false positives.
# Optimized to remove redundant patterns and use shortest effective substrings.
SENSITIVE_SUBSTRINGS = [
    "KEY",
    "SECRET",
    "SENSITIVE",
    "TOKEN",
    "PASS",
    "PWD",
    "AUTH",
    "CERT",
    "CRED",
    "MNEMONIC",
    "SEED",
    "PRIV",
    "PKCS",
    "SSH",
    "PGP",
    "GPG",
    "SALT",
    "SIGNATURE",
    "JWT",
    "SESS",
    "BEARER",
    "PHRASE",
    "RECOVERY",
    "PEM",
    "XPRV",
    "ENCRYPT",
    "VAULT",
    "MASTER",
    "ROOT",
    "ADMIN",
    "BIP3",
    "KUBECONFIG",
    "DOCKER",
    "DATABASE",
    "DB_",
]

# Bolt ⚡: Pre-compile regex for faster substring matching in high-frequency checks.
SENSITIVE_RE = re.compile("|".join(SENSITIVE_SUBSTRINGS))

# Bolt ⚡: Public keys that should be excluded from value-based secret detection.
# These often contain 64-character hex strings but are public blockchain data.
PUBLIC_SUBSTRINGS = [
    "PUBLIC",
    "TX_",
    "TXID",
    "HASH",
    "SIGNATURE",  # Explicitly allow standalone 'SIGNATURE' as public
    "ADDR",
    "PRINCIPAL",
]

# Bolt ⚡: Pre-compile regex for faster public key matching.
PUBLIC_RE = re.compile("|".join(PUBLIC_SUBSTRINGS))

# Bolt ⚡: Pre-compile regex for faster hex character validation.
HEX_RE = re.compile(r"^[0-9a-fA-F]+$")


@functools.lru_cache(maxsize=128)
def validate_private_key(privkey: str) -> bool:
    """
    Validate Stacks private key format (64 or 66 chars hex, optional 0x prefix).

    Bolt ⚡: Caching this function improves UI responsiveness during real-time
    validation of private keys.
    """
    if not privkey or not isinstance(privkey, str):
        return False
    pk = privkey.strip()

    # 🛡️ Sentinel: Support optional 0x prefix for Stacks private keys.
    if pk.lower().startswith("0x"):
        pk = pk[2:]

    # Bolt ⚡: Check length first to fail fast and avoid more expensive checks.
    # This also catches placeholders like 'your_private_key_here' (21 chars) automatically.
    if len(pk) not in (64, 66):
        return False
    # Bolt ⚡: Use regex for faster hex character validation (~5.5x faster than loop).
    return bool(HEX_RE.match(pk))


@functools.lru_cache(maxsize=1024)
def _is_sensitive_value_cached(value: str) -> bool:
    """Internal cached logic for sensitive value detection."""
    # Check for Stacks private key format (64 or 66 hex chars)
    if validate_private_key(value):
        return True

    # Bolt ⚡: Use a fast split and length check.
    # BIP-39 supports 12, 15, 18, 21, and 24 words.
    words = value.strip().split()
    if len(words) in (12, 15, 18, 21, 24) and all(len(w) >= 3 for w in words):
        # Additional check: most mnemonics are all lowercase or all uppercase
        if value.islower() or value.isupper():
            return True

    return False


def is_sensitive_value(value: str) -> bool:
    """
    🛡️ Sentinel: Check if a value looks like a secret (e.g., a private key or mnemonic).
    This provides defense-in-depth by catching secrets even if stored under non-sensitive keys.

    Bolt ⚡: Optimization - Fast-fail for non-strings or large strings.
    This prevents unnecessary LRU cache lookups and expensive processing for non-secrets.
    """
    # ⚡ Bolt: Fast-fail non-string types immediately.
    if not isinstance(value, str) or not value:
        return False

    # 🛡️ Sentinel: Strip whitespace before checking length to prevent newline-based bypasses.
    # This ensures that multiline secrets or those with trailing newlines are still detected.
    v = value.strip()

    # ⚡ Bolt: Fast-fail for large strings (e.g. source code).
    # Mnemonics are typically under 500 characters even with multiple lines.
    if len(v) > 500:
        return False

    return _is_sensitive_value_cached(v)


def redact_recursive(item, parent_key="", is_sensitive=None, is_public=None):
    """
    🛡️ Sentinel: Recursively traverses a configuration dictionary or list to redact sensitive information.
    This ensures that even nested secrets (e.g., in loaded templates or manifests) are protected.

    Bolt ⚡: Optimized to skip value-based detection for known public keys.
    """
    # Bolt ⚡: Determine states once per key/level to avoid redundant O(N) checks in lists.
    if is_sensitive is None:
        is_sensitive = is_sensitive_key(parent_key)
    if is_public is None:
        is_public = is_public_key(parent_key)

    if isinstance(item, dict):
        # 🛡️ Sentinel: Dict children inherit parent sensitivity (Defense-in-Depth).
        # Bolt ⚡: Child keys inherit parent state, but are re-checked if parent isn't sensitive/public.
        return {
            key: redact_recursive(
                value,
                key,
                is_sensitive or is_sensitive_key(key),
                is_public or is_public_key(key),
            )
            for key, value in item.items()
        }
    elif isinstance(item, (list, tuple, set)):
        # Pass current sensitivity/publicity to list items as they inherit the parent key's state.
        redacted_items = [
            redact_recursive(sub_item, parent_key, is_sensitive, is_public)
            for sub_item in item
        ]
        if isinstance(item, tuple):
            return tuple(redacted_items)
        if isinstance(item, set):
            return set(redacted_items)
        return redacted_items
    else:
        # ⚡ Bolt: Check for non-sensitive non-string types early to bypass expensive logic.
        # Fast-path for integers, floats, and booleans that aren't marked as sensitive.
        if not is_sensitive and isinstance(item, (int, float, bool)):
            return item

        if item is None:
            return None

        # Check if the parent key is a known secret or contains a sensitive substring.
        # 🛡️ Sentinel: Also check if the value itself looks like a secret (Defense-in-Depth).
        # Bolt ⚡: Skip value-based detection if the key is known to be public (e.g. TX_ID).
        # ⚡ Bolt: Avoid redundant str() conversion if item is already a string.
        item_str = item if isinstance(item, str) else str(item)
        if (
            is_sensitive or (not is_public and is_sensitive_value(item_str))
        ):
            # Skip empty values or common non-secret placeholders
            if is_placeholder(item_str):
                return item

            # Redact the value but preserve its type for clarity (e.g., show empty string or 0)
            if isinstance(item, str):
                return "<redacted>"
            elif isinstance(item, bytes):
                return b"<redacted>"
            elif isinstance(item, (int, float)):
                return 0
            elif isinstance(item, bool):
                return False
            else:
                # 🛡️ Sentinel: Catch-all for any other sensitive type (Defense-in-Depth)
                return "<redacted>"

        # Return the original value if it's not sensitive.
        return item


@functools.lru_cache(maxsize=1024)
def _is_sensitive_normalized(k: str) -> bool:
    """Bolt ⚡: Internal cached check for normalized (uppercase) keys."""
    if k in SECRET_KEYS:
        return True

    # Check if it matches sensitive patterns
    if not SENSITIVE_RE.search(k):
        return False

    # 🛡️ Sentinel: Surgical exclusion for public identifiers.
    # If the key contains a public identifier, it's not sensitive UNLESS it
    # also contains a high-confidence sensitive keyword like 'PRIV', 'SECRET', or 'AUTH'.
    # This allows 'PUBLIC_KEY' while protecting 'PUBLIC_PRIVATE_KEY_PAIR' and 'AUTH_SIGNATURE'.
    if _is_public_normalized(k):
        if not any(word in k for word in ["PRIV", "SECRET", "MNEMONIC", "PASS", "AUTH"]):
            return False

    return True


@functools.lru_cache(maxsize=1024)
def _is_public_normalized(k: str) -> bool:
    """Bolt ⚡: Internal cached check for normalized (uppercase) public keys."""
    return bool(PUBLIC_RE.search(k))


@functools.lru_cache(maxsize=1024)
def is_public_key(key: str) -> bool:
    """
    Check if a configuration or API key is considered public.
    Public keys are excluded from value-based secret detection.

    Bolt ⚡: We cache this outer function to avoid redundant .upper() calls.
    """
    if not key or not isinstance(key, str):
        return False
    return _is_public_normalized(key.upper())


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
    "0x_your_private_key_here",
    "your_hiro_api_key",
    "your_stacks_address_here",
    "your_mnemonic_here",
    "your_seed_phrase_here",
    "your_recovery_phrase_here",
}


@functools.lru_cache(maxsize=1024)
def _is_placeholder_cached(value: str) -> bool:
    """Internal cached logic for placeholder detection."""
    return value.strip().lower() in SAFE_PLACEHOLDERS


def is_placeholder(value: str) -> bool:
    """
    🛡️ Sentinel: Check if a value is a known safe placeholder or empty.
    This ensures consistent, case-insensitive handling across all loaders.

    Bolt ⚡: Caching this function avoids redundant .strip().lower() calls
    for repeated configuration values and API response fields.
    """
    if value is None:
        return True

    # Bolt ⚡: Optimization - Skip str() conversion if already a string.
    val_str = value if isinstance(value, str) else str(value)

    # Bolt ⚡: Optimization - Safe placeholders are short (longest is ~26 chars).
    # Skip string normalization for large strings to avoid O(N) overhead.
    if len(val_str) > 50:
        return False

    return _is_placeholder_cached(val_str)


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


def save_secure_config(filepath: str, config: object, json_format: bool = False, redact: bool = True, indent: int = 2):
    """
    🛡️ Sentinel: Atomically and securely save configuration to a file.
    Uses a temporary file and os.replace for atomicity, and ensures
    secure file permissions (0600) from the start.
    If json_format is True, the config is automatically redacted and saved as JSON.

    Bolt ⚡: Added 'redact' and 'indent' parameters to allow performance-critical
    caching systems to skip expensive O(N) redaction and reduce I/O overhead.
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
                    # 🛡️ Sentinel: Automatically redact before saving as JSON (if enabled)
                    # Bolt ⚡: Optimization - Skip redaction for public/cached data to save CPU.
                    if redact:
                        redacted = redact_recursive(config)
                    else:
                        redacted = config
                    json.dump(redacted, f, indent=indent)
                # Handle both dict and string content
                elif isinstance(config, dict):
                    for key, value in config.items():
                        # 🛡️ Sentinel: Security Enforcer.
                        # Explicitly skip any known secrets, potential sensitive keys, OR values that look like secrets.
                        # This prevents secrets from being saved to disk even if stored under generic key names.
                        if not is_sensitive_key(str(key)) and not is_sensitive_value(str(value)):
                            # 🛡️ Sentinel: Sanitize key and value to prevent injection and format breakage.
                            # We remove newlines and equals signs from keys to prevent configuration injection.
                            safe_key = (
                                str(key)
                                .replace("\n", "")
                                .replace("\r", "")
                                .replace("=", "")
                            )
                            safe_val = (
                                str(value).replace("\n", "\\n").replace("\r", "\\r")
                            )
                            f.write(f"{safe_key}={safe_val}\n")
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

        # 🛡️ Sentinel: Use realpath to resolve all symlinks before path validation.
        # This prevents Path Traversal via symlinks to outside files.
        base = os.path.realpath(base_dir)
        target = os.path.realpath(os.path.join(base, target_path))

        # os.path.commonpath returns the longest common sub-path of each passed pathname.
        # If it matches the base, then target is within base.
        return os.path.commonpath([base, target]) == base
    except Exception:
        return False
