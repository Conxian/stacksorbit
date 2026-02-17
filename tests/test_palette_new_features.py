import pytest
import asyncio
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import TabbedContent, Switch, Label, Static
from textual.events import Click

@pytest.mark.asyncio
async def test_dashboard_metric_navigation():
    """Verify that clicking dashboard metric cards navigates to the correct tabs."""
    app = StacksOrbitGUI()
    # Increase screen height to ensure metrics are within bounds
    async with app.run_test(size=(120, 100)) as pilot:
        tabs = app.query_one(TabbedContent)

        # 1. Click Contracts metric
        await pilot.click("#metric-contracts")
        await pilot.pause()
        assert tabs.active == "contracts"

        # 2. Click Balance metric (should go to transactions)
        # First switch back to overview
        tabs.active = "overview"
        await pilot.pause()
        await pilot.click("#metric-balance")
        await pilot.pause()
        assert tabs.active == "transactions"

        # 3. Click Nonce metric
        tabs.active = "overview"
        await pilot.pause()
        await pilot.click("#metric-nonce")
        await pilot.pause()
        assert tabs.active == "transactions"

@pytest.mark.asyncio
async def test_settings_label_toggle():
    """Verify that clicking the 'Show' label toggles the private key switch."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        # Switch to settings tab
        app.query_one(TabbedContent).active = "settings"
        await pilot.pause()

        priv_switch = app.query_one("#show-privkey", Switch)
        initial_state = priv_switch.value

        # Click the label
        await pilot.click("#show-privkey-label")
        await pilot.pause()

        assert priv_switch.value != initial_state

@pytest.mark.asyncio
async def test_metric_tooltips():
    """Verify that new clickable metrics have appropriate tooltips."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        assert "deployed contracts" in app.query_one("#metric-contracts").tooltip.lower()
        assert "transaction history" in app.query_one("#metric-balance").tooltip.lower()
        assert "private key" in app.query_one("#show-privkey-label").tooltip.lower()
