import pytest
from stacksorbit_secrets import is_sensitive_value, redact_recursive

def test_is_sensitive_value_newline_bypass():
    """🛡️ Sentinel: Verify that secrets with newlines are correctly detected."""
    # Private key with trailing newline
    pk_newline = "a" * 64 + "\n"
    assert is_sensitive_value(pk_newline) is True

    # Mnemonic with internal newlines (multiline mnemonic)
    mnemonic_multiline = "word " * 5 + "\n" + "word " * 5 + "\n" + "word word"
    assert is_sensitive_value(mnemonic_multiline) is True

    # Private key with 0x prefix and newline
    pk_prefixed_newline = "0x" + "b" * 64 + "\r\n"
    assert is_sensitive_value(pk_prefixed_newline) is True

def test_redact_recursive_newline_bypass():
    """🛡️ Sentinel: Verify that secrets with newlines are correctly redacted."""
    config = {
        "pk": "c" * 64 + "\n",
        "mnemonic": "word " * 11 + "\nword",
        "nested": {
            "key": "d" * 64 + "\r"
        }
    }

    redacted = redact_recursive(config)

    assert redacted["pk"] == "<redacted>"
    assert redacted["mnemonic"] == "<redacted>"
    assert redacted["nested"]["key"] == "<redacted>"

def test_is_sensitive_value_large_string_still_fast_fails():
    """Bolt ⚡: Verify that very large strings still fast-fail for performance."""
    large_string = "a" * 501
    # This should be False even if it contains 64 hex chars (which it doesn't here, but still)
    assert is_sensitive_value(large_string) is False
