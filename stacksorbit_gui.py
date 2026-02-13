#!/usr/bin/env python3
"""
StacksOrbit GUI - A modern, feature-rich dashboard for Stacks blockchain deployment
"""

import asyncio
import os
import subprocess
import threading
import webbrowser
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
from stacksorbit_secrets import (
    SECRET_KEYS,
    is_sensitive_key,
    validate_stacks_address,
    validate_private_key,
    set_secure_permissions,
)


class StacksOrbitGUI(App):
    """A Textual dashboard for StacksOrbit."""

    CSS_PATH = "stacksorbit_gui.tcss"

    BINDINGS = [
        Binding("d", "toggle_dark", "Toggle dark mode"),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh data"),
        Binding("s", "save_settings", "Save settings"),
        Binding("f1", "switch_tab('overview')", "Dashboard", show=True),
        Binding("f2", "switch_tab('contracts')", "Contracts", show=True),
        Binding("f3", "switch_tab('transactions')", "Transactions", show=True),
        Binding("f4", "switch_tab('deployment')", "Deploy", show=True),
        Binding("f5", "switch_tab('settings')", "Settings", show=True),
    ]

    # Reactive variables
    network = reactive("testnet")

    def watch_network(self, network: str) -> None:
        """Watch the network reactive variable and update subtitle."""
        self.sub_title = f"Deployment Dashboard [{network.upper()}]"

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
                            if is_sensitive_key(k) and v not in (
                                "",
                                "your_private_key_here",
                                "your_hiro_api_key",
                            ):
                                raise ValueError(
                                    f"🛡️ Sentinel Security Error: Secret key '{k}' found in .env file.\n"
                                    "   Storing secrets in plaintext files is a critical security risk.\n"
                                    "   Please move this secret to an environment variable."
                                )
                            config[k] = v

            # 🛡️ Sentinel: Selectively load environment variables to override file config.
            # This uses an allow-list (keys from .env + known secrets) to prevent
            # leaking unrelated environment variables.
            allowed_keys = set(config.keys()) | set(SECRET_KEYS)
            for key in allowed_keys:
                if key in os.environ:
                    config[key] = os.environ[key]

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
                with Grid(id="metrics-grid"):
                    yield Container(
                        Label("Network Status"),
                        Static("N/A", id="network-status"),
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
                        Static("0 STX", id="balance"),
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
                    yield Label("Private Key: [red]*[/red]", markup=True)
                    with Horizontal(classes="input-group"):
                        yield Input(
                            placeholder="Your private key",
                            value=self.config.get("DEPLOYER_PRIVKEY", ""),
                            id="privkey-input",
                            password=True,
                        )
                        yield Label("Show", classes="switch-label", id="show-privkey-label")
                        yield Switch(id="show-privkey")
                    yield Label("", id="privkey-error", markup=True)
                    yield Label("Stacks Address: [red]*[/red]", markup=True)
                    with Horizontal(classes="input-group"):
                        yield Input(
                            placeholder="Your STX address",
                            value=self.config.get("SYSTEM_ADDRESS", ""),
                            id="address-input",
                        )
                        yield Button(
                            "📋",
                            id="copy-address-btn",
                        )
                    yield Label("", id="address-error", markup=True)
                    yield Button(
                        "💾 Save",
                        id="save-config-btn",
                        variant="primary",
                    )

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the GUI"""
        self.title = "StacksOrbit"
        self.sub_title = f"Deployment Dashboard [{self.network.upper()}]"
        for indicator in self.query(LoadingIndicator):
            indicator.display = False

        # Add tooltips to widgets
        self.query_one("#contracts-table", DataTable).tooltip = (
            "List of contracts deployed by this address. Click a row to view source code."
        )
        self.query_one("#transactions-table", DataTable).tooltip = (
            "Recent transactions for this address. Click a row to copy full TX ID."
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
        self.query_one("#show-privkey", Switch).tooltip = (
            "Toggle private key visibility"
        )
        self.query_one("#copy-address-btn", Button).tooltip = (
            "Copy address to clipboard"
        )
        self.query_one("#copy-contract-id-btn", Button).tooltip = (
            "Copy selected contract ID"
        )
        self.query_one("#copy-source-btn", Button).tooltip = "Copy contract source code"
        self.query_one("#view-explorer-btn", Button).tooltip = (
            "View contract on Hiro Explorer"
        )

        self.query_one("#copy-contract-id-btn", Button).disabled = True
        self.query_one("#copy-source-btn", Button).disabled = True
        self.query_one("#view-explorer-btn", Button).disabled = True

        # Transaction actions initialization
        self.query_one("#copy-selected-tx-btn", Button).disabled = True
        self.query_one("#view-selected-tx-explorer-btn", Button).disabled = True
        self.query_one("#copy-selected-tx-btn", Button).tooltip = "Copy full transaction ID"
        self.query_one("#view-selected-tx-explorer-btn", Button).tooltip = (
            "View transaction on Hiro Explorer"
        )

        self.query_one("#save-config-btn", Button).tooltip = (
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
            "Current status of the Stacks API"
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
        self.query_one("#show-privkey-label").tooltip = "Toggle private key visibility"

        self._setup_tables()
        self.set_interval(10.0, self.update_data)
        self.run_worker(self.update_data())

    def _setup_tables(self) -> None:
        """Setup the data tables"""
        contracts_table = self.query_one("#contracts-table", DataTable)
        contracts_table.add_columns("Status", "Name", "Address")

        transactions_table = self.query_one("#transactions-table", DataTable)
        transactions_table.add_columns("TX ID", "Type", "Status", "Block")

    async def update_data(self, bypass_cache: bool = False) -> None:
        """Update all data in the GUI concurrently."""
        # ⚡ Bolt: Don't clear tables immediately to avoid flickering.
        # We will clear them only if data has changed.
        for indicator in self.query(LoadingIndicator):
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
            self.query_one("#network-status").update(
                api_status.get("status", "unknown").upper()
            )
            self.query_one("#block-height").update(
                str(api_status.get("block_height", 0))
            )

            # Process account info result
            if isinstance(account_info, Exception):
                raise account_info
            if account_info:
                balance_raw = account_info.get("balance", 0)
                balance_stx = (
                    int(balance_raw, 16)
                    if isinstance(balance_raw, str) and balance_raw.startswith("0x")
                    else int(balance_raw)
                ) / 1_000_000
                self.query_one("#balance").update(f"{balance_stx:,.6f} STX")
                self.query_one("#nonce").update(str(account_info.get("nonce", 0)))
            else:
                self.query_one("#balance").update("0 STX")
                self.query_one("#nonce").update("0")

            # Process deployed contracts result
            if isinstance(deployed_contracts, Exception):
                raise deployed_contracts
            self.query_one("#contract-count").update(str(len(deployed_contracts)))

            # ⚡ Bolt: Only clear and repopulate contracts table if data changed
            if deployed_contracts != self._last_contracts:
                contracts_table = self.query_one("#contracts-table", DataTable)
                contracts_table.clear()
                if deployed_contracts:
                    for contract in deployed_contracts:
                        address, name = contract.get("contract_id", "...").split(".")
                        contracts_table.add_row(
                            "✅", name, address, key=contract.get("contract_id")
                        )
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

            # ⚡ Bolt: Only clear and repopulate transactions table if data changed
            if transactions != self._last_transactions:
                transactions_table = self.query_one("#transactions-table", DataTable)
                transactions_table.clear()
                if transactions:
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

                        transactions_table.add_row(
                            tx.get("tx_id", "")[:10] + "...",
                            tx.get("tx_type", ""),
                            display_status,
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
            self.query_one("#network-status").update("[red]Error[/]")
            self.notify(f"API error: {e}", severity="error")
        finally:
            for indicator in self.query(LoadingIndicator):
                indicator.display = False

    @on(DataTable.RowSelected, "#contracts-table")
    def on_contracts_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle contract row selection."""
        contract_id = event.row_key.value
        if contract_id:
            self.selected_contract_id = contract_id
            self.query_one("#copy-contract-id-btn", Button).disabled = False
            self.query_one("#copy-source-btn", Button).disabled = False
            self.query_one("#view-explorer-btn", Button).disabled = False
            self.run_worker(self.fetch_contract_details(contract_id), exclusive=True)

    @on(DataTable.RowSelected, "#transactions-table")
    def on_transactions_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle transaction row selection."""
        tx_id = event.row_key.value
        if tx_id:
            self.selected_tx_id = tx_id
            self.query_one("#copy-selected-tx-btn", Button).disabled = False
            self.query_one("#view-selected-tx-explorer-btn", Button).disabled = False
            self.query_one("#tx-status-label", Label).update(
                f"Selected: [cyan]{tx_id[:16]}...[/cyan]"
            )

            # Auto-copy for immediate use
            self.copy_to_clipboard(tx_id)
            self.notify(
                f"Transaction ID copied: {tx_id}", severity="information"
            )

    @on(Click, "#metric-contracts")
    def on_contracts_metric_click(self) -> None:
        """Navigate to contracts tab when contract metric is clicked."""
        self.query_one(TabbedContent).active = "contracts"

    @on(Click, "#metric-balance")
    @on(Click, "#metric-nonce")
    @on(Click, "#metric-height")
    def on_transactions_metric_click(self) -> None:
        """Navigate to transactions tab when account metrics are clicked."""
        self.query_one(TabbedContent).active = "transactions"

    @on(Click, "#show-privkey-label")
    def on_show_privkey_label_click(self) -> None:
        """Toggle private key visibility when its label is clicked."""
        self.query_one("#show-privkey", Switch).toggle()

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab."""
        self.query_one(TabbedContent).active = tab_id

    async def fetch_contract_details(self, contract_id: str) -> None:
        """Worker to fetch and display contract details."""
        details_pane = self.query(".details-pane").first()
        md = details_pane.query_one(Markdown)
        loader = details_pane.query_one(LoadingIndicator)

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
        self.query_one(TabbedContent).active = "settings"
        await self.on_save_config_pressed()

    @on(Button.Pressed, "#refresh-btn")
    def action_refresh(self) -> None:
        """Handle manual refresh button press."""
        if self._manual_refresh_in_progress:
            return

        refresh_btn = self.query_one("#refresh-btn", Button)
        self._original_btn_label = refresh_btn.label
        refresh_btn.disabled = True
        refresh_btn.label = "Refreshing..."
        self.query("#overview LoadingIndicator").first().display = True

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
            refresh_btn = self.query_one("#refresh-btn", Button)
            refresh_btn.disabled = False
            refresh_btn.label = self._original_btn_label
            self.query("#overview LoadingIndicator").first().display = False
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
        """Toggle private key visibility."""
        self.query_one("#privkey-input", Input).password = not event.value

    @on(Input.Changed, "#address-input")
    def on_address_changed(self, event: Input.Changed) -> None:
        """Real-time validation for Stacks address."""
        error_label = self.query_one("#address-error", Label)
        if not event.value:
            event.input.remove_class("error")
            error_label.update("")
        elif validate_stacks_address(event.value, self.network):
            event.input.remove_class("error")
            error_label.update("")
        else:
            event.input.add_class("error")
            prefix = "SP" if self.network == "mainnet" else "ST"
            error_label.update(f"[red]❌ Must be 41 chars and start with {prefix}[/red]")

    @on(Input.Changed, "#privkey-input")
    def on_privkey_changed(self, event: Input.Changed) -> None:
        """Real-time validation for Private Key."""
        error_label = self.query_one("#privkey-error", Label)
        if not event.value or event.value == "your_private_key_here":
            event.input.remove_class("error")
            error_label.update("")
        elif validate_private_key(event.value):
            event.input.remove_class("error")
            error_label.update("")
        else:
            event.input.add_class("error")
            error_label.update("[red]❌ Must be a 64 or 66 character hex string[/red]")

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
        save_btn = self.query_one("#save-config-btn", Button)
        original_label = save_btn.label

        # 🛡️ Sentinel: Collect values in the main thread for thread safety.
        # We also identify if the user is attempting to save a real secret.
        privkey_val = self.query_one("#privkey-input", Input).value
        address_val = self.query_one("#address-input", Input).value

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

            with open(self.config_path, "w", encoding="utf-8") as f:
                for key, value in config.items():
                    # 🛡️ Sentinel: Security Enforcer.
                    # Explicitly skip any known secrets or potential sensitive keys before saving to disk.
                    # This prevents accidental persistence of secrets to plaintext files.
                    if not is_sensitive_key(key):
                        f.write(f"{key}={value}\n")

            # 🛡️ Sentinel: Enforce secure file permissions
            set_secure_permissions(self.config_path)

        try:
            # 🛡️ Sentinel: Only save non-sensitive settings to the file.
            await asyncio.to_thread(_save_config_io, address_val)

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
