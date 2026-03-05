
import os
import pytest
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import Static, DataTable
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_relative_time_formatting():
    from datetime import timezone
    app = StacksOrbitGUI()
    now_utc = datetime.now(timezone.utc)
    now_bucket = int(now_utc.timestamp() / 10) * 10

    # Test 'Pending'
    assert app._format_relative_time(None, now_bucket) == "[yellow]Pending[/]"

    # Test 'Just now'
    now_iso = now_utc.isoformat().replace("+00:00", "Z")
    assert "Just now" in app._format_relative_time(now_iso, now_bucket)

    # Test '5m ago'
    five_m_ago = (now_utc - timedelta(minutes=5, seconds=5)).isoformat().replace("+00:00", "Z")
    res = app._format_relative_time(five_m_ago, now_bucket)
    assert "m ago" in res or "Just now" in res

    # Test '2h ago'
    two_h_ago = (now_utc - timedelta(hours=2, seconds=5)).isoformat().replace("+00:00", "Z")
    res = app._format_relative_time(two_h_ago, now_bucket)
    assert "h ago" in res

    # Test '1d ago'
    one_d_ago = (now_utc - timedelta(days=1, hours=1)).isoformat().replace("+00:00", "Z")
    res = app._format_relative_time(one_d_ago, now_bucket)
    assert "d ago" in res

@pytest.mark.asyncio
async def test_clickable_address():
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        display_address = app.query_one("#display-address", Static)
        assert "clickable-label" in display_address.classes
        assert display_address.tooltip == "Click to copy your Stacks address [c]"

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

@pytest.mark.asyncio
async def test_unsaved_changes_feedback(monkeypatch):
    from textual.widgets import Button, Input
    # Mock save_secure_config to avoid actual file IO
    monkeypatch.setattr("stacksorbit_gui.save_secure_config", lambda *args, **kwargs: None)

    app = StacksOrbitGUI(config_path=".env.test")
    async with app.run_test() as pilot:
        save_btn = app.query_one("#save-config-btn", Button)
        address_input = app.query_one("#address-input", Input)

        # Use a valid address to ensure validation passes
        valid_addr = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        address_input.value = valid_addr
        app.unsaved_changes = False # reset after programmatic set

        # Initial state
        assert app.unsaved_changes is False

        # Simulate user input
        address_input.focus()
        await pilot.press("backspace")
        await pilot.press("M")

        assert app.unsaved_changes is True

        # Directly reset it to test reactive property if handler is tricky in test
        app.unsaved_changes = False
        assert save_btn.variant == "primary"

        # Trigger it again
        address_input.focus()
        await pilot.press("backspace")
        await pilot.press("M")
        assert app.unsaved_changes is True

        # Reset and check
        app.unsaved_changes = False
        assert save_btn.variant == "primary"

    if os.path.exists(".env.test"):
        os.remove(".env.test")

@pytest.mark.asyncio
async def test_show_hide_privkey_label_toggle():
    from textual.widgets import Switch, Label
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        label = app.query_one("#show-privkey-label", Label)
        switch = app.query_one("#show-privkey", Switch)

        # Initial state
        assert str(label.render()) == "Show"

        # Programmatically trigger the handler since pilot.focus is missing
        # and we want to verify the UI logic
        app.on_show_privkey_changed(Switch.Changed(switch, True))
        assert str(label.render()) == "Hide"

        app.on_show_privkey_changed(Switch.Changed(switch, False))
        assert str(label.render()) == "Show"

@pytest.mark.asyncio
async def test_transaction_confirmations_and_highlighting():
    from unittest.mock import MagicMock
    app = StacksOrbitGUI()
    app.address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"

    async with app.run_test() as pilot:
        # Mock transaction data
        tx_id = "0x" + "a" * 64
        transactions = [{
            "tx_id": tx_id,
            "tx_type": "contract_call",
            "tx_status": "success",
            "burn_block_time_iso": "2023-01-01T00:00:00Z",
            "block_height": 100
        }]
        app._all_transactions = transactions
        app.current_block_height = 105

        # Refresh table
        app._update_transactions_table()

        table = app.query_one("#transactions-table", DataTable)
        # Check that row was added
        assert table.row_count == 1

        # Check confirmation count calculation (105 - 100 + 1 = 6)
        row_data = table.get_row(tx_id)
        # Block column is index 4
        assert "(6)" in str(row_data[4])

        # Test highlighting fluid update
        # RowHighlighted is nested under DataTable
        # Simulate highlight event
        from textual.widgets._data_table import RowKey
        app.on_transactions_row_highlighted(DataTable.RowHighlighted(table, table.get_row_index(tx_id), RowKey(tx_id)))
        assert app.selected_tx_id == tx_id
        assert not app.w_copy_tx_btn.disabled
        assert "(6)" in str(app.w_tx_status_label.render()) or "Selected" in str(app.w_tx_status_label.render())
