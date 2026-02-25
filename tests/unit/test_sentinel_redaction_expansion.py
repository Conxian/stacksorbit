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
