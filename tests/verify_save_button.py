
import asyncio
from pathlib import Path
import os
from stacksorbit_gui import StacksOrbitGUI

async def main():
    """
    Verification script to test the 'Saved!' button state using Textual's Pilot.
    """
    # 🎨 Palette: This verification script tests the new "Saved!" button state.
    # It navigates to the Settings tab, clicks Save, and captures a screenshot.
    app = StacksOrbitGUI()

    async with app.run_test() as pilot:
        # Ensure the CSS path is correct, as the script runs from the repo root
        pilot.app.CSS_PATH = Path("stacksorbit_gui.tcss").resolve()

        # Create a dummy .env file for the test
        with open(".env.test_palette", "w") as f:
            f.write("DEPLOYER_PRIVKEY=\n")
            f.write("SYSTEM_ADDRESS=\n")
        pilot.app.config_path = ".env.test_palette"

        # Switch to the Settings tab by pressing the right arrow key multiple times
        await pilot.press("right", "right", "right", "right")
        await pilot.pause(0.1) # Allow UI to update

        # Click the save button
        await pilot.click("#save-config-btn")

        # Wait for the "Saved!" state to appear
        await pilot.pause(0.5)

        # Capture a screenshot
        screenshot_path = "palette-ux-after.svg"
        pilot.app.save_screenshot(filename=screenshot_path, path=".")
        print(f"Screenshot saved to {screenshot_path}")

        # Clean up the dummy .env file
        os.remove(".env.test_palette")

if __name__ == "__main__":
    asyncio.run(main())
