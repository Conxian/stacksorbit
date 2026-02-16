
import pytest
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from wallet_connect import WalletConnectHandler, save_wallet_address

def test_wallet_connect_headers():
    """Test that WalletConnectHandler sends the correct security headers."""
    handler = MagicMock(spec=WalletConnectHandler)
    handler.path = "/?token=test_token"
    WalletConnectHandler.session_token = "test_token"

    # Mock the necessary attributes for do_GET
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = MagicMock()

    # Call do_GET
    WalletConnectHandler.do_GET(handler)

    # Verify headers
    calls = [call[0] for call in handler.send_header.call_args_list]
    headers = {c[0]: c[1] for c in calls}

    assert "X-Frame-Options" in headers
    assert headers["X-Frame-Options"] == "DENY"
    assert "Referrer-Policy" in headers
    assert headers["Referrer-Policy"] == "no-referrer"
    assert "Content-type" in headers
    assert "charset=utf-8" in headers["Content-type"]

def test_save_wallet_address_filters_secrets(tmp_path):
    """Test that save_wallet_address filters out sensitive keys."""
    env_file = tmp_path / ".env"
    env_file.write_text("SYSTEM_ADDRESS=old_address\nDEPLOYER_PRIVKEY=secret_key\nOTHER_VAR=value\n")

    with patch("wallet_connect.Path", return_value=env_file), \
         patch("wallet_connect.save_secure_config") as mock_save:
        save_wallet_address("new_address")

    # In our refactored version, save_wallet_address uses save_secure_config
    # which handles filtering and permissions.
    mock_save.assert_called_once()
    args, _ = mock_save.call_args
    assert args[0] == str(env_file)
    assert args[1]["SYSTEM_ADDRESS"] == "new_address"
    assert args[1]["OTHER_VAR"] == "value"
