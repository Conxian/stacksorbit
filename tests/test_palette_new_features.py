
import pytest
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import Static, DataTable
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_relative_time_formatting():
    app = StacksOrbitGUI()

    # Test 'Pending'
    assert app._format_relative_time(None) == "[yellow]Pending[/]"

    # Test 'Just now'
    now_iso = datetime.now().isoformat() + "Z"
    assert app._format_relative_time(now_iso) == "Just now"

    # Test '5m ago'
    five_m_ago = (datetime.now() - timedelta(minutes=5)).isoformat() + "Z"
    assert "5m ago" == app._format_relative_time(five_m_ago)

    # Test '2h ago'
    two_h_ago = (datetime.now() - timedelta(hours=2)).isoformat() + "Z"
    assert "2h ago" == app._format_relative_time(two_h_ago)

    # Test '1d ago'
    one_d_ago = (datetime.now() - timedelta(days=1)).isoformat() + "Z"
    assert "1d ago" == app._format_relative_time(one_d_ago)

@pytest.mark.asyncio
async def test_clickable_address():
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        display_address = app.query_one("#display-address", Static)
        assert "clickable-label" in display_address.classes
        assert display_address.tooltip == "Click to copy your Stacks address"

        # Verify Click handler exists (calling it doesn't crash)
        await pilot.click("#display-address")

@pytest.mark.asyncio
async def test_transactions_table_columns():
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        table = app.query_one("#transactions-table", DataTable)
        # Verify column count including new 'Time' column
        assert len(table.columns) == 5
