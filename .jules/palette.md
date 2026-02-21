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

## 2025-05-19 - Real-time Character Counts for Strict Inputs
**Learning:** For inputs with strict length requirements (like Stacks addresses or private keys), displaying a real-time character count (e.g., (41/41)) directly in the feedback label significantly reduces user friction and anxiety. It allows users to catch typos or incomplete pastes immediately without waiting for a final validation check.
**Action:** Always include real-time character count indicators for any TUI input field that has a specific required length or range.

## 2025-05-20 - Constraining Loading Indicators for TUI Layout Stability
**Learning:** Standard Textual `LoadingIndicator` widgets can default to `height: 100%`, which may push all subsequent content out of the viewport if placed at the top of a layout. This not only ruins the UX by hiding the interface during initial load but also causes `OutOfBounds` errors in automated `pilot.click` tests.
**Action:** Always constrain `LoadingIndicator` height in CSS (e.g., `height: 3;`) to ensure it remains a localized feedback element rather than a layout-disrupting overlay.

## 2025-05-21 - Asynchronous Wallet Connect Integration
**Learning:** Integrating a web-based connection wizard directly into a TUI via an asynchronous background worker and thread-safe UI updates significantly reduces user friction by keeping the user within the main application flow. Using `asyncio.to_thread` for blocking operations (like an HTTP server) and `contextlib.redirect_stdout` to suppress background noise ensures the TUI remains responsive and visual integrity is maintained.
**Action:** For any external authentication or complex configuration tasks, provide a direct "Connect" or "Launch" button in the TUI that orchestrates the process asynchronously and updates the interface in real-time upon completion.

## 2025-05-22 - Context-Aware Utility Buttons
**Learning:** Adding context-aware utility buttons (like a "Faucet" link that only appears on Testnet) provides immediate value to specific user segments (developers) without cluttering the interface for others. Using specialized visual variants (like orange `.warning` for external links) creates a clear visual hierarchy and helps users distinguish between internal app actions and external transitions.
**Action:** Identify network-specific or state-specific utilities and implement them as dynamic UI elements. Use distinct visual styles for external links to manage user expectations about navigation.

## 2025-05-23 - Interactive Input Labels and Metric Cards
**Learning:** In a TUI, making text labels interactive by associating them with their respective inputs (e.g., clicking a "Private Key" label focuses the input field) significantly improves usability and accessibility. Similarly, making informational metric cards clickable to trigger common actions (like refreshing data) makes the dashboard feel more responsive and intuitive.
**Action:** Always assign IDs and 'clickable-label' classes to form labels, implementing focus handlers and hover styles to indicate interactivity. Consider if summary metrics can serve as shorthand triggers for related application actions.
