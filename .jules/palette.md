# Palette's UX Journal

## 2025-05-14 - Inline Validation Feedback
**Learning:** In Textual TUIs, providing real-time validation feedback through dedicated Label widgets using Rich markup ([red]) is a highly effective way to improve usability without needing custom CSS. This provides immediate, actionable guidance to the user.
**Action:** Use 'markup=True' on Labels for error messages and update them in 'Input.Changed' handlers to provide specific feedback on format, length, and prefixes.

## 2025-05-15 - Visual Feedback for Copy Actions
**Learning:** For icon-only buttons in a TUI, temporary label changes (e.g., from 📋 to ✅) provide excellent immediate feedback for non-visual and visual users alike when combined with notifications. It's a reusable pattern for any "copy to clipboard" functionality.
**Action:** Implement copy handlers with an async delay (asyncio.sleep) to revert the icon label, ensuring the user sees the success state clearly.
