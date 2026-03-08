## 2025-03-08 - [Dashboard Metric Accessibility]
**Learning:** Custom 'metric card' containers in Textual (using `Container` or `Grid`) are not focusable by default. To make them keyboard-accessible, `can_focus = True` must be set explicitly in `on_mount`, and an `on_key` handler must be implemented to map 'enter' to their respective click actions. This ensures users with screen readers or keyboard-only setups can navigate and interact with dashboard summaries.
**Action:** Always audit custom UI components for focusability and provide `on_key` handlers for primary interactions (Enter/Space).

## 2025-03-08 - [Enhanced Copy Feedback]
**Learning:** While button-label changes (📋 -> ✅) provide some feedback, users often look at the data they are copying. Providing feedback directly on the label containing the data (e.g., "Copied to clipboard!") provides more immediate and contextual confirmation of the action.
**Action:** Use a temporary label update pattern alongside button changes for high-intent copy actions.
