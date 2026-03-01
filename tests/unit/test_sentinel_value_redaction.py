import pytest
from stacksorbit_secrets import redact_recursive, is_sensitive_value

def test_is_sensitive_value_private_key():
    """Verify that private keys are detected as sensitive values."""
    # 64 hex chars
    pk64 = "a" * 64
    assert is_sensitive_value(pk64) is True

    # 66 hex chars
    pk66 = "01" + "a" * 64
    assert is_sensitive_value(pk66) is True

    # 0x-prefixed (66 or 68 total chars)
    pk_prefixed_64 = "0x" + "a" * 64
    pk_prefixed_66 = "0X" + "a" * 66
    assert is_sensitive_value(pk_prefixed_64) is True
    assert is_sensitive_value(pk_prefixed_66) is True

    # Too short
    assert is_sensitive_value("a" * 63) is False

    # Non-hex
    assert is_sensitive_value("g" * 64) is False

def test_is_sensitive_value_mnemonic():
    """Verify that mnemonics are detected as sensitive values."""
    # 12 words
    mnemonic12 = "word " * 11 + "word"
    assert is_sensitive_value(mnemonic12) is True

    # 24 words
    mnemonic24 = "word " * 23 + "word"
    assert is_sensitive_value(mnemonic24) is True

    # 11 words (invalid)
    mnemonic11 = "word " * 10 + "word"
    assert is_sensitive_value(mnemonic11) is False

    # Mixed case (usually not a mnemonic)
    mnemonic_mixed = "Word " * 11 + "Word"
    assert is_sensitive_value(mnemonic_mixed) is False

def test_redact_recursive_by_value():
    """Verify that sensitive values are redacted even with non-sensitive keys."""
    config = {
        "regular_field": "normal_value",
        "random_name": "a" * 64,  # Looks like a private key
        "prefixed_secret": "0x" + "b" * 64,  # 0x-prefixed private key
        "another_random": "word " * 11 + "word",  # Looks like a mnemonic
        "nested": {
            "hidden_secret": "c" * 64
        }
    }

    redacted = redact_recursive(config)

    assert redacted["regular_field"] == "normal_value"
    assert redacted["random_name"] == "<redacted>"
    assert redacted["prefixed_secret"] == "<redacted>"
    assert redacted["another_random"] == "<redacted>"
    assert redacted["nested"]["hidden_secret"] == "<redacted>"

def test_redact_recursive_preserves_placeholders():
    """Verify that placeholders are NOT redacted even if they look like they could be sensitive (though placeholders usually don't)."""
    config = {
        "my_key": "your_private_key_here"
    }
    redacted = redact_recursive(config)
    # Even if we mark 'my_key' as sensitive in the call, is_placeholder should preserve it
    assert redacted["my_key"] == "your_private_key_here"

    # Test with parent_key marked sensitive
    redacted_sensitive = redact_recursive("your_private_key_here", parent_key="DEPLOYER_PRIVKEY")
    assert redacted_sensitive == "your_private_key_here"
