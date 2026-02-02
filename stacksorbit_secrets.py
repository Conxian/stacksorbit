"""
Centralized list of secret keys for StacksOrbit.
"""

SECRET_KEYS = [
    "HIRO_API_KEY",
    "DEPLOYER_PRIVKEY",
    "STACKS_DEPLOYER_PRIVKEY",
    "TESTNET_DEPLOYER_MNEMONIC",
    "STACKS_PRIVKEY",
    "SYSTEM_PRIVKEY",
    "SYSTEM_MNEMONIC",
    "TESTNET_WALLET1_MNEMONIC",
    "TESTNET_WALLET2_MNEMONIC",
]

# 🛡️ Sentinel: Sensitive substrings to identify potential secrets in configuration keys.
SENSITIVE_SUBSTRINGS = ["KEY", "SECRET", "TOKEN", "PASSWORD", "MNEMONIC"]


def is_sensitive_key(key: str) -> bool:
    """
    Check if a configuration key is considered sensitive.
    A key is sensitive if it's in the known SECRET_KEYS list or
    contains any of the SENSITIVE_SUBSTRINGS.
    """
    if not key:
        return False

    k = key.upper()
    return k in SECRET_KEYS or any(sub in k for sub in SENSITIVE_SUBSTRINGS)
