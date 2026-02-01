import pytest
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import Log, Button


@pytest.mark.asyncio
async def test_clear_log_functionality():
    """Verify that the Clear button exists and clears the log."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        # Check Clear button existence and tooltip
        clear_btn = app.query_one("#clear-log-btn", Button)
        assert clear_btn.tooltip == "Clear the deployment log"

        # Switch to deployment tab
        app.query_one("TabbedContent").active = "deployment"
        await pilot.pause()

        log = app.query_one("#deployment-log", Log)
        log.write("Test line")
        await pilot.pause()

        # Verify log is NOT empty
        assert len(log.lines) > 0

        # Press clear button
        await pilot.click("#clear-log-btn")
        await pilot.pause()

        # Verify log IS empty
        assert len(log.lines) == 0
