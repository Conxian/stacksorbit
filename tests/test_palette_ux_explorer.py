import pytest
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import Button
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_explorer_buttons_exist():
    """Verify that the new explorer and copy-source buttons exist and have correct tooltips."""
    app = StacksOrbitGUI()
    # Mock monitor to avoid API calls during app startup
    app.monitor = MagicMock()
    app.monitor.check_api_status.return_value = {"status": "online", "block_height": 100}
    app.monitor.get_account_info.return_value = {"balance": "0", "nonce": 0}
    app.monitor.get_deployed_contracts.return_value = []
    app.monitor.get_recent_transactions.return_value = []

    async with app.run_test() as pilot:
        # Check if buttons are present
        copy_source_btn = app.query_one("#copy-source-btn", Button)
        view_explorer_btn = app.query_one("#view-explorer-btn", Button)

        assert copy_source_btn is not None
        assert view_explorer_btn is not None

        # Check tooltips
        assert copy_source_btn.tooltip == "Copy contract source code"
        assert view_explorer_btn.tooltip == "View contract on Hiro Explorer"

        # Check initial state (should be disabled)
        assert copy_source_btn.disabled is True
        assert view_explorer_btn.disabled is True

@pytest.mark.asyncio
async def test_buttons_enable_on_selection():
    """Verify that the buttons enable when a contract is selected."""
    app = StacksOrbitGUI()
    # Mock the monitor to avoid real API calls and provide valid data for UI
    app.monitor = MagicMock()
    app.monitor.check_api_status.return_value = {"status": "online", "block_height": 100}
    app.monitor.get_account_info.return_value = {"balance": "0", "nonce": 0}
    app.monitor.get_deployed_contracts.return_value = []
    app.monitor.get_recent_transactions.return_value = []
    app.monitor.get_contract_details.return_value = {"source_code": "(define-public (hello) (ok u1))"}

    async with app.run_test() as pilot:
        # For this test, we'll manually call the handler with a mock event
        mock_event = MagicMock()
        mock_event.row_key.value = "ST1PQ.placeholder"

        app.on_contracts_row_selected(mock_event)

        assert app.query_one("#copy-source-btn", Button).disabled is False
        assert app.query_one("#view-explorer-btn", Button).disabled is False
        assert app.selected_contract_id == "ST1PQ.placeholder"

        # Wait for workers to finish
        await pilot.pause()
        assert app.current_source_code == "(define-public (hello) (ok u1))"
