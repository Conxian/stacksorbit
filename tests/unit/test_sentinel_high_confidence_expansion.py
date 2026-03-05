import pytest
from stacksorbit_secrets import is_sensitive_key

def test_high_confidence_expansion():
    """🛡️ Sentinel: Verify that expanded high-confidence keywords are redacted even with public prefixes."""

    # Test cases for newly added high-confidence keywords
    new_sensitive_composite_keys = [
        "PUBLIC_SSH_KEY",
        "ADDR_PGP_KEY",
        "TX_PEM_CERT",
        "PUBLIC_GPG_KEY",
        "ADDR_PKCS12_CERT",
        "TX_SSH_PRIVATE_KEY",
        "SYSTEM_PEM_FILE"
    ]

    for key in new_sensitive_composite_keys:
        assert is_sensitive_key(key) is True, f"Key {key} should be sensitive"

def test_existing_high_confidence():
    """🛡️ Sentinel: Verify that existing high-confidence keywords still work correctly."""
    existing_sensitive_composite_keys = [
        "PUBLIC_JWT_TOKEN",
        "ADDR_TOKEN_SECRET",
        "TX_AUTH_KEY",
        "PUBLIC_RECOVERY_PHRASE",
        "ADDR_SEED_PHRASE",
        "PUBLIC_DB_PASSWORD"
    ]

    for key in existing_sensitive_composite_keys:
        assert is_sensitive_key(key) is True, f"Key {key} should be sensitive"

def test_normal_public_keys():
    """🛡️ Sentinel: Verify that normal public keys without high-confidence keywords are NOT sensitive."""
    normal_public_keys = [
        "PUBLIC_KEY",
        "ADDR_PRINCIPAL",
        "TX_HASH",
        "TX_ID",
        "SIGNATURE"
    ]

    for key in normal_public_keys:
        assert is_sensitive_key(key) is False, f"Key {key} should NOT be sensitive"
