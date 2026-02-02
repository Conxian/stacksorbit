## 2024-05-23 - Robust Async Button States

**Learning:** When a button triggers a long-running asynchronous operation in a Textual app, it is critical to provide immediate feedback by disabling the button and changing its label. More importantly, the original state *must* be restored in a `try...finally` block to prevent the UI from getting stuck if the async operation fails unexpectedly. Saving the button's original label *before* changing it is the key to correct state restoration.

**Action:** For all future async operations tied to a button, I will apply this pattern:
1. Save the button's original label.
2. Disable the button and set its label to an "in-progress" state (e.g., "Loading...").
3. Wrap the async call in a `try...finally` block.
4. In the `finally` block, restore the original label and re-enable the button.

## 2024-05-24 - TUI Accessibility and Clarity
**Learning:** In terminal-based UIs (Textual), tooltips and explicit focus states are vital for accessibility. Tooltips provide essential context for emoji-heavy buttons without cluttering the layout. A clear focus state (e.g., changing border color on :focus) is necessary for keyboard-only navigation to ensure the user always knows their current position.
**Action:** I will always include tooltips for icon/emoji buttons and define explicit :focus styles in TCSS for interactive elements.

## 2025-02-01 - Widget-Specific Tooltip Limitations in Textual
**Learning:** While the 'tooltip' attribute is a property of the base 'Widget' class in Textual, not all built-in widgets (like 'DataTable') accept it as a keyword argument in their '__init__' method. Attempting to do so results in a 'TypeError'.
**Action:** For widgets that do not support 'tooltip' in their constructor, I will set the property programmatically in the 'on_mount' method or after instantiation.

## 2025-02-02 - Multi-Tab Loading States and Empty States
**Learning:** In a multi-tabbed TUI, providing consistent loading feedback across all data-driven tabs is essential. If only one tab shows a loading indicator during a global refresh, users on other tabs may perceive the app as frozen. Additionally, providing explicit "No data found" rows in tables prevents the "is it still loading or is it empty?" confusion.
**Action:** I will implement global loading management by querying all loading indicators and provide meaningful empty-state rows for all data tables.
