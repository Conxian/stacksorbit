
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
         patch("wallet_connect.set_secure_permissions") as mock_chmod:
        save_wallet_address("new_address")

    content = env_file.read_text()
    assert "SYSTEM_ADDRESS=new_address" in content
    assert "OTHER_VAR=value" in content
    assert "DEPLOYER_PRIVKEY" not in content  # Should be filtered out
    mock_chmod.assert_called_once()
