import pytest
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import Log, Button, LoadingIndicator, DataTable


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


@pytest.mark.asyncio
async def test_new_ux_enhancements():
    """Verify new UX enhancements like tooltips, indicators, and variants."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        # 1. Verify multiple loading indicators
        indicators = app.query(LoadingIndicator)
        assert (
            len(indicators) >= 3
        )  # Overview, Contracts, Transactions, Deployment

        # 2. Verify tooltips set in on_mount
        contracts_table = app.query_one("#contracts-table", DataTable)
        assert contracts_table.tooltip == "List of contracts deployed by this address"

        transactions_table = app.query_one("#transactions-table", DataTable)
        assert transactions_table.tooltip == "Recent transactions for this address"

        # 3. Verify Refresh button tooltip with shortcut hint
        refresh_btn = app.query_one("#refresh-btn", Button)
        assert "[r]" in str(refresh_btn.tooltip)

        # 4. Verify Clear button variant
        clear_btn = app.query_one("#clear-log-btn", Button)
        assert clear_btn.variant == "error"
