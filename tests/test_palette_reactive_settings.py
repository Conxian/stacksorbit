
import pytest
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import Button, Input

@pytest.mark.asyncio
async def test_reactive_settings_buttons():
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        # Navigate to settings tab
        await pilot.press("f5")

        address_input = app.query_one("#address-input", Input)
        copy_btn = app.query_one("#copy-address-btn", Button)
        explorer_btn = app.query_one("#view-address-explorer-btn", Button)

        # Test 1: Empty address
        address_input.focus()
        while address_input.value:
            await pilot.press("backspace")

        await pilot.pause(0.1)
        assert copy_btn.disabled is True
        assert explorer_btn.disabled is True

        # Test 2: Valid address (Testnet)
        valid_address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        # Type the address
        for char in valid_address:
            await pilot.press(char)

        await pilot.pause(0.1)
        assert copy_btn.disabled is False
        assert explorer_btn.disabled is False

        # Test 3: Invalid address (too short)
        # Delete some chars
        for _ in range(15):
            await pilot.press("backspace")

        await pilot.pause(0.1)
        # Check current length to be sure it's invalid (< 28 chars)
        assert len(address_input.value) < 28
        assert copy_btn.disabled is False # Still has text
        assert explorer_btn.disabled is True # but invalid address

        # Test 4: Back to valid
        address_input.value = valid_address
        # Trigger manually if pilot.press isn't used
        app.on_address_changed(Input.Changed(address_input, valid_address))

        await pilot.pause(0.1)
        assert copy_btn.disabled is False
        assert explorer_btn.disabled is False

@pytest.mark.asyncio
async def test_reactive_dashboard_address_update():
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        display_address = app.query_one("#display-address")
        explorer_btn = app.query_one("#view-dashboard-explorer-btn")

        # Update address reactively
        new_addr = "ST21979EF7D8Y88A58W9YVDY6D380YF6SBYYPQY8B"
        app.address = new_addr
        await pilot.pause(0.1)

        # Check rendered text (Rich markup might be present)
        assert new_addr in str(display_address.render())
        assert explorer_btn.disabled is False

        # Update to unconfigured
        app.address = "Not configured"
        await pilot.pause(0.1)
        assert "Not configured" in str(display_address.render())
        assert explorer_btn.disabled is True
