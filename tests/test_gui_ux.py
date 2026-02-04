import pytest
from unittest.mock import patch, MagicMock
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets.data_table import RowKey

@pytest.mark.asyncio
async def test_transaction_selection_copies_to_clipboard():
    """Verify selecting a transaction row copies the TX ID to clipboard."""
    app = StacksOrbitGUI()
    # Mock notify and copy_to_clipboard
    with patch.object(app, 'notify') as mock_notify, \
         patch.object(app, 'copy_to_clipboard') as mock_copy:

        async with app.run_test() as pilot:
            transactions_table = app.query_one("#transactions-table")
            tx_id = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

            # Manually add a row with a key
            transactions_table.add_row(
                tx_id[:10] + "...", "contract_call", "success", "123",
                key=tx_id
            )
            await pilot.pause()

            # Simulate the row selection event
            app.on_transactions_row_selected(
                transactions_table.RowSelected(
                    data_table=transactions_table,
                    row_key=RowKey(tx_id),
                    cursor_row=0
                )
            )
            await pilot.pause()

            # Assert
            mock_copy.assert_called_once_with(tx_id)
            mock_notify.assert_called_once()
            assert "Transaction ID copied" in mock_notify.call_args[0][0]
