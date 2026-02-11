"""
Centralized list of secret keys for StacksOrbit.
"""

import functools

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
]


def redact_recursive(item, parent_key=""):
    """
    🛡️ Sentinel: Recursively traverses a configuration dictionary or list to redact sensitive information.
    This ensures that even nested secrets (e.g., in loaded templates or manifests) are protected.
    """
    if isinstance(item, dict):
        return {key: redact_recursive(value, key) for key, value in item.items()}
    elif isinstance(item, list):
        return [redact_recursive(sub_item) for sub_item in item]
    else:
        # Check if the parent key is a known secret or contains a sensitive substring.
        if is_sensitive_key(parent_key) and item is not None:
            # Skip empty values or common non-secret placeholders
            if str(item).strip() == "" or str(item).lower() in (
                "your_private_key_here",
                "your_hiro_api_key",
                "your_stacks_address_here",
            ):
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


@functools.lru_cache(maxsize=128)
def is_sensitive_key(key: str) -> bool:
    """
    Check if a configuration key is considered sensitive.
    A key is sensitive if it's in the known SECRET_KEYS set or
    contains any of the SENSITIVE_SUBSTRINGS.
    """
    if not key:
        return False

    k = key.upper()
    return k in SECRET_KEYS or any(sub in k for sub in SENSITIVE_SUBSTRINGS)


def validate_stacks_address(address: str, network: str = None) -> bool:
    """
    Validate Stacks address format by network and charset.
    Prefix rules: SP for mainnet, ST for testnet/devnet.
    C32 allowed charset (I, L, O, U are excluded).
    """
    if not address or not isinstance(address, str):
        return False

    addr = address.strip().upper()

    # Prefix rules
    if network == "mainnet":
        if not addr.startswith("SP"):
            return False
    elif network in ["testnet", "devnet"]:
        if not addr.startswith("ST"):
            return False
    else:
        if not (addr.startswith("SP") or addr.startswith("ST")):
            return False

    # Length and Charset validation (Stacks addresses are typically 28-41 characters)
    if not (28 <= len(addr) <= 41):
        return False

    # C32 allowed charset (I, L, O, U are excluded)
    body = addr[2:]
    return all(ch in ALLOWED_C32_CHARS for ch in body)


# Bolt ⚡: Define C32 charset at module level to avoid redundant set creation.
ALLOWED_C32_CHARS = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")


def validate_private_key(privkey: str) -> bool:
    """
    Validate Stacks private key format (64 or 66 chars hex).
    """
    if not privkey or not isinstance(privkey, str):
        return False
    pk = privkey.strip()
    if pk.lower() == "your_private_key_here":
        return False
    if len(pk) not in (64, 66):
        return False
    # Hex-only characters
    return all(c in "0123456789abcdefABCDEF" for c in pk)


def set_secure_permissions(filepath: str):
    """
    🛡️ Sentinel: Set file permissions to 600 (owner read/write only) on POSIX systems.
    This prevents other users on the same machine from reading sensitive configuration files.
    """
    try:
        import os
        if os.name == 'posix' and os.path.exists(filepath):
            os.chmod(filepath, 0o600)
    except Exception:
        # Fail gracefully if permissions cannot be set
        pass
