#!/usr/bin/env python3
"""
Enhanced Monitoring Dashboard for StacksOrbit (Textual Version)
"""
import asyncio
import json
from pathlib import Path
import sys
import time
from typing import Dict
from textual.binding import Binding
from textual.widgets import Label, Button, DataTable, Footer, Header, Pretty, TabbedContent, TabPane
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.worker import Worker, get_current_worker
from textual import on
from deployment_monitor import DeploymentMonitor
from enhanced_conxian_deployment import EnhancedConfigManager

class StacksOrbitDashboard(App):
    """A Textual dashboard for StacksOrbit."""

    CSS_PATH = "dashboard.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit")
    ]

    def __init__(self, config: Dict, network: str = 'testnet', **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.network = network
        self.monitor = DeploymentMonitor(network, config)
        self.address = self.config.get('SYSTEM_ADDRESS', 'Not configured')
        self.data = {}

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        with TabbedContent(initial="overview"):
            with TabPane("Overview", id="overview"):
                yield VerticalScroll(
                    Label(f"Address: {self.address}", id="address"),
                    Horizontal(
                        Vertical(
                            Label("API Status:", classes="bold"),
                            Label(id="api_status"),
                            Label("Block Height:", classes="bold"),
                            Label(id="block_height"),
                            classes="overview_left"
                        ),
                        Vertical(
                            Label("Balance:", classes="bold"),
                            Label(id="balance"),
                            Label("Nonce:", classes="bold"),
                            Label(id="nonce"),
                            classes="overview_right"
                        )
                    )
                )
            with TabPane("Contracts", id="contracts"):
                yield DataTable()
            with TabPane("Network", id="network"):
                yield Pretty({})
            with TabPane("Transactions", id="transactions"):
                yield DataTable()
            with TabPane("Analytics", id="analytics"):
                yield Pretty({})


    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.update_data()

    @on(Button.Pressed)
    def handle_button_press(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "refresh":
            self.update_data()

    def update_data(self) -> None:
        """Update the data in the background."""
        self.run_worker(self._update_data)

    async def _update_data(self) -> None:
        """Background worker to update data."""
        while True:
            try:
                # API Status
                api_status = self.monitor.check_api_status()
                self.query_one("#api_status").update(f"[bold green]{api_status.get('status', 'unknown').upper()}[/]")
                self.query_one("#block_height").update(str(api_status.get('block_height', 0)))

                # Account Info
                account_info = self.monitor.get_account_info(self.address)
                if account_info:
                    balance_stx = int(account_info.get('balance', 0)) / 1_000_000
                    self.query_one("#balance").update(f"{balance_stx:,.6f} STX")
                    self.query_one("#nonce").update(str(account_info.get('nonce', 0)))

                # Deployed Contracts
                deployed_contracts = self.monitor.get_deployed_contracts(self.address)
                contracts_table = self.query("DataTable")[0]
                contracts_table.clear(columns=True)
                contracts_table.add_columns("Contract ID", "Status")
                for contract in deployed_contracts:
                    status = "✅" # Simplified for demo
                    contracts_table.add_row(contract.get('contract_id', 'unknown'), status)

                # Network Info
                network_info = self.monitor.check_api_status()
                self.query("Pretty")[0].update(network_info)

                # Transactions
                transactions = self.monitor.get_recent_transactions(self.address)
                transactions_table = self.query("DataTable")[1]
                transactions_table.clear(columns=True)
                transactions_table.add_columns("TX ID", "Type", "Status")
                for tx in transactions:
                    transactions_table.add_row(
                        tx.get('tx_id', 'unknown')[:10] + "...",
                        tx.get('tx_type', 'unknown'),
                        tx.get('tx_status', 'unknown')
                    )

            except Exception as e:
                self.query_one("#api_status").update(f"[bold red]Error: {e}[/]")

            await asyncio.sleep(5)

def main():
    """Main dashboard CLI function."""
    config_manager = EnhancedConfigManager('.env')
    config = config_manager.load_config()
    app = StacksOrbitDashboard(config=config)
    app.run()

if __name__ == "__main__":
    main()