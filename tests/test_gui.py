import pytest
from unittest.mock import patch, AsyncMock
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets.data_table import RowKey

@pytest.mark.asyncio
async def test_gui_launches():
    """Test that the GUI launches without errors."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        assert pilot is not None
        await pilot.press("q")

@pytest.mark.asyncio
async def test_contract_selection_triggers_details_fetch():
    """Verify selecting a contract triggers the details fetch."""
    app = StacksOrbitGUI()
    with patch.object(app, 'fetch_contract_details', new_callable=AsyncMock) as mock_fetch:
        async with app.run_test() as pilot:
            contracts_table = app.query_one("#contracts-table")
            contracts_table.add_row("✅", "test-contract", "ST123...", key="ST123.test-contract")
            await pilot.pause()

            # Simulate the row selection event
            app.on_data_table_row_selected(
                contracts_table.RowSelected(
                    data_table=contracts_table,
                    row_key=RowKey("ST123.test-contract"),
                    cursor_row=0
                )
            )
            await pilot.pause()

            # Assert
            mock_fetch.assert_called_once_with("ST123.test-contract")
