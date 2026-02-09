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
        assert "❌ Must be 41 chars" in str(address_error.render())

        # Valid address (ST for testnet)
        address_input.value = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        app.on_address_changed(address_input.Changed(address_input, address_input.value))
        assert str(address_error.render()) == ""

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
        assert str(privkey_error.render()) == ""
