# Palette's UX Journal

## 2025-05-14 - Inline Validation Feedback
**Learning:** In Textual TUIs, providing real-time validation feedback through dedicated Label widgets using Rich markup ([red]) is a highly effective way to improve usability without needing custom CSS. This provides immediate, actionable guidance to the user.
**Action:** Use 'markup=True' on Labels for error messages and update them in 'Input.Changed' handlers to provide specific feedback on format, length, and prefixes.

## 2025-05-15 - Visual Feedback for Copy Actions
**Learning:** For icon-only buttons in a TUI, temporary label changes (e.g., from 📋 to ✅) provide excellent immediate feedback for non-visual and visual users alike when combined with notifications. It's a reusable pattern for any "copy to clipboard" functionality.
**Action:** Implement copy handlers with an async delay (asyncio.sleep) to revert the icon label, ensuring the user sees the success state clearly.

## 2025-05-16 - Contextual Transaction Action Bar
**Learning:** A "Transaction Action Bar" pattern (Horizontal container below a DataTable) is an excellent way to provide contextual deep-links (Explorer) and utility actions (Copy ID) without cluttering the table rows. Using a status label in the bar helps confirm which item is selected in truncated views.
**Action:** When displaying complex identifiers in a table, implement a contextual action bar with status feedback to enable detailed interactions without row-level complexity.
