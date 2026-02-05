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

## 2025-02-03 - Event Handler Naming and Collisions in Textual
**Learning:** In Textual, naming an event handler with a generic pattern like `on_data_table_row_selected` makes it a global listener for that event across all instances of that widget class. If you also use the `@on` decorator with a specific ID, both the generic handler and the decorated handler may fire, or it may cause unexpected behavior.
**Action:** Always use specific, unique names for event handlers (e.g., `on_contracts_row_selected`) when using the `@on` decorator with an ID selector to avoid collisions with automatic generic handler discovery.

## 2024-05-25 - Robust Visual Feedback in TUIs
**Learning:** When implementing temporary visual feedback (e.g., changing a button label to '✅' for 1 second) in a Textual TUI, avoid saving the 'original' label in a variable if the handler can be triggered multiple times quickly. If the user clicks during the feedback period, the variable might capture the '✅' label, causing the button to get stuck in that state.
**Action:** Use a hardcoded restoration value for the label (e.g., returning to '📋' or 'Copy') or check the current label state before starting the feedback timer to ensure the UI remains consistent.
