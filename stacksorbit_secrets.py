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

    # Length and Charset validation
    if len(addr) != 41:
        return False

    # C32 allowed charset (I, L, O, U are excluded)
    allowed = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
    body = addr[2:]
    return all(ch in allowed for ch in body)


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
