import pytest
from stacksorbit_gui import StacksOrbitGUI

@pytest.mark.asyncio
async def test_gui_launches():
    """Test that the GUI launches without errors."""
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        assert pilot is not None
        await pilot.press("q")
