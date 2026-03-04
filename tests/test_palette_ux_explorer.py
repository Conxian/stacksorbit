import pytest
from unittest.mock import MagicMock
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import Button, DataTable
from textual.widgets.data_table import RowKey

@pytest.mark.asyncio
async def test_dashboard_navigation_from_metrics():
    """Verify that clicking dashboard metrics navigates to correct tabs."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        # Initial tab should be overview
        assert app.query_one("TabbedContent").active == "overview"

        # Click on contracts metric
        await pilot.click("#metric-contracts")
        assert app.query_one("TabbedContent").active == "contracts"

        # Go back to overview
        await pilot.press("f1")
        assert app.query_one("TabbedContent").active == "overview"

        # Click on balance metric
        await pilot.click("#metric-balance")
        assert app.query_one("TabbedContent").active == "transactions"

@pytest.mark.asyncio
async def test_buttons_enable_on_selection():
    """Verify that the buttons enable when a contract is highlighted."""
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

        app.on_contracts_row_highlighted(mock_event)

        assert app.query_one("#copy-source-btn", Button).disabled is False
        assert app.query_one("#view-explorer-btn", Button).disabled is False
        assert app.selected_contract_id == "ST1PQ.placeholder"

        # Wait for workers to finish
        await pilot.pause(1.0)
        assert app.current_source_code == "(define-public (hello) (ok u1))"
