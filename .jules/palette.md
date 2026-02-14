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

## 2025-05-17 - Interactive Dashboard Metrics and Label Toggling
**Learning:** In a Textual TUI, making informational metric cards clickable to navigate between tabs significantly enhances discoverability and intuition. Similarly, making labels for toggles (like switches) clickable mirrors familiar web accessibility patterns and improves ease of use. Using emojis and colorized statuses in data tables drastically improves scannability for complex technical data.
**Action:** Always consider if summary metrics can serve as navigation shortcuts to detail views. Ensure form labels are clickable where possible to toggle their associated inputs.

## 2025-05-18 - Immediate UI Synchronization for Primary Identity
**Learning:** For primary user identity elements (like the Stacks Address), providing a high-visibility, persistent display on the main dashboard (rather than hiding it in Settings) drastically reduces user friction. When this identity is updated in settings, performing "immediate UI synchronization" across all active tabs ensures the user feels in control and avoids confusion from stale data.
**Action:** Identify primary identity or state elements and promote them to the main dashboard. Always synchronize these elements immediately across the UI when they are modified in specialized settings views.
