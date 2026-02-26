#!/usr/bin/env python3
"""
StacksOrbit GUI - A modern, feature-rich dashboard for Stacks blockchain deployment
"""

import asyncio
import os
import subprocess
import threading
import webbrowser
from datetime import datetime, timezone
import functools
from typing import Dict, List

try:
    from textual.app import App, ComposeResult
    from textual.widgets import (
        Header,
        Footer,
        DataTable,
        Static,
        Button,
        TabPane,
        TabbedContent,
        Label,
        Input,
        Log,
        Switch,
        LoadingIndicator,
        Markdown,
    )
    from textual.containers import Container, Horizontal, Vertical, VerticalScroll, Grid
    from textual.reactive import reactive
    from textual.binding import Binding
    from textual.events import Click
    from textual import on

    GUI_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    GUI_AVAILABLE = False

from deployment_monitor import DeploymentMonitor

@functools.lru_cache(maxsize=128)
def _parse_iso_to_dt(iso_time: str) -> datetime:
    """Bolt ⚡: Cached ISO parsing to avoid redundant expensive fromisoformat calls."""
    # Handle 'Z' for older Python versions and parse ISO string
    ts = iso_time.replace("Z", "+00:00")
    return datetime.fromisoformat(ts)


@functools.lru_cache(maxsize=1024)
def _format_relative_time_cached(iso_time: str, now_bucket: int) -> str:
    """Bolt ⚡: Cached relative time formatting to minimize O(N) timedelta math in loops."""
    try:
        dt = _parse_iso_to_dt(iso_time)
        now = datetime.fromtimestamp(now_bucket, tz=timezone.utc)
        diff = now - dt

        if diff.total_seconds() < 0:  # Future (can happen in dev/test)
            return "Just now"
        if diff.days > 0:
            return f"{diff.days}d ago"
        if diff.seconds >= 3600:
            return f"{diff.seconds // 3600}h ago"
        if diff.seconds >= 60:
            return f"{diff.seconds // 60}m ago"
        return "Just now"
    except Exception:
        return "N/A"
from stacksorbit_secrets import (
    SECRET_KEYS,
    is_sensitive_key,
    is_sensitive_value,
    is_placeholder,
    validate_stacks_address,
    validate_private_key,
    set_secure_permissions,
    save_secure_config,
)


class StacksOrbitGUI(App):
    """A Textual dashboard for StacksOrbit."""

    CSS_PATH = "stacksorbit_gui.tcss"

    BINDINGS = [
        Binding("d", "toggle_dark", "Toggle dark mode"),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("s", "save_settings", "Save", show=True),
        Binding("f1", "switch_tab('overview')", "Dashboard", show=True),
        Binding("f2", "switch_tab('contracts')", "Contracts", show=True),
        Binding("f3", "switch_tab('transactions')", "Transactions", show=True),
        Binding("f4", "switch_tab('deployment')", "Deploy", show=True),
        Binding("f5", "switch_tab('settings')", "Settings", show=True),
    ]

    # Reactive variables
    network = reactive("testnet")
    unsaved_changes = reactive(False)

    def watch_unsaved_changes(self, unsaved: bool) -> None:
        """Watch for unsaved changes and update the Save button UI."""
        try:
            btn = self.w_save_config_btn
            if unsaved:
                btn.variant = "warning"
                btn.label = "💾 Save Changes*"
                btn.tooltip = "You have unsaved changes [s]"
            else:
                btn.variant = "primary"
                btn.label = "💾 Save"
                btn.tooltip = "Save settings to .env file [s]"
        except Exception:
            # Widget might not be mounted yet
            pass

    def watch_network(self, network: str) -> None:
        """Watch the network reactive variable and update subtitle."""
        self.sub_title = f"Deployment Dashboard [{network.upper()}]"
        try:
            # PALETTE: Context-aware visibility for Faucet buttons (Testnet only)
            is_testnet = network == "testnet"
            self.w_faucet_btn.display = is_testnet
            self.w_settings_faucet_btn.display = is_testnet
        except Exception:
            # Widgets might not be mounted yet
            pass

    def __init__(self, config_path: str = ".env", **kwargs):
        super().__init__(**kwargs)
        self.config_path = config_path
        self.config = self._load_config()
        self.network = self.config.get("NETWORK", "testnet")
        self.address = self.config.get("SYSTEM_ADDRESS", "Not configured")
        self.monitor = DeploymentMonitor(self.network, self.config)
        self._manual_refresh_in_progress = False
        self.selected_contract_id = None
        self.selected_tx_id = None
        self.current_source_code = None
        # Bolt ⚡: State tracking to avoid redundant UI re-renders
        self._last_contracts = None
        self._last_transactions = None
        self._last_metrics = {}

    def _load_config(self) -> Dict:
        """Load configuration from file and environment, enforcing security policies."""
        config = {}
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            k, v = key.strip(), value.strip().strip('"').strip("'")

                            # 🛡️ Sentinel: Enforce security policy - no secrets in .env
                            # Bolt ⚡: Check both key name and value for secrets to provide defense-in-depth.
                            if (is_sensitive_key(k) or is_sensitive_value(v)) and not is_placeholder(v):
                                raise ValueError(
                                    f"🛡️ Sentinel Security Error: Secret key '{k}' found in .env file.\n"
                                    "   Storing secrets in plaintext files is a critical security risk.\n"
                                    "   Please move this secret to an environment variable."
                                )
                            config[k] = v

            # 🛡️ Sentinel: Secure and broadened environment variable loading.
            # Load any environment variable that is in the .env file OR matches our
            # specific app secrets (SECRET_KEYS) OR has a safe app-specific prefix.
            for key, value in os.environ.items():
                if (
                    key in config
                    or key in SECRET_KEYS
                    or key.startswith(("STACKS_", "STACKSORBIT_"))
                ):
                    config[key] = value

        except ValueError as e:
            # Re-raise Sentinel security errors to prevent app from starting insecurely
            print(f"\n{e}\n")
            raise
        except Exception:
            # 🛡️ Sentinel: Prevent sensitive information disclosure.
            print("Error loading configuration.")
        return config

    def compose(self) -> ComposeResult:
        """Compose the GUI layout"""
        yield Header()

        with TabbedContent(initial="overview"):
            with TabPane("📊 Dashboard", id="overview"):
                yield LoadingIndicator()
                with Horizontal(id="address-bar"):
                    yield Label("System Address:", id="system-address-label")
                    yield Static(
                        self.address,
                        id="display-address",
                        classes="clickable-label",
                        markup=True,
                    )
                    yield Button("📋", id="copy-dashboard-address-btn")
                    yield Button("🌐", id="view-dashboard-explorer-btn")
                    yield Button("🚰 Faucet", id="faucet-btn", variant="warning")
                with Grid(id="metrics-grid"):
                    yield Container(
                        Label("Network Status"),
                        Static("N/A", id="network-status", markup=True),
                        classes="metric-card",
                        id="metric-network",
                    )
                    yield Container(
                        Label("Contracts Deployed"),
                        Static("0", id="contract-count"),
                        classes="metric-card",
                        id="metric-contracts",
                    )
                    yield Container(
                        Label("Balance"),
                        Static("0 STX", id="balance", markup=True),
                        classes="metric-card",
                        id="metric-balance",
                    )
                    yield Container(
                        Label("Nonce"),
                        Static("0", id="nonce"),
                        classes="metric-card",
                        id="metric-nonce",
                    )
                    yield Container(
                        Label("Block Height"),
                        Static("0", id="block-height"),
                        classes="metric-card",
                        id="metric-height",
                    )
                with Horizontal(id="overview-buttons"):
                    yield Button(
                        "🔄 Refresh",
                        id="refresh-btn",
                    )
                    yield Label("", id="last-updated-label")

            with TabPane("📄 Contracts", id="contracts"):
                with Horizontal():
                    yield DataTable(id="contracts-table", zebra_stripes=True)
                    yield Vertical(
                        Horizontal(
                            Label("Contract Details", classes="header"),
                            Button("📋", id="copy-contract-id-btn"),
                            Button("📄", id="copy-source-btn"),
                            Button("🌐", id="view-explorer-btn"),
                            id="contract-details-header",
                        ),
                        LoadingIndicator(),
                        Markdown(
                            "Select a contract from the table to view its source code.",
                            id="contract-details",
                        ),
                        classes="details-pane",
                    )

            with TabPane("📜 Transactions", id="transactions"):
                yield LoadingIndicator()
                yield DataTable(id="transactions-table", zebra_stripes=True)
                with Horizontal(id="transaction-actions"):
                    yield Label("Select a transaction to see actions", id="tx-status-label")
                    yield Button("📋", id="copy-selected-tx-btn")
                    yield Button("🌐", id="view-selected-tx-explorer-btn")

            with TabPane("🚀 Deploy", id="deployment"):
                with Vertical():
                    yield LoadingIndicator()
                    yield Log(id="deployment-log")
                    with Horizontal():
                        yield Button(
                            "🔍 Pre-check",
                            id="precheck-btn",
                            variant="primary",
                        )
                        yield Button(
                            "🚀 Deploy",
                            id="start-deploy-btn",
                            variant="primary",
                        )
                        yield Button(
                            "🗑️ Clear",
                            id="clear-log-btn",
                            variant="error",
                        )

            with TabPane("⚙️ Settings", id="settings"):
                with VerticalScroll():
                    yield Label(
                        "Private Key: [red]*[/red]",
                        markup=True,
                        id="privkey-label",
                        classes="clickable-label",
                    )
                    with Horizontal(classes="input-group"):
                        yield Input(
                            placeholder="Your private key",
                            value=self.config.get("DEPLOYER_PRIVKEY", ""),
                            id="privkey-input",
                            password=True,
                        )
                        yield Label(
                            "Show",
                            classes="switch-label clickable-label",
                            id="show-privkey-label",
                        )
                        yield Switch(id="show-privkey")
                    yield Label("", id="privkey-error", markup=True)
                    yield Label(
                        "Stacks Address: [red]*[/red]",
                        markup=True,
                        id="address-label",
                        classes="clickable-label",
                    )
                    with Horizontal(classes="input-group"):
                        yield Input(
                            placeholder="Your STX address",
                            value=self.config.get("SYSTEM_ADDRESS", ""),
                            id="address-input",
                        )
                        yield Button(
                            "🔗 Connect",
                            id="connect-wallet-btn",
                        )
                        yield Button(
                            "📋",
                            id="copy-address-btn",
                        )
                        yield Button(
                            "🌐",
                            id="view-address-explorer-btn",
                        )
                        yield Button(
                            "🚰 Faucet",
                            id="settings-faucet-btn",
                            variant="warning",
                        )
                    yield Label("", id="address-error", markup=True)
                    yield Button(
                        "💾 Save",
                        id="save-config-btn",
                        variant="primary",
                    )

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the GUI and cache widget references for performance."""
        self.title = "StacksOrbit"
        self.sub_title = f"Deployment Dashboard [{self.network.upper()}]"

        # Bolt ⚡: Cache frequently accessed widgets to avoid redundant DOM queries via query_one.
        # This significantly improves performance during high-frequency update loops and UI events.
        self.w_network_status = self.query_one("#network-status", Static)
        self.w_block_height = self.query_one("#block-height", Static)
        self.w_balance = self.query_one("#balance", Static)
        self.w_nonce = self.query_one("#nonce", Static)
        self.w_contract_count = self.query_one("#contract-count", Static)
        self.w_last_updated = self.query_one("#last-updated-label", Label)
        self.w_contracts_table = self.query_one("#contracts-table", DataTable)
        self.w_transactions_table = self.query_one("#transactions-table", DataTable)
        self.w_display_address = self.query_one("#display-address", Static)
        self.w_faucet_btn = self.query_one("#faucet-btn", Button)
        self.w_view_dashboard_explorer_btn = self.query_one("#view-dashboard-explorer-btn", Button)
        self.w_settings_faucet_btn = self.query_one("#settings-faucet-btn", Button)
        self.w_view_address_explorer_btn = self.query_one("#view-address-explorer-btn", Button)
        self.w_address_input = self.query_one("#address-input", Input)
        self.w_privkey_input = self.query_one("#privkey-input", Input)
        self.w_address_error = self.query_one("#address-error", Label)
        self.w_privkey_error = self.query_one("#privkey-error", Label)
        self.w_copy_contract_btn = self.query_one("#copy-contract-id-btn", Button)
        self.w_copy_source_btn = self.query_one("#copy-source-btn", Button)
        self.w_view_explorer_btn = self.query_one("#view-explorer-btn", Button)
        self.w_copy_tx_btn = self.query_one("#copy-selected-tx-btn", Button)
        self.w_view_tx_explorer_btn = self.query_one("#view-selected-tx-explorer-btn", Button)
        self.w_tx_status_label = self.query_one("#tx-status-label", Label)
        self.w_save_config_btn = self.query_one("#save-config-btn", Button)
        self.w_deployment_log = self.query_one("#deployment-log", Log)
        self.w_show_privkey = self.query_one("#show-privkey", Switch)
        self.w_tabbed_content = self.query_one(TabbedContent)
        self.w_contract_details_header_label = self.query_one("#contract-details-header Label", Label)
        self.w_contract_details_md = self.query_one("#contract-details", Markdown)
        self.w_details_loader = self.query(".details-pane LoadingIndicator").first()

        # Bolt ⚡: Cache all LoadingIndicator widgets and the Refresh button to avoid redundant DOM queries.
        # Use defensive queries to avoid crashes if widgets are unmounted during initialization.
        self.w_loading_indicators = list(self.query(LoadingIndicator))
        self.w_overview_indicators = list(self.query("#overview LoadingIndicator"))
        self.w_refresh_btn = self.query("#refresh-btn").first() if self.query("#refresh-btn") else None

        # PALETTE: Handle 'Not configured' state visually
        if self.address == "Not configured":
            self.w_display_address.update("[dim]Not configured[/]")

        for indicator in self.query(LoadingIndicator):
            indicator.display = False

        # Add tooltips to widgets
        self.w_contracts_table.tooltip = (
            "List of contracts deployed by this address. Click a row to view source code."
        )
        self.w_transactions_table.tooltip = (
            "Recent transactions for this address. Click a row to copy full TX ID."
        )
        self.w_deployment_log.tooltip = (
            "Deployment process logs and output"
        )

        # Buttons and interactive elements tooltips
        self.query_one("#refresh-btn", Button).tooltip = (
            "Refresh all dashboard data [r]"
        )
        self.query_one("#precheck-btn", Button).tooltip = (
            "Run diagnostic checks before deployment"
        )
        self.query_one("#start-deploy-btn", Button).tooltip = (
            "Start the deployment process"
        )
        self.query_one("#clear-log-btn", Button).tooltip = "Clear the deployment log"
        self.w_show_privkey.tooltip = (
            "Toggle private key visibility"
        )
        self.query_one("#copy-address-btn", Button).tooltip = (
            "Copy address to clipboard"
        )
        self.w_view_address_explorer_btn.tooltip = (
            "View address on Hiro Explorer"
        )
        self.query_one("#connect-wallet-btn", Button).tooltip = (
            "Connect your wallet via browser"
        )
        self.query_one("#system-address-label", Label).tooltip = (
            "Your active Stacks address for deployments"
        )
        self.w_display_address.tooltip = (
            "Click to copy your Stacks address"
        )
        self.query_one("#copy-dashboard-address-btn", Button).tooltip = (
            "Copy your Stacks address to clipboard"
        )
        self.w_view_dashboard_explorer_btn.tooltip = (
            "View your address on Hiro Explorer"
        )
        self.w_faucet_btn.tooltip = (
            "Get free STX from the Hiro Testnet Faucet"
        )
        self.w_settings_faucet_btn.tooltip = (
            "Get free STX from the Hiro Testnet Faucet"
        )
        self.w_copy_contract_btn.tooltip = (
            "Copy selected contract ID"
        )
        self.w_copy_source_btn.tooltip = "Copy contract source code"
        self.w_view_explorer_btn.tooltip = (
            "View contract on Hiro Explorer"
        )

        self.w_copy_contract_btn.disabled = True
        self.w_copy_source_btn.disabled = True
        self.w_view_explorer_btn.disabled = True

        # PALETTE: Initialize address explorer button states
        is_addr_configured = self.address != "Not configured"
        self.w_view_dashboard_explorer_btn.disabled = not is_addr_configured
        self.w_view_address_explorer_btn.disabled = not is_addr_configured

        # Transaction actions initialization
        self.w_copy_tx_btn.disabled = True
        self.w_view_tx_explorer_btn.disabled = True
        self.w_copy_tx_btn.tooltip = "Copy full transaction ID"
        self.w_view_tx_explorer_btn.tooltip = (
            "View transaction on Hiro Explorer"
        )

        self.w_save_config_btn.tooltip = (
            "Save settings to .env file [s]"
        )

        # Add tooltips to tabs for better discoverability
        self.query_one("#overview").tooltip = "Dashboard overview [F1]"
        self.query_one("#contracts").tooltip = "Contract management [F2]"
        self.query_one("#transactions").tooltip = "Transaction history [F3]"
        self.query_one("#deployment").tooltip = "Smart contract deployment [F4]"
        self.query_one("#settings").tooltip = "App settings [F5]"

        # Add tooltips to metric cards for better clarity
        self.query("#network-status").first().parent.tooltip = (
            f"Current status of the Stacks API ({self.monitor.api_url}). Click to refresh."
        )
        self.query("#contract-count").first().parent.tooltip = (
            "Total number of contracts deployed by this address"
        )
        self.query("#balance").first().parent.tooltip = (
            "Available STX balance in this account"
        )
        self.query("#nonce").first().parent.tooltip = (
            "Current account nonce (next transaction number)"
        )
        self.query("#block-height").first().parent.tooltip = (
            "Current Stacks blockchain height"
        )

        # Dashboard navigation tooltips
        self.query_one("#metric-contracts").tooltip = "Click to view deployed contracts [F2]"
        self.query_one("#metric-balance").tooltip = "Click to view transaction history [F3]"
        self.query_one("#metric-nonce").tooltip = "Click to view transaction history [F3]"
        self.query_one("#metric-height").tooltip = "Click to view transaction history [F3]"
        self.query_one("#privkey-label", Label).tooltip = "Click to focus private key input"
        self.query_one("#address-label", Label).tooltip = "Click to focus address input"
        self.query_one("#show-privkey-label").tooltip = "Toggle private key visibility"

        # PALETTE: Initialize Faucet button visibility
        try:
            is_testnet = self.network == "testnet"
            self.w_faucet_btn.display = is_testnet
            self.w_settings_faucet_btn.display = is_testnet
        except Exception:
            pass

        self._setup_tables()
        self.set_interval(10.0, self.update_data)
        self.run_worker(self.update_data())

    def _setup_tables(self) -> None:
        """Setup the data tables"""
        contracts_table = self.query_one("#contracts-table", DataTable)
        contracts_table.add_columns("Status", "Name", "Address")

        transactions_table = self.query_one("#transactions-table", DataTable)
        transactions_table.add_columns("TX ID", "Type", "Status", "Time", "Block")

    def _format_relative_time(self, iso_time: str, now: datetime) -> str:
        """Format an ISO timestamp as a relative time string (e.g., '5m ago')."""
        if not iso_time:
            return "[yellow]Pending[/]"

        # Bolt ⚡: Normalize 'now' to 10s intervals to maximize cache hits across refreshes.
        # This avoids redundant calculations for transactions whose relative time hasn't changed.
        now_bucket = int(now.timestamp() / 10) * 10
        return _format_relative_time_cached(iso_time, now_bucket)

    async def update_data(self, bypass_cache: bool = False) -> None:
        """Update all data in the GUI concurrently."""
        # ⚡ Bolt: Don't clear tables immediately to avoid flickering.
        # We will clear them only if data has changed.
        # Bolt ⚡: Use cached indicators to avoid O(N) DOM queries.
        for indicator in self.w_loading_indicators:
            indicator.display = True

        try:
            # ⚡ Bolt: Run synchronous API calls concurrently in threads
            # This prevents the UI from blocking and speeds up the data refresh
            # by fetching all data in parallel instead of one by one.
            api_status_task = asyncio.to_thread(
                self.monitor.check_api_status, bypass_cache=bypass_cache
            )

            if self.address != "Not configured":
                account_info_task = asyncio.to_thread(
                    self.monitor.get_account_info, self.address, bypass_cache=bypass_cache
                )
                contracts_task = asyncio.to_thread(
                    self.monitor.get_deployed_contracts,
                    self.address,
                    bypass_cache=bypass_cache,
                )
                transactions_task = asyncio.to_thread(
                    self.monitor.get_recent_transactions,
                    self.address,
                    bypass_cache=bypass_cache,
                )

                api_status, account_info, deployed_contracts, transactions = (
                    await asyncio.gather(
                        api_status_task,
                        account_info_task,
                        contracts_task,
                        transactions_task,
                        return_exceptions=True,
                    )
                )
            else:
                # If no address, only fetch API status and provide sensible defaults for other data.
                api_status = await api_status_task
                account_info, deployed_contracts, transactions = None, [], []
                # Data will be processed by the Bolt ⚡ optimization logic below

            # Process API status result
            if isinstance(api_status, Exception):
                raise api_status  # Propagate exception to be caught by the main handler

            # Bolt ⚡: Conditional UI updates for dashboard metrics.
            # Static.update() is expensive; only call it if the value has changed.
            status = api_status.get("status", "unknown").upper()
            dot = "[green]●[/]" if status == "ONLINE" else "[red]●[/]"
            status_display = f"{dot} {status}"
            if self._last_metrics.get("status") != status_display:
                self.w_network_status.update(status_display)
                self._last_metrics["status"] = status_display

            height = str(api_status.get("block_height", 0))
            if self._last_metrics.get("height") != height:
                self.w_block_height.update(height)
                self._last_metrics["height"] = height

            # Process account info result
            if isinstance(account_info, Exception):
                raise account_info

            balance_stx_display = "0 STX"
            nonce_display = "0"

            if account_info:
                balance_raw = account_info.get("balance", 0)
                balance_stx = (
                    int(balance_raw, 16)
                    if isinstance(balance_raw, str) and balance_raw.startswith("0x")
                    else int(balance_raw)
                ) / 1_000_000
                balance_stx_display = f"{balance_stx:,.6f} STX"

                # PALETTE: Colorize balance for immediate visual context
                if balance_stx >= 1.0:
                    balance_stx_display = f"[green]{balance_stx_display}[/]"
                elif balance_stx > 0:
                    balance_stx_display = f"[yellow]{balance_stx_display}[/]"
                else:
                    balance_stx_display = f"[red]{balance_stx_display}[/]"

                nonce_display = str(account_info.get("nonce", 0))

            if self._last_metrics.get("balance") != balance_stx_display:
                self.w_balance.update(balance_stx_display)
                self._last_metrics["balance"] = balance_stx_display

            if self._last_metrics.get("nonce") != nonce_display:
                self.w_nonce.update(nonce_display)
                self._last_metrics["nonce"] = nonce_display

            # Process deployed contracts result
            if isinstance(deployed_contracts, Exception):
                raise deployed_contracts

            count_display = str(len(deployed_contracts))
            if self._last_metrics.get("contract-count") != count_display:
                self.w_contract_count.update(count_display)
                self._last_metrics["contract-count"] = count_display

            # ⚡ Bolt: Only clear and repopulate contracts table if data changed
            if deployed_contracts != self._last_contracts:
                contracts_table = self.w_contracts_table
                contracts_table.clear()
                if deployed_contracts:
                    # Bolt ⚡: Build rows in a list and use add_rows() for atomic, high-performance table population.
                    contract_rows = []
                    for contract in deployed_contracts:
                        address, name = contract.get("contract_id", "...").split(".")
                        contract_rows.append(("✅", name, address))

                    # Note: DataTable.add_rows doesn't take keys in the same way as add_row in some versions,
                    # so we'll use add_row in a loop if add_rows doesn't support keys.
                    # Actually, Textual's add_rows doesn't support per-row keys.
                    # So I will keep add_row but move it to a more efficient loop if possible.
                    # Wait, if I want keys, I have to use add_row.
                    for i, row in enumerate(contract_rows):
                        contracts_table.add_row(*row, key=deployed_contracts[i].get("contract_id"))
                elif self.address != "Not configured":
                    contracts_table.add_row(
                        "", "No contracts found", "Deploy a contract to see it here."
                    )
                else:
                    contracts_table.add_row(
                        "⚠️", "Config missing", "Address not configured in .env file."
                    )
                self._last_contracts = deployed_contracts

            # Process transactions result
            if isinstance(transactions, Exception):
                raise transactions

            # Update last updated label
            now_label = datetime.now().strftime("%H:%M:%S")
            self.w_last_updated.update(f" [dim]Last updated: {now_label}[/]")

            # ⚡ Bolt: Only clear and repopulate transactions table if data changed
            if transactions != self._last_transactions:
                transactions_table = self.w_transactions_table
                transactions_table.clear()
                if transactions:
                    # Bolt ⚡: Hoist datetime.now(timezone.utc) out of the loop to avoid redundant system calls.
                    now_utc = datetime.now(timezone.utc)
                    # Bolt ⚡: Building rows first and then adding them can be more efficient,
                    # but we use add_row to preserve row keys for selection.
                    for tx in transactions:
                        status = tx.get("tx_status", "")
                        # PALETTE: Colorize status with emojis for better scannability
                        display_status = status
                        if status == "success":
                            display_status = "[green]✅ success[/]"
                        elif "pending" in status:
                            display_status = "[yellow]⏳ pending[/]"
                        elif "abort" in status or status == "failed":
                            display_status = "[red]❌ failed[/]"

                        tx_type = tx.get("tx_type", "")
                        display_type = tx_type
                        if tx_type == "smart_contract":
                            display_type = "📄 [cyan]contract[/]"
                        elif tx_type == "contract_call":
                            display_type = "📞 [magenta]call[/]"
                        elif tx_type == "token_transfer":
                            display_type = "💸 [yellow]transfer[/]"
                        elif tx_type == "coinbase":
                            display_type = "⛏️ [green]coinbase[/]"

                        transactions_table.add_row(
                            tx.get("tx_id", "")[:10] + "...",
                            display_type,
                            display_status,
                            self._format_relative_time(tx.get("burn_block_time_iso"), now_utc),
                            str(tx.get("block_height", "")),
                            key=tx.get("tx_id"),
                        )
                elif self.address != "Not configured":
                    transactions_table.add_row("", "No transactions found", "", "")
                else:
                    transactions_table.add_row(
                        "⚠️", "Config missing", "Address not configured in .env", ""
                    )
                self._last_transactions = transactions

        except Exception as e:
            self.w_network_status.update("[red]Error[/]")
            self.notify(f"API error: {e}", severity="error")
        finally:
            # Bolt ⚡: Use cached indicators to avoid O(N) DOM queries.
            for indicator in self.w_loading_indicators:
                indicator.display = False

    @on(DataTable.RowSelected, "#contracts-table")
    def on_contracts_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle contract row selection."""
        contract_id = event.row_key.value
        if contract_id:
            self.selected_contract_id = contract_id
            # Update detail header with contract name
            name = contract_id.split(".")[1] if "." in contract_id else contract_id
            self.w_contract_details_header_label.update(f"Details: [cyan]{name}[/]")

            self.w_copy_contract_btn.disabled = False
            self.w_copy_source_btn.disabled = False
            self.w_view_explorer_btn.disabled = False
            self.run_worker(self.fetch_contract_details(contract_id), exclusive=True)

    @on(DataTable.RowSelected, "#transactions-table")
    def on_transactions_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle transaction row selection."""
        tx_id = event.row_key.value
        if tx_id:
            self.selected_tx_id = tx_id
            self.w_copy_tx_btn.disabled = False
            self.w_view_tx_explorer_btn.disabled = False
            self.w_tx_status_label.update(
                f"Selected: [cyan]{tx_id[:16]}...[/cyan]"
            )

            # Auto-copy for immediate use
            self.copy_to_clipboard(tx_id)
            self.notify(
                f"Transaction ID copied: {tx_id}", severity="information"
            )

    @on(Click, "#display-address")
    async def on_display_address_click(self) -> None:
        """Copy address to clipboard when the display address is clicked."""
        if self.address and self.address != "Not configured":
            self.copy_to_clipboard(self.address)
            self.notify("Address copied to clipboard", severity="information")

    @on(Click, "#metric-network")
    def on_network_metric_click(self) -> None:
        """Refresh data when network metric is clicked."""
        self.action_refresh()

    @on(Click, "#metric-contracts")
    def on_contracts_metric_click(self) -> None:
        """Navigate to contracts tab when contract metric is clicked."""
        self.w_tabbed_content.active = "contracts"

    @on(Click, "#metric-balance")
    @on(Click, "#metric-nonce")
    @on(Click, "#metric-height")
    def on_transactions_metric_click(self) -> None:
        """Navigate to transactions tab when account metrics are clicked."""
        self.w_tabbed_content.active = "transactions"

    @on(Click, "#privkey-label")
    def on_privkey_label_click(self) -> None:
        """Focus the private key input when its label is clicked."""
        self.w_privkey_input.focus()

    @on(Click, "#address-label")
    def on_address_label_click(self) -> None:
        """Focus the address input when its label is clicked."""
        self.w_address_input.focus()

    @on(Click, "#show-privkey-label")
    def on_show_privkey_label_click(self) -> None:
        """Toggle private key visibility when its label is clicked."""
        self.w_show_privkey.toggle()

    @on(TabbedContent.TabActivated)
    def on_tab_changed(self, event: TabbedContent.TabActivated) -> None:
        """Handle tab changes to improve interaction focus."""
        if event.tabbed_content.active == "settings":
            self.w_privkey_input.focus()

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab."""
        self.w_tabbed_content.active = tab_id

    async def fetch_contract_details(self, contract_id: str) -> None:
        """Worker to fetch and display contract details."""
        md = self.w_contract_details_md
        loader = self.w_details_loader

        md.update("")
        loader.display = True
        self.current_source_code = None
        try:
            details = await asyncio.to_thread(
                self.monitor.get_contract_details, contract_id
            )
            if details:
                self.current_source_code = details.get("source_code")
                md.update(
                    f"**Source Code:**\n```clarity\n{self.current_source_code or 'Not available.'}\n```"
                )
            else:
                md.update("Could not retrieve contract details.")
        finally:
            loader.display = False

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    async def action_save_settings(self) -> None:
        """Action to save settings from keyboard shortcut."""
        self.w_tabbed_content.active = "settings"
        await self.on_save_config_pressed()

    @on(Button.Pressed, "#refresh-btn")
    def action_refresh(self) -> None:
        """Handle manual refresh button press."""
        if self._manual_refresh_in_progress:
            return

        # Bolt ⚡: Use cached refresh button and indicators for O(1) feedback.
        refresh_btn = self.w_refresh_btn
        if refresh_btn:
            self._original_btn_label = refresh_btn.label
            refresh_btn.disabled = True
            refresh_btn.label = "Refreshing..."

        for indicator in self.w_overview_indicators:
            indicator.display = True

        self.run_worker(self._do_refresh())

    async def _do_refresh(self) -> None:
        """Perform the data refresh and update the UI."""
        self._manual_refresh_in_progress = True
        try:
            # Bolt ⚡: Manual refresh always bypasses the cache for immediate responsiveness.
            await self.update_data(bypass_cache=True)
            self.notify("Data refreshed")
        except Exception as e:
            self.notify(f"Refresh failed: {e}", severity="error")
        finally:
            # Bolt ⚡: Use cached refresh button and indicators for O(1) feedback.
            if self.w_refresh_btn:
                self.w_refresh_btn.disabled = False
                self.w_refresh_btn.label = getattr(self, "_original_btn_label", "🔄 Refresh")

            for indicator in self.w_overview_indicators:
                indicator.display = False
            self._manual_refresh_in_progress = False

    def run_command(
        self, command: List[str], button: Button, in_progress_label: str
    ) -> None:
        """Run a CLI command in a separate thread, with button feedback."""
        log = self.query_one("#deployment-log", Log)
        log.clear()

        loading_indicator = self.query("#deployment LoadingIndicator").first()
        loading_indicator.display = True

        precheck_btn = self.query_one("#precheck-btn", Button)
        deploy_btn = self.query_one("#start-deploy-btn", Button)
        original_label = button.label

        precheck_btn.disabled = True
        deploy_btn.disabled = True
        button.label = in_progress_label

        def worker():
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                for line in iter(process.stdout.readline, ""):
                    self.call_from_thread(log.write, line.strip())
                process.stdout.close()
                return_code = process.wait()
                self.call_from_thread(
                    log.write,
                    f"\n[bold]{'Success' if return_code == 0 else 'Failed'}[/bold]",
                )
            finally:
                self.call_from_thread(setattr, button, "label", original_label)
                self.call_from_thread(setattr, precheck_btn, "disabled", False)
                self.call_from_thread(setattr, deploy_btn, "disabled", False)
                self.call_from_thread(setattr, loading_indicator, "display", False)

        thread = threading.Thread(target=worker)
        thread.start()

    @on(Button.Pressed, "#precheck-btn")
    def on_precheck_pressed(self, event: Button.Pressed) -> None:
        """Handle pre-check button press."""
        self.run_command(
            ["python", "stacksorbit_cli.py", "diagnose"],
            event.button,
            in_progress_label="Checking...",
        )

    @on(Button.Pressed, "#start-deploy-btn")
    def on_start_deploy_pressed(self, event: Button.Pressed) -> None:
        """Handle deploy button press."""
        self.run_command(
            ["python", "stacksorbit_cli.py", "deploy"],
            event.button,
            in_progress_label="Deploying...",
        )

    @on(Button.Pressed, "#clear-log-btn")
    def on_clear_log_pressed(self) -> None:
        """Handle clear log button press."""
        self.query_one("#deployment-log", Log).clear()
        self.notify("Deployment log cleared")

    @on(Switch.Changed, "#show-privkey")
    def on_show_privkey_changed(self, event: Switch.Changed) -> None:
        """Toggle private key visibility and update label."""
        self.w_privkey_input.password = not event.value
        try:
            label = self.query_one("#show-privkey-label", Label)
            label.update("Hide" if event.value else "Show")
        except Exception:
            pass

    @on(Input.Changed, "#address-input")
    def on_address_changed(self, event: Input.Changed) -> None:
        """Real-time validation for Stacks address with character count."""
        error_label = self.w_address_error
        count = len(event.value)
        # PALETTE: Include character count in feedback
        count_display = f" [dim]({count}/41)[/]" if event.value else ""

        # PALETTE: Track unsaved changes if the user is interacting with the input
        if event.input.has_focus:
            self.unsaved_changes = True

        if not event.value:
            event.input.remove_class("error")
            error_label.update("")
        elif validate_stacks_address(event.value, self.network):
            event.input.remove_class("error")
            error_label.update(f"[green]✅ Valid[/]{count_display}")
        else:
            event.input.add_class("error")
            prefix = "SP" if self.network == "mainnet" else "ST"
            # PALETTE: Accurate validation range from stacksorbit_secrets.py
            error_label.update(
                f"[red]❌ Must be 28-41 chars and start with {prefix}[/red]{count_display}"
            )

    @on(Input.Changed, "#privkey-input")
    def on_privkey_changed(self, event: Input.Changed) -> None:
        """Real-time validation for Private Key with character count."""
        error_label = self.w_privkey_error
        count = len(event.value)
        # PALETTE: Include character count in feedback
        count_display = f" [dim]({count}/64 or 66)[/]" if event.value else ""

        # PALETTE: Track unsaved changes if the user is interacting with the input
        if event.input.has_focus:
            self.unsaved_changes = True

        if not event.value or event.value == "your_private_key_here":
            event.input.remove_class("error")
            error_label.update("")
        elif validate_private_key(event.value):
            event.input.remove_class("error")
            error_label.update(f"[green]✅ Valid[/]{count_display}")
        else:
            event.input.add_class("error")
            error_label.update(
                f"[red]❌ Must be a 64 or 66 character hex string[/red]{count_display}"
            )

    @on(Button.Pressed, "#connect-wallet-btn")
    def on_connect_wallet_pressed(self) -> None:
        """Launch the wallet connection wizard."""
        self.notify("Launching Wallet Connect in your browser...", severity="information")
        self.run_worker(self._run_wallet_connect())

    async def _run_wallet_connect(self) -> None:
        """Worker to run the wallet connect server and update UI."""
        from wallet_connect import start_wallet_connect_server
        import contextlib
        import io

        btn = self.query_one("#connect-wallet-btn", Button)
        original_label = btn.label
        btn.disabled = True
        btn.label = "🔗 Waiting..."

        try:
            # Run the server in a thread and suppress stdout to keep TUI clean
            with contextlib.redirect_stdout(io.StringIO()):
                address = await asyncio.to_thread(start_wallet_connect_server)

            if address:
                # Update inputs and internal state
                self.w_address_input.value = address
                self.address = address
                self.unsaved_changes = True
                try:
                    self.w_display_address.update(address)
                except Exception:
                    pass
                self.notify(f"Wallet connected: {address}", severity="success")
                btn.label = "✅ Done"
                await asyncio.sleep(2)
        except Exception as e:
            self.notify(f"Wallet connection failed: {e}", severity="error")
        finally:
            btn.disabled = False
            btn.label = original_label

    @on(Button.Pressed, "#copy-address-btn")
    async def on_copy_address_pressed(self) -> None:
        """Handle copy address button press with visual feedback."""
        address = self.query_one("#address-input", Input).value
        if address:
            self.copy_to_clipboard(address)
            self.notify("Address copied to clipboard", severity="information")

            # Micro-UX: Visual feedback
            btn = self.query_one("#copy-address-btn", Button)
            if btn.label != "✅":
                btn.label = "✅"
                await asyncio.sleep(1)
                btn.label = "📋"

    @on(Button.Pressed, "#faucet-btn")
    @on(Button.Pressed, "#settings-faucet-btn")
    def on_faucet_pressed(self) -> None:
        """Open the Hiro Testnet Faucet in the browser."""
        url = "https://explorer.hiro.so/sandbox/faucet?chain=testnet"
        webbrowser.open(url)
        self.notify("Opening Testnet Faucet in browser...", severity="information")

    @on(Button.Pressed, "#view-dashboard-explorer-btn")
    @on(Button.Pressed, "#view-address-explorer-btn")
    async def on_view_address_explorer_pressed(self, event: Button.Pressed) -> None:
        """Open the Stacks address on the Hiro Explorer."""
        # For dashboard button, use self.address.
        # For settings button, use the current input value for better UX.
        address = self.address
        if event.button.id == "view-address-explorer-btn":
            address = self.w_address_input.value

        if not address or address == "Not configured":
            self.notify("No address configured to view.", severity="warning")
            return

        if self.network == "devnet":
            self.notify(
                "Hiro Explorer is not available for local devnet.", severity="warning"
            )
            return

        url = f"https://explorer.hiro.so/address/{address}?chain={self.network}"
        webbrowser.open(url)
        self.notify("Opening Explorer in browser...", severity="information")

    @on(Button.Pressed, "#copy-dashboard-address-btn")
    async def on_copy_dashboard_address_pressed(self) -> None:
        """Handle dashboard address copy button press with visual feedback."""
        if self.address and self.address != "Not configured":
            self.copy_to_clipboard(self.address)
            self.notify("Address copied to clipboard", severity="information")
            btn = self.query_one("#copy-dashboard-address-btn", Button)
            if btn.label != "✅":
                btn.label = "✅"
                await asyncio.sleep(1)
                btn.label = "📋"

    @on(Button.Pressed, "#copy-contract-id-btn")
    async def on_copy_contract_id_pressed(self) -> None:
        """Handle contract ID copy button press with visual feedback."""
        if self.selected_contract_id:
            self.copy_to_clipboard(self.selected_contract_id)
            self.notify(
                f"Contract ID copied: {self.selected_contract_id}",
                severity="information",
            )

            # Micro-UX: Visual feedback
            btn = self.query_one("#copy-contract-id-btn", Button)
            if btn.label != "✅":
                btn.label = "✅"
                await asyncio.sleep(1)
                btn.label = "📋"

    @on(Button.Pressed, "#copy-source-btn")
    async def on_copy_source_pressed(self) -> None:
        """Handle copy source button press with visual feedback."""
        if self.current_source_code:
            self.copy_to_clipboard(self.current_source_code)
            self.notify("Contract source code copied", severity="information")

            # Micro-UX: Visual feedback
            btn = self.query_one("#copy-source-btn", Button)
            if btn.label != "✅":
                btn.label = "✅"
                await asyncio.sleep(1)
                btn.label = "📄"

    @on(Button.Pressed, "#view-explorer-btn")
    async def on_view_explorer_pressed(self) -> None:
        """Open the contract on the Hiro Explorer."""
        if self.selected_contract_id:
            if self.network == "devnet":
                self.notify(
                    "Hiro Explorer is not available for local devnet.", severity="warning"
                )
                return

            url = f"https://explorer.hiro.so/txid/{self.selected_contract_id}?chain={self.network}"
            webbrowser.open(url)
            self.notify("Opening Explorer in browser...", severity="information")

    @on(Button.Pressed, "#copy-selected-tx-btn")
    async def on_copy_selected_tx_pressed(self) -> None:
        """Handle transaction ID copy button press with visual feedback."""
        if self.selected_tx_id:
            self.copy_to_clipboard(self.selected_tx_id)
            self.notify(
                f"Transaction ID copied: {self.selected_tx_id}", severity="information"
            )

            # Micro-UX: Visual feedback
            btn = self.query_one("#copy-selected-tx-btn", Button)
            if btn.label != "✅":
                btn.label = "✅"
                await asyncio.sleep(1)
                btn.label = "📋"

    @on(Button.Pressed, "#view-selected-tx-explorer-btn")
    async def on_view_selected_tx_explorer_pressed(self) -> None:
        """Open the selected transaction on the Hiro Explorer."""
        if self.selected_tx_id:
            if self.network == "devnet":
                self.notify(
                    "Hiro Explorer is not available for local devnet.", severity="warning"
                )
                return

            url = f"https://explorer.hiro.so/txid/{self.selected_tx_id}?chain={self.network}"
            webbrowser.open(url)
            self.notify("Opening Explorer in browser...", severity="information")

    @on(Button.Pressed, "#save-config-btn")
    async def on_save_config_pressed(self) -> None:
        """Handle save config button press with visual feedback."""
        save_btn = self.w_save_config_btn
        original_label = save_btn.label

        # 🛡️ Sentinel: Collect values in the main thread for thread safety.
        # We also identify if the user is attempting to save a real secret.
        privkey_val = self.w_privkey_input.value
        address_val = self.w_address_input.value

        # 🛡️ Sentinel: Validate the Stacks address before saving
        if address_val and not validate_stacks_address(address_val, self.network):
            self.notify(
                f"🛡️ Security: Invalid Stacks address for {self.network.upper()}.",
                severity="error",
            )
            return

        # 🛡️ Sentinel: Validate the private key if provided
        if (
            privkey_val
            and privkey_val != "your_private_key_here"
            and not validate_private_key(privkey_val)
        ):
            self.notify(
                "🛡️ Security: Invalid private key format (must be 64/66 hex chars).",
                severity="error",
            )
            return

        # Check if the private key is a real secret (not empty or placeholder)
        is_secret_provided = (
            privkey_val.strip() != ""
            and privkey_val.strip().lower() != "your_private_key_here"
        )

        save_btn.disabled = True
        save_btn.label = "Saving..."

        # This function handles the file I/O.
        # By running it in a thread, we prevent the UI from freezing.
        def _save_config_io(p_address: str):
            config = self._load_config()

            # Update non-sensitive configuration
            config["SYSTEM_ADDRESS"] = p_address

            # 🛡️ Sentinel: Use centralized atomic and secure config saver.
            # This automatically filters secrets and ensures atomic, secure write.
            save_secure_config(str(self.config_path), config)

        try:
            # 🛡️ Sentinel: Only save non-sensitive settings to the file.
            await asyncio.to_thread(_save_config_io, address_val)
            self.address = address_val
            self.unsaved_changes = False

            # Sync local config
            self.config["SYSTEM_ADDRESS"] = address_val
            if is_secret_provided:
                self.config["DEPLOYER_PRIVKEY"] = privkey_val

            try:
                self.w_display_address.update(address_val)
            except Exception: pass

            if is_secret_provided:
                # 🛡️ Sentinel: Inform the user that secrets are not saved to disk.
                self.notify(
                    "🛡️ Security: Configuration saved (excluding private keys). "
                    "Use environment variables for secrets.",
                    severity="warning",
                    timeout=10,
                )
            else:
                self.notify("Configuration saved.", severity="success")

            # Provide clear, temporary success feedback on the button.
            save_btn.label = "✅ Saved!"
            save_btn.add_class("success")
            await asyncio.sleep(2)

        except Exception as e:
            self.notify(f"Error saving config: {e}", severity="error")
        finally:
            save_btn.disabled = False
            save_btn.label = original_label
            save_btn.remove_class("success")


def main():
    if not GUI_AVAILABLE:
        print(
            "GUI dependencies not available. Install with: pip install textual rich psutil"
        )
        return

    app = StacksOrbitGUI()
    app.run()


if __name__ == "__main__":
    main()
