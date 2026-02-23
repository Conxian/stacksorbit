
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

@pytest.mark.asyncio
async def test_balance_colorization():
    from unittest.mock import MagicMock
    app = StacksOrbitGUI()
    # Set a dummy address so it attempts to fetch account info
    app.address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"

    # Use run_test to ensure app is mounted
    async with app.run_test() as pilot:
        # We can test the update_data logic by mocking the monitor and checking _last_metrics
        app.monitor = MagicMock()
        app.monitor.check_api_status.return_value = {"status": "online", "block_height": 100}
        # Clear the cache tracking so it actually updates
        app._last_metrics = {}

        # Test healthy balance (Green)
        app.monitor.get_account_info = MagicMock(return_value={"balance": 2000000, "nonce": 5})
        app.monitor.get_deployed_contracts = MagicMock(return_value=[])
        app.monitor.get_recent_transactions = MagicMock(return_value=[])

        await app.update_data()
        assert "[green]2.000000 STX[/]" in app._last_metrics["balance"]

        # Test low balance (Yellow)
        app.monitor.get_account_info.return_value = {"balance": 500000, "nonce": 5}
        await app.update_data()
        assert "[yellow]0.500000 STX[/]" in app._last_metrics["balance"]

        # Test empty balance (Red)
        app.monitor.get_account_info.return_value = {"balance": 0, "nonce": 5}
        await app.update_data()
        assert "[red]0.000000 STX[/]" in app._last_metrics["balance"]

@pytest.mark.asyncio
async def test_settings_focus_on_tab_change():
    from textual.widgets import TabbedContent, Tab
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        # Switch to settings tab via shortcut key which triggers action_switch_tab
        await pilot.press("f5")

        # Give some time for the message to be processed and focus to change
        await pilot.pause(0.5)

        # Check if privkey-input is focused
        assert app.focused is not None
        assert app.focused.id == "privkey-input"
