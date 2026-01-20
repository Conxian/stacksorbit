## 2024-05-23 - Robust Async Button States

**Learning:** When a button triggers a long-running asynchronous operation in a Textual app, it is critical to provide immediate feedback by disabling the button and changing its label. More importantly, the original state *must* be restored in a `try...finally` block to prevent the UI from getting stuck if the async operation fails unexpectedly. Saving the button's original label *before* changing it is the key to correct state restoration.

**Action:** For all future async operations tied to a button, I will apply this pattern:
1. Save the button's original label.
2. Disable the button and set its label to an "in-progress" state (e.g., "Loading...").
3. Wrap the async call in a `try...finally` block.
4. In the `finally` block, restore the original label and re-enable the button.
