import pytest
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import Input

@pytest.mark.asyncio
async def test_tx_clear_filter_functionality():
    """Verify that the clear filter button and ESC key work as expected."""
    app = StacksOrbitGUI()
    app.address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"

    async with app.run_test() as pilot:
        await pilot.press("f3") # Switch to transactions tab

        filter_input = app.query_one("#tx-filter-input", Input)
        clear_btn = app.query_one("#clear-tx-filter-btn")

        # Initially hidden
        assert clear_btn.display is False

        # Type something
        await pilot.click("#tx-filter-input")
        await pilot.press("t", "e", "s", "t")
        assert app.tx_filter == "test"
        assert clear_btn.display is True

        # Click clear button
        await pilot.click("#clear-tx-filter-btn")
        assert filter_input.value == ""
        assert app.tx_filter == ""
        assert clear_btn.display is False
        assert app.focused == filter_input

        # Test ESC key
        await pilot.press("a", "b", "c")
        assert filter_input.value == "abc"
        assert clear_btn.display is True

        await pilot.press("escape")
        assert filter_input.value == ""
        assert clear_btn.display is False
