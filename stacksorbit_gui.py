#!/usr/bin/env python3
"""
StacksOrbit GUI - A modern, feature-rich dashboard for Stacks blockchain deployment
"""

import asyncio
import subprocess
import threading
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
    from textual import on

    GUI_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    GUI_AVAILABLE = False

from deployment_monitor import DeploymentMonitor
from stacksorbit_secrets import SECRET_KEYS


class StacksOrbitGUI(App):
    """A Textual dashboard for StacksOrbit."""

    CSS_PATH = "stacksorbit_gui.tcss"

    BINDINGS = [
        Binding("d", "toggle_dark", "Toggle dark mode"),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh data"),
    ]

    # Reactive variables
    network = reactive("testnet")

    def __init__(self, config_path: str = ".env", **kwargs):
        super().__init__(**kwargs)
        self.config_path = config_path
        self.config = self._load_config()
        self.network = self.config.get("NETWORK", "testnet")
        self.address = self.config.get("SYSTEM_ADDRESS", "Not configured")
        self.monitor = DeploymentMonitor(self.network, self.config)
        self._manual_refresh_in_progress = False

    def _load_config(self) -> Dict:
        """Load configuration from file"""
        config = {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip().strip('"').strip("'")
        except FileNotFoundError:
            # app.notify might not be available yet in __init__
            print(f"Config file {self.config_path} not found")
        except Exception as e:
            # 🛡️ Sentinel: Prevent sensitive information disclosure.
            print("Error loading configuration from file.")
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
                    )
                    yield Container(
                        Label("Contracts Deployed"),
                        Static("0", id="contract-count"),
                        classes="metric-card",
                    )
                    yield Container(
                        Label("Balance"),
                        Static("0 STX", id="balance"),
                        classes="metric-card",
                    )
                    yield Container(
                        Label("Nonce"), Static("0", id="nonce"), classes="metric-card"
                    )
                    yield Container(
                        Label("Block Height"),
                        Static("0", id="block-height"),
                        classes="metric-card",
                    )
                with Horizontal(id="overview-buttons"):
                    yield Button(
                        "🔄 Refresh",
                        id="refresh-btn",
                        tooltip="Refresh all dashboard data [r]",
                    )

            with TabPane("📄 Contracts", id="contracts"):
                with Horizontal():
                    yield DataTable(id="contracts-table", zebra_stripes=True)
                    yield Vertical(
                        Label("Contract Details", classes="header"),
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

            with TabPane("🚀 Deploy", id="deployment"):
                with Vertical():
                    yield LoadingIndicator()
                    yield Log(id="deployment-log")
                    with Horizontal():
                        yield Button(
                            "🔍 Pre-check",
                            id="precheck-btn",
                            variant="primary",
                            tooltip="Run diagnostic checks before deployment",
                        )
                        yield Button(
                            "🚀 Deploy",
                            id="start-deploy-btn",
                            variant="primary",
                            tooltip="Start the deployment process",
                        )
                        yield Button(
                            "🗑️ Clear",
                            id="clear-log-btn",
                            variant="error",
                            tooltip="Clear the deployment log",
                        )

            with TabPane("⚙️ Settings", id="settings"):
                with VerticalScroll():
                    yield Label("Private Key:")
                    with Horizontal(classes="input-group"):
                        yield Input(
                            placeholder="Your private key",
                            value=self.config.get("DEPLOYER_PRIVKEY", ""),
                            id="privkey-input",
                            password=True,
                        )
                        yield Label("Show", classes="switch-label")
                        yield Switch(
                            id="show-privkey", tooltip="Toggle private key visibility"
                        )
                    yield Label("Stacks Address:")
                    yield Input(
                        placeholder="Your STX address",
                        value=self.config.get("SYSTEM_ADDRESS", ""),
                        id="address-input",
                    )
                    yield Button(
                        "💾 Save",
                        id="save-config-btn",
                        variant="primary",
                        tooltip="Save settings to .env file",
                    )

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the GUI"""
        self.title = "StacksOrbit"
        self.sub_title = "Deployment Dashboard"
        for indicator in self.query(LoadingIndicator):
            indicator.display = False

        # 🎨 Palette: Add tooltips to widgets that don't support them in constructor
        self.query_one("#contracts-table", DataTable).tooltip = (
            "List of contracts deployed by this address"
        )
        self.query_one("#transactions-table", DataTable).tooltip = (
            "Recent transactions for this address"
        )

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

        self._setup_tables()
        self.set_interval(10.0, self.update_data)
        self.run_worker(self.update_data())

    def _setup_tables(self) -> None:
        """Setup the data tables"""
        contracts_table = self.query_one("#contracts-table", DataTable)
        contracts_table.add_columns("Status", "Name", "Address")

        transactions_table = self.query_one("#transactions-table", DataTable)
        transactions_table.add_columns("TX ID", "Type", "Status", "Block")

    async def update_data(self) -> None:
        """Update all data in the GUI concurrently."""
        for indicator in self.query(LoadingIndicator):
            indicator.display = True
        contracts_table = self.query_one("#contracts-table", DataTable)
        transactions_table = self.query_one("#transactions-table", DataTable)
        contracts_table.clear()
        transactions_table.clear()

        try:
            # ⚡ Bolt: Run synchronous API calls concurrently in threads
            # This prevents the UI from blocking and speeds up the data refresh
            # by fetching all data in parallel instead of one by one.
            api_status_task = asyncio.to_thread(self.monitor.check_api_status)

            if self.address != "Not configured":
                account_info_task = asyncio.to_thread(
                    self.monitor.get_account_info, self.address
                )
                contracts_task = asyncio.to_thread(
                    self.monitor.get_deployed_contracts, self.address
                )
                transactions_task = asyncio.to_thread(
                    self.monitor.get_recent_transactions, self.address
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
                contracts_table.add_row("Address not configured in .env file.")
                transactions_table.add_row("Address not configured in .env file.")

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

            # Process transactions result
            if isinstance(transactions, Exception):
                raise transactions
            if transactions:
                for tx in transactions:
                    transactions_table.add_row(
                        tx.get("tx_id", "")[:10] + "...",
                        tx.get("tx_type", ""),
                        tx.get("tx_status", ""),
                        str(tx.get("block_height", "")),
                    )
            elif self.address != "Not configured":
                transactions_table.add_row("", "No transactions found", "", "")

        except Exception as e:
            self.query_one("#network-status").update("[red]Error[/]")
            self.notify(f"API error: {e}", severity="error")
        finally:
            for indicator in self.query(LoadingIndicator):
                indicator.display = False

    @on(DataTable.RowSelected, "#contracts-table")
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # ⚡ Bolt: This event handler was previously decorated twice, causing it to
        # fire two times for every click. The redundant decorator was removed to
        # prevent duplicate API calls and unnecessary processing.
        """Handle contract row selection."""
        contract_id = event.row_key.value
        if contract_id:
            self.run_worker(self.fetch_contract_details(contract_id), exclusive=True)

    async def fetch_contract_details(self, contract_id: str) -> None:
        """Worker to fetch and display contract details."""
        details_pane = self.query(".details-pane").first()
        md = details_pane.query_one(Markdown)
        loader = details_pane.query_one(LoadingIndicator)

        md.update("")
        loader.display = True
        try:
            details = await self.monitor.get_contract_details(contract_id)
            if details:
                md.update(
                    f"**Source Code:**\n```clarity\n{details.get('source_code', 'Not available.')}\n```"
                )
            else:
                md.update("Could not retrieve contract details.")
        finally:
            loader.display = False

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

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
            await self.update_data()
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

    @on(Button.Pressed, "#save-config-btn")
    async def on_save_config_pressed(self) -> None:
        """Handle save config button press with visual feedback."""
        save_btn = self.query_one("#save-config-btn", Button)
        original_label = save_btn.label

        # 🛡️ Sentinel: Collect values in the main thread for thread safety.
        # We also identify if the user is attempting to save a real secret.
        privkey_val = self.query_one("#privkey-input", Input).value
        address_val = self.query_one("#address-input", Input).value

        # Check if the private key is a real secret (not empty or placeholder)
        is_secret_provided = (
            privkey_val.strip() != ""
            and privkey_val.strip().lower() != "your_private_key_here"
        )

        save_btn.disabled = True
        save_btn.label = "Saving..."

        # 🎨 Palette: This function handles the file I/O.
        # By running it in a thread, we prevent the UI from freezing.
        def _save_config_io(p_address: str):
            config = self._load_config()

            # Update non-sensitive configuration
            config["SYSTEM_ADDRESS"] = p_address

            with open(self.config_path, "w", encoding="utf-8") as f:
                for key, value in config.items():
                    # 🛡️ Sentinel: Security Enforcer.
                    # We explicitly skip any known secrets before saving to disk.
                    # This ensures that secrets are only handled in-memory or
                    # via environment variables.
                    if key not in SECRET_KEYS:
                        f.write(f"{key}={value}\n")

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

            # 🎨 Palette: Provide clear, temporary success feedback on the button.
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
