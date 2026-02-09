# Palette's UX Journal

## 2025-05-14 - Inline Validation Feedback
**Learning:** In Textual TUIs, providing real-time validation feedback through dedicated Label widgets using Rich markup ([red]) is a highly effective way to improve usability without needing custom CSS. This provides immediate, actionable guidance to the user.
**Action:** Use 'markup=True' on Labels for error messages and update them in 'Input.Changed' handlers to provide specific feedback on format, length, and prefixes.
