import pytest
from unittest.mock import patch, AsyncMock
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets.data_table import RowKey

@pytest.mark.asyncio
async def test_gui_launches():
    """Test that the GUI launches without errors."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        assert pilot is not None
        await pilot.press("q")

@pytest.mark.asyncio
async def test_contract_selection_triggers_details_fetch():
    """Verify selecting a contract triggers the details fetch."""
    app = StacksOrbitGUI()
    with patch.object(app, 'fetch_contract_details', new_callable=AsyncMock) as mock_fetch:
        async with app.run_test() as pilot:
            contracts_table = app.query_one("#contracts-table")
            contracts_table.add_row("✅", "test-contract", "ST123...", key="ST123.test-contract")
            await pilot.pause()

            # Simulate the row selection event
            app.on_contracts_row_selected(
                contracts_table.RowSelected(
                    data_table=contracts_table,
                    row_key=RowKey("ST123.test-contract"),
                    cursor_row=0
                )
            )
            await pilot.pause()

            # Assert
            mock_fetch.assert_called_once_with("ST123.test-contract")

@pytest.mark.asyncio
async def test_validation_error_messages():
    """Test that validation error messages appear for invalid input."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        # Test Stacks Address validation
        address_input = app.query_one("#address-input")
        address_error = app.query_one("#address-error")

        # Invalid address
        address_input.value = "invalid-address"
        # Manually trigger the event since pilot.type might be slow or tricky in some environments
        app.on_address_changed(address_input.Changed(address_input, "invalid-address"))
        # PALETTE: Updated to match new error message format
        assert "❌ Must be 28-41 chars" in str(address_error.render())

        # Valid address (ST for testnet)
        address_input.value = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        app.on_address_changed(address_input.Changed(address_input, address_input.value))
        assert "✅ Valid" in str(address_error.render())

        # Test Private Key validation
        privkey_input = app.query_one("#privkey-input")
        privkey_error = app.query_one("#privkey-error")

        # Invalid private key
        privkey_input.value = "too-short"
        app.on_privkey_changed(privkey_input.Changed(privkey_input, "too-short"))
        assert "❌ Must be a 64 or 66 character hex string" in str(privkey_error.render())

        # Valid private key
        privkey_input.value = "a" * 64
        app.on_privkey_changed(privkey_input.Changed(privkey_input, privkey_input.value))
        assert "✅ Valid" in str(privkey_error.render())

@pytest.mark.asyncio
async def test_transaction_selection_enables_buttons():
    """Verify that selecting a transaction enables the action buttons."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        transactions_table = app.query_one("#transactions-table")
        copy_btn = app.query_one("#copy-selected-tx-btn")
        explorer_btn = app.query_one("#view-selected-tx-explorer-btn")
        status_label = app.query_one("#tx-status-label")

        # Initial state: disabled
        assert copy_btn.disabled is True
        assert explorer_btn.disabled is True
        assert "Select a transaction" in str(status_label.render())

        # Simulate transaction data for the Bolt ⚡ optimization logic
        app._last_transactions = [{"tx_id": "0x1234567890abcdef"}]

        # Add a row to the table
        transactions_table.add_row("0x1234...", "token-transfer", "success", "100", key="0x1234567890abcdef")
        await pilot.pause()

        # Simulate the row selection event
        app.on_transactions_row_selected(
            transactions_table.RowSelected(
                data_table=transactions_table,
                row_key=RowKey("0x1234567890abcdef"),
                cursor_row=0
            )
        )
        await pilot.pause()

        # Assert: buttons are enabled and label is updated
        assert copy_btn.disabled is False
        assert explorer_btn.disabled is False
        assert "0x1234567890abcd" in str(status_label.render())
        assert app.selected_tx_id == "0x1234567890abcdef"

@pytest.mark.asyncio
async def test_validation_includes_char_count():
    """Verify that validation labels include character count feedback."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        address_input = app.query_one("#address-input")
        address_error = app.query_one("#address-error")

        # Test with some text (invalid)
        test_address = "ST123"
        address_input.value = test_address
        app.on_address_changed(address_input.Changed(address_input, test_address))
        assert f"({len(test_address)}/41)" in str(address_error.render())
        assert "❌" in str(address_error.render())
        assert "28-41 chars" in str(address_error.render())

        # Test valid address
        valid_address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        address_input.value = valid_address
        app.on_address_changed(address_input.Changed(address_input, valid_address))
        assert f"({len(valid_address)}/41)" in str(address_error.render())
        assert "✅ Valid" in str(address_error.render())

        # Test Private Key
        privkey_input = app.query_one("#privkey-input")
        privkey_error = app.query_one("#privkey-error")

        test_pk = "abc"
        privkey_input.value = test_pk
        app.on_privkey_changed(privkey_input.Changed(privkey_input, test_pk))
        assert f"({len(test_pk)}/64 or 66)" in str(privkey_error.render())

        # Test valid private key
        valid_pk = "a" * 64
        privkey_input.value = valid_pk
        app.on_privkey_changed(privkey_input.Changed(privkey_input, valid_pk))
        assert f"({len(valid_pk)}/64 or 66)" in str(privkey_error.render())
        assert "✅ Valid" in str(privkey_error.render())

@pytest.mark.asyncio
async def test_wallet_connect_button_triggers_worker():
    """Verify that clicking the wallet connect button triggers the worker."""
    app = StacksOrbitGUI()
    with patch("wallet_connect.start_wallet_connect_server", return_value="ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM") as mock_server:
        async with app.run_test() as pilot:
            # Switch to settings tab
            await pilot.press("f5")
            await pilot.pause()

            connect_btn = app.query_one("#connect-wallet-btn")
            address_input = app.query_one("#address-input")

            # Click the button
            await pilot.click("#connect-wallet-btn")
            # The worker runs start_wallet_connect_server in a thread
            # We need to wait for it to complete.
            # Since we mocked it to return immediately, it should be fast.
            await pilot.pause(1.0)

            # Assert server was called
            mock_server.assert_called_once()
            # Assert UI was updated
            assert address_input.value == "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
            assert app.address == "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
