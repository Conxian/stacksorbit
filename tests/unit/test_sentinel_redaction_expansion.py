import pytest
from stacksorbit_secrets import redact_recursive

def test_redact_bytes():
    """Test that bytes objects are correctly redacted."""
    key = "DEPLOYER_PRIVKEY"
    value = b"secret_bytes_123456"
    config = {key: value}
    redacted = redact_recursive(config)
    assert redacted[key] == b"<redacted>"

def test_redact_tuple():
    """Test that tuple objects are correctly redacted."""
    key = "DEPLOYER_PRIVKEY"
    value = ("secret1", "secret2")
    config = {key: value}
    redacted = redact_recursive(config)
    assert redacted[key] == ("<redacted>", "<redacted>")

def test_redact_set():
    """Test that set objects are correctly redacted."""
    key = "DEPLOYER_PRIVKEY"
    value = {"secret1", "secret2"}
    config = {key: value}
    redacted = redact_recursive(config)
    # set will collapse multiple identical "<redacted>" strings
    assert redacted[key] == {"<redacted>"}

def test_redact_unknown_object():
    """Test that unknown objects are correctly redacted."""
    class SecretObject:
        def __str__(self):
            return "secret_representation"

    key = "DEPLOYER_PRIVKEY"
    value = SecretObject()
    config = {key: value}
    redacted = redact_recursive(config)
    assert redacted[key] == "<redacted>"

def test_no_redact_safe_types():
    """Test that safe types are NOT redacted when the key is NOT sensitive."""
    config = {
        "PUBLIC_NAME": "public_value",
        "PUBLIC_DATA": b"public_bytes",
        "PUBLIC_INFO": ("public", "tuple")
    }
    redacted = redact_recursive(config)
    assert redacted["PUBLIC_NAME"] == "public_value"
    assert redacted["PUBLIC_DATA"] == b"public_bytes"
    assert redacted["PUBLIC_INFO"] == ("public", "tuple")

def test_nested_mixed_containers():
    """Test redaction in nested mixed containers."""
    config = {
        "METADATA": {
            "SENSITIVE_DATA": [
                b"bytes_secret",
                {"nested_key": ("tuple_secret",)}
            ]
        }
    }
    redacted = redact_recursive(config)
    assert redacted["METADATA"]["SENSITIVE_DATA"][0] == b"<redacted>"
    assert redacted["METADATA"]["SENSITIVE_DATA"][1]["nested_key"] == ("<redacted>",)

def test_sensitive_key_redaction_expansion():
    """🛡️ Sentinel: Verify that newly added high-confidence keywords are redacted even with public prefixes."""
    from stacksorbit_secrets import is_sensitive_key

    # Newly hardened keys (should now be True)
    assert is_sensitive_key("PUBLIC_RECOVERY_PHRASE") is True
    assert is_sensitive_key("ADDR_SEED_PHRASE") is True
    assert is_sensitive_key("PUBLIC_MASTER_KEY") is True
    assert is_sensitive_key("VAULT_PUBLIC_KEY") is True
    assert is_sensitive_key("XPRV_PUBLIC_KEY") is True
    assert is_sensitive_key("ADMIN_PUBLIC_KEY") is True
    assert is_sensitive_key("ROOT_PUBLIC_KEY") is True
    assert is_sensitive_key("PUBLIC_PWD") is True
    assert is_sensitive_key("ADDR_PASSWORD") is True

    # Original high-confidence keys (should remain True)
    assert is_sensitive_key("PUBLIC_PRIVATE_KEY") is True
    assert is_sensitive_key("ADDR_SECRET") is True
    assert is_sensitive_key("PUBLIC_MNEMONIC") is True
    assert is_sensitive_key("AUTH_SIGNATURE") is True

    # Generic public keys (should remain False)
    assert is_sensitive_key("PUBLIC_KEY") is False
    assert is_sensitive_key("ADDR_HASH") is False
    assert is_sensitive_key("TX_SIGNATURE") is False
    assert is_sensitive_key("CONTRACT_PRINCIPAL") is False
    assert is_sensitive_key("DEPLOYMENT_ADDR") is False

def test_case_insensitivity():
    """🛡️ Sentinel: Verify that detection is case-insensitive."""
    from stacksorbit_secrets import is_sensitive_key
    assert is_sensitive_key("public_recovery_phrase") is True
    assert is_sensitive_key("Addr_Seed_Phrase") is True
    assert is_sensitive_key("Public_Key") is False
