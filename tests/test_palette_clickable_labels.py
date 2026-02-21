import pytest
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import Label, Input

@pytest.mark.asyncio
async def test_palette_clickable_labels_and_tooltips():
    """Verify the new clickable labels, tooltips, and interactive metrics."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        # Check Dashboard System Address label tooltip
        address_label = app.query_one("#system-address-label", Label)
        assert address_label is not None
        assert address_label.tooltip == "Your active Stacks address for deployments"

        # Check Settings labels IDs and classes
        privkey_label = app.query_one("#privkey-label", Label)
        assert privkey_label is not None
        assert "clickable-label" in privkey_label.classes
        assert privkey_label.tooltip == "Click to focus private key input"

        address_input_label = app.query_one("#address-label", Label)
        assert address_input_label is not None
        assert "clickable-label" in address_input_label.classes
        assert address_input_label.tooltip == "Click to focus address input"

        # Check interaction: Click privkey label to focus input
        await pilot.click("#privkey-label")
        assert app.focused.id == "privkey-input"

        # Check interaction: Click address label to focus input
        await pilot.click("#address-label")
        assert app.focused.id == "address-input"

        # Check interaction: Click metric card for network (triggers refresh)
        # We can't easily verify the refresh happened without mocking,
        # but we can verify the handler is called by checking if it doesn't crash
        # and checking the metric card exists.
        metric_network = app.query_one("#metric-network")
        assert metric_network is not None
        # Click it
        await pilot.click("#metric-network")
        # Should not crash.
