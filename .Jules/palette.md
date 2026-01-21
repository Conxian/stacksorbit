## 2024-05-24 - Async Button Feedback in Textual

**Learning:** When a Textual button triggers a long-running, non-`async` background task (like a `subprocess`), it's crucial to provide immediate UI feedback. The best pattern is to disable the button, change its label to indicate a "loading" state, and wrap the state-restoring logic in a `try...finally` block. This ensures the UI is never left in an inconsistent state, even if the background task fails.

**Action:** Apply this disable/label/`try-finally` pattern to any future buttons that trigger synchronous, blocking operations in a separate thread. This makes the TUI feel responsive and prevents duplicate actions.
