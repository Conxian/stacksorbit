import pytest
import asyncio
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import Input, DataTable, Label, TabbedContent

async def mock_async_none(*args, **kwargs):
    return None

@pytest.mark.asyncio
async def test_tx_filtering_logic(monkeypatch):
    """Verify that the transaction filter correctly narrows down results."""
    # Disable background data fetching for clean testing
    monkeypatch.setattr("stacksorbit_gui.StacksOrbitGUI.update_data", mock_async_none)
    app = StacksOrbitGUI()
    app.address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"

    # Mock data
    mock_txs = [
        {"tx_id": "0x1234567890abcdef", "tx_type": "smart_contract", "tx_status": "success"},
        {"tx_id": "0xabcdef1234567890", "tx_type": "contract_call", "tx_status": "pending"},
        {"tx_id": "0x5555555555555555", "tx_type": "token_transfer", "tx_status": "failed"},
    ]

    async with app.run_test() as pilot:
        # Inject mock data
        app._all_transactions = mock_txs
        app._update_transactions_table()

        table = app.query_one("#transactions-table", DataTable)
        count_label = app.query_one("#tx-filter-count", Label)

        # Initial state (no filter)
        assert table.row_count == 3

        # Filter by ID
        app.tx_filter = "0x123"
        app._update_transactions_table()
        assert table.row_count == 1

        # Filter by Type
        app.tx_filter = "call"
        app._update_transactions_table()
        assert table.row_count == 1

        # Filter by Status
        app.tx_filter = "failed"
        app._update_transactions_table()
        assert table.row_count == 1

        # Filter with no matches
        app.tx_filter = "nonexistent"
        app._update_transactions_table()
        assert table.row_count == 1  # Should show the "No matches" row
        row = table.get_row_at(0)
        assert "No matches for 'nonexistent'" in str(row)

        # Clear filter
        app.tx_filter = ""
        app._update_transactions_table()
        assert table.row_count == 3

@pytest.mark.asyncio
async def test_tx_filter_focus_shortcut(monkeypatch):
    """Verify that the '/' shortcut focuses the filter input."""
    monkeypatch.setattr("stacksorbit_gui.StacksOrbitGUI.update_data", mock_async_none)
    app = StacksOrbitGUI()
    app.address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
    async with app.run_test() as pilot:
        # Navigate to a different tab first
        await pilot.press("f1")
        await pilot.pause()

        # Press '/'
        await pilot.press("/")
        # Wait a bit for messages to be processed
        await pilot.pause(0.5)

        # Check focus and tab
        assert app.query_one(TabbedContent).active == "transactions"
        # Check if focus is correct or will be soon
        if app.focused is None or app.focused.id != "tx-filter-input":
            await pilot.pause(0.5)

        assert app.focused is not None
        assert app.focused.id == "tx-filter-input"

@pytest.mark.asyncio
async def test_tx_filter_input_event(monkeypatch):
    """Verify that typing in the filter input updates the filter state."""
    monkeypatch.setattr("stacksorbit_gui.StacksOrbitGUI.update_data", mock_async_none)
    app = StacksOrbitGUI()
    # Set address before running to ensure it's picked up by reactive logic
    app.address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
    async with app.run_test() as pilot:
        # Set transactions BEFORE address to avoid empty table via watch_address
        app._all_transactions = [
            {"tx_id": "0x123", "tx_type": "call", "tx_status": "success"},
            {"tx_id": "0x456", "tx_type": "transfer", "tx_status": "success"},
        ]
        # Ensure the address is correctly set in the reactive state
        app.address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"

        # Navigate to transactions tab
        await pilot.press("f3")
        await pilot.pause()

        # Focus filter and type
        app.query_one("#tx-filter-input").focus()
        await pilot.press("t", "r", "a", "n", "s")
        # Ensure the event handler finished
        await pilot.pause(0.5)

        assert app.tx_filter == "trans"
        # Manually trigger update to ensure it's matched if the event was slow
        app._update_transactions_table()
        table = app.query_one("#transactions-table", DataTable)
        assert table.row_count == 1
        assert "transfer" in str(table.get_row_at(0))
