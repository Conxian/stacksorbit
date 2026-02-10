# Palette's UX Journal

## 2025-05-14 - Inline Validation Feedback
**Learning:** In Textual TUIs, providing real-time validation feedback through dedicated Label widgets using Rich markup ([red]) is a highly effective way to improve usability without needing custom CSS. This provides immediate, actionable guidance to the user.
**Action:** Use 'markup=True' on Labels for error messages and update them in 'Input.Changed' handlers to provide specific feedback on format, length, and prefixes.

## 2025-05-15 - Visual Feedback for Clipboard Actions
**Learning:** In Textual TUIs, changing a button's label to a '✅' checkmark for a short duration (e.g., 1 second using asyncio.sleep) provides highly effective and satisfying feedback for background actions like "Copy to Clipboard" that otherwise lack visible results.
**Action:** Implement temporary label changes with 'asyncio.sleep' in button handlers for non-disruptive confirmation of success.
