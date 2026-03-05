import asyncio
from stacksorbit_gui import StacksOrbitGUI
from textual.widgets import Button, Label

async def capture_screenshot():
    app = StacksOrbitGUI()
    async with app.run_test() as pilot:
        # Give it a moment to render
        await pilot.pause(0.5)

        # Capture the initial dashboard view
        app.save_screenshot("dashboard_shortcuts.svg")

        # Switch to Contracts tab
        await pilot.press("f2")
        await pilot.pause(0.5)
        app.save_screenshot("contracts_shortcuts.svg")

        # Switch to Transactions tab
        await pilot.press("f3")
        await pilot.pause(0.5)
        app.save_screenshot("transactions_shortcuts.svg")

        # Switch to Settings tab
        await pilot.press("f5")
        await pilot.pause(0.5)
        app.save_screenshot("settings_shortcuts.svg")

if __name__ == "__main__":
    asyncio.run(capture_screenshot())
