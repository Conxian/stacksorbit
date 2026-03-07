## 2025-05-15 - [Deployment Log Interaction]
**Learning:** Deployment logs in TUIs are often frustratingly ephemeral. Users want to share success or debug failures, but selecting text in a terminal-like widget is often clunky. Providing a dedicated 'Copy' button and shortcut that captures the raw stream (rather than the rendered Rich text) significantly lowers friction for troubleshooting.
**Action:** Always implement a raw-log buffer when using `textual.widgets.Log` to enable clean clipboard functionality.

## 2025-05-15 - [Keyboard Shortcut Consistency]
**Learning:** Standardizing keyboard shortcuts across tabs (e.g., 'c' for copy, 'p' for pre-check) makes the app feel cohesive. When 'c' was used for a command in one tab and copy in another, it created cognitive load.
**Action:** Reserve standard keys like 'c' for copy across all context-aware tabs to maintain a mental model of the interface.
