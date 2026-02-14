import pytest
from unittest.mock import patch
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import Label, Static, Button

@pytest.mark.asyncio
async def test_dashboard_address_bar_exists():
    """Verify that the new address bar and its components exist in the Dashboard."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        address_bar = app.query_one("#address-bar")
        assert address_bar is not None
        assert "System Address:" in str(address_bar.query_one(Label).render())
        assert address_bar.query_one("#display-address", Static) is not None
        assert "📋" in str(address_bar.query_one("#copy-dashboard-address-btn", Button).label)

@pytest.mark.asyncio
async def test_network_status_dot():
    """Verify that the network status now includes a colored dot."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        await app.update_data()
        status_label = app.query_one("#network-status")
        assert "●" in str(status_label.render())

@pytest.mark.asyncio
async def test_address_synchronization():
    """Verify that saving settings updates the dashboard address display."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        new_address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        with patch("asyncio.to_thread", return_value=None):
            app.query_one("#address-input").value = new_address
            app.query_one("#privkey-input").value = ""
            await app.on_save_config_pressed()
        assert app.address == new_address
        assert str(app.query_one("#display-address", Static).render()) == new_address
