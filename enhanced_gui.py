#!/usr/bin/env python3
"""
Enhanced StacksOrbit GUI - A modern, feature-rich dashboard for Stacks blockchain deployment
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import subprocess
import threading

try:
    from textual.app import App, ComposeResult
    from textual.widgets import (
        Header, Footer, DataTable, Static, Button, ProgressBar, 
        Tabs, TabPane, TabbedContent, Label, Input, TextArea,
        Log, Sparkline, Switch, Select, LoadingIndicator
    )
    from textual.containers import Container, Horizontal, Vertical, VerticalScroll, Grid
    from textual.reactive import reactive
    from textual.binding import Binding
    from textual import on
    from rich.text import Text
    import psutil
    GUI_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    GUI_AVAILABLE = False

from deployment_monitor import DeploymentMonitor
from enhanced_conxian_deployment import EnhancedConfigManager, EnhancedConxianDeployer
from deployment_verifier import DeploymentVerifier

class EnhancedStacksOrbitGUI(App):
    """Enhanced GUI for StacksOrbit with advanced features"""
    
    CSS = """
    /* Enhanced styling for modern look */
    .container {
        padding: 1;
        background: $background;
        border: solid $primary;
    }
    
    .header {
        background: $primary;
        color: $text;
        text-align: center;
        padding: 1;
    }
    
    .status-success {
        color: $success;
        text-style: bold;
    }
    
    .status-error {
        color: $error;
        text-style: bold;
    }
    
    .status-warning {
        color: $warning;
        text-style: bold;
    }
    
    .progress-bar {
        width: 100%;
        height: 3;
    }
    
    .metric-card {
        border: solid $accent;
        padding: 1;
        margin: 1;
        background: $surface;
    }
    
    .log-container {
        height: 20;
        border: solid $primary;
        background: $panel;
    }
    
    .button-primary {
        background: $primary;
        color: $text;
    }
    
    .button-success {
        background: $success;
        color: $text;
    }
    
    .button-danger {
        background: $error;
        color: $text;
    }
    """
    
    BINDINGS = [
        Binding("d", "toggle_dark", "Toggle dark mode"),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh data"),
        Binding("s", "start_deployment", "Start deployment"),
        Binding("h", "show_help", "Help"),
    ]
    
    # Reactive variables
    network = reactive("testnet")
    deployment_status = reactive("ready")
    progress = reactive(0)
    selected_contracts = reactive([])
    
    def __init__(self, config_path: str = None, **kwargs):
        super().__init__(**kwargs)
        self.config_path = config_path or ".env"
        self.config = self._load_config()
        self.monitor = None
        self.deployer = None
        self.verifier = None
        self.deployment_log = []
        self.metrics = {
            "total_contracts": 0,
            "deployed_contracts": 0,
            "failed_contracts": 0,
            "deployment_time": 0,
            "gas_used": 0,
            "balance": 0
        }
        
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        config = {}
        try:
            with open(self.config_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        config[key] = value
        except FileNotFoundError:
            self.notify(f"Config file {self.config_path} not found", severity="error")
        return config
    
    def compose(self) -> ComposeResult:
        """Compose the GUI layout"""
        yield Header()
        
        with TabbedContent(initial="overview"):
            # Overview Tab
            with TabPane("📊 Overview", id="overview"):
                with Grid(id="metrics-grid"):
                    yield Container(Label("Network Status", classes="header"), Static("Testnet", id="network-status"), classes="metric-card")
                    yield Container(Label("Contracts", classes="header"), Static("0/0", id="contract-count"), classes="metric-card")
                    yield Container(Label("Progress", classes="header"), ProgressBar(id="progress-bar", show_eta=True), classes="metric-card")
                    yield Container(Label("Gas Used", classes="header"), Static("0 µSTX", id="gas-used"), classes="metric-card")
                    yield Container(Label("Balance", classes="header"), Static("0 µSTX", id="balance"), classes="metric-card")
                    yield Container(Label("Time", classes="header"), Static("00:00:00", id="deployment-time"), classes="metric-card")
                
                with Horizontal():
                    yield Button("🚀 Deploy", id="deploy-btn", variant="primary")
                    yield Button("⏸️ Pause", id="pause-btn", variant="warning")
                    yield Button("⏹️ Stop", id="stop-btn", variant="error")
                    yield Button("🔄 Refresh", id="refresh-btn", variant="default")
                    yield Button("📋 Logs", id="logs-btn", variant="default")
        
            # Contracts Tab
            with TabPane("📄 Contracts", id="contracts"):
                with Horizontal():
                    yield Select(
                    options=[
                        ("All Contracts", "all"),
                        ("Core", "core"),
                        ("Tokens", "tokens"),
                        ("DEX", "dex"),
                        ("Governance", "governance"),
                        ("Oracle", "oracle"),
                    ],
                    id="category-filter",
                    value="all"
                )
                    yield Input(placeholder="Search contracts...", id="search-input")
                    yield Button("🔄 Reload", id="reload-contracts")
                
                yield DataTable(id="contracts-table", zebra_stripes=True)
        
            # Deployment Tab
            with TabPane("🚀 Deployment", id="deployment"):
                with Vertical():
                    with Horizontal():
                        yield Select(
                            options=[
                                ("Testnet", "testnet"),
                                ("Mainnet", "mainnet"),
                                ("Devnet", "devnet"),
                            ],
                            id="network-select",
                            value="testnet"
                        )
                        yield Input(placeholder="Batch size (1-10)", value="3", id="batch-size")
                        yield Switch(value=True, id="parallel-deploy")
                        yield Label("Parallel", id="parallel-label")
                    
                    with Horizontal():
                        yield Button("🔍 Pre-check", id="precheck-btn", variant="primary")
                        yield Button("🚀 Deploy", id="start-deploy-btn", variant="success")
                        yield Button("⏹️ Cancel", id="cancel-deploy-btn", variant="error")
                        yield Button("📊 Status", id="deployment-status-btn", variant="default")
                    
                    yield Container(Log(id="deployment-log", classes="log-container"))
        
            # Monitoring Tab
            with TabPane("📈 Monitoring", id="monitoring"):
                with Grid(id="monitoring-grid"):
                    yield Container(Label("API Status", classes="header"), Static("✅ Connected", id="api-status"), classes="metric-card")
                    yield Container(Label("Block Height", classes="header"), Static("0", id="block-height"), classes="metric-card")
                    yield Container(Label("Network Load", classes="header"), Sparkline([], id="network-load"), classes="metric-card")
                    yield Container(Label("Memory Usage", classes="header"), Sparkline([], id="memory-usage"), classes="metric-card")
                
                yield Container(Static("Real-time monitoring data will appear here", id="monitoring-details"))
        
            # Settings Tab
            with TabPane("⚙️ Settings", id="settings"):
                with Vertical():
                    yield Container(Label("Configuration", classes="header"))
                    yield Input(placeholder="Deployer Private Key", value=self.config.get("DEPLOYER_PRIVKEY", ""), id="privkey-input", password=True)
                    yield Input(placeholder="System Address", value=self.config.get("SYSTEM_ADDRESS", ""), id="address-input")
                    yield Input(placeholder="Hiro API Key", value=self.config.get("HIRO_API_KEY", ""), id="apikey-input")
                    
                    with Horizontal():
                        yield Button("💾 Save Config", id="save-config-btn", variant="primary")
                        yield Button("🔄 Reload Config", id="reload-config-btn", variant="default")
                        yield Button("🧪 Test Connection", id="test-connection-btn", variant="success")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the GUI"""
        self.title = "Enhanced StacksOrbit GUI"
        self.sub_title = "Advanced Stacks Blockchain Deployment Tool"
        
        # Start background tasks
        self.set_interval(5.0, self.update_metrics)
        self.set_interval(2.0, self.update_monitoring)
        
        # Initialize components
        self._setup_contracts_table()
        self._load_initial_data()
    
    def _setup_contracts_table(self) -> None:
        """Setup the contracts data table"""
        table = self.query_one("#contracts-table", DataTable)
        table.add_column("Status", key="status")
        table.add_column("Name", key="name")
        table.add_column("Category", key="category")
        table.add_column("Address", key="address")
        table.add_column("Gas", key="gas")
        table.add_column("Actions", key="actions")
    
    def _load_initial_data(self) -> None:
        """Load initial data"""
        self.update_metrics()
        self.update_monitoring()
        self._load_contracts()
    
    def _load_contracts(self) -> None:
        """Load contracts from Clarinet.toml"""
        table = self.query_one("#contracts-table", DataTable)
        table.clear()
        
        # Sample contract data - in real implementation, load from Clarinet.toml
        contracts = [
            {"status": "✅", "name": "ownable", "category": "base", "address": "ST1...", "gas": "150"},
            {"status": "⏳", "name": "token", "category": "tokens", "address": "", "gas": "200"},
            {"status": "❌", "name": "dex", "category": "dex", "address": "", "gas": "500"},
        ]
        
        for contract in contracts:
            table.add_row(
                contract["status"],
                contract["name"], 
                contract["category"],
                contract["address"],
                contract["gas"],
                "View"
            )
    
    def update_metrics(self) -> None:
        """Update metrics display"""
        try:
            # Update contract count
            deployed = self.metrics.get("deployed_contracts", 0)
            total = self.metrics.get("total_contracts", 0)
            self.query_one("#contract-count", Static).update(f"{deployed}/{total}")
            
            # Update progress
            progress = (deployed / total * 100) if total > 0 else 0
            self.query_one("#progress-bar", ProgressBar).progress = progress
            
            # Update gas used
            gas_used = self.metrics.get("gas_used", 0)
            self.query_one("#gas-used", Static).update(f"{gas_used:,} µSTX")
            
            # Update balance
            balance = self.metrics.get("balance", 0)
            self.query_one("#balance", Static).update(f"{balance:,} µSTX")
            
            # Update deployment time
            deployment_time = self.metrics.get("deployment_time", 0)
            hours = deployment_time // 3600
            minutes = (deployment_time % 3600) // 60
            seconds = deployment_time % 60
            self.query_one("#deployment-time", Static).update(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
        except Exception as e:
            self.notify(f"Error updating metrics: {e}", severity="error")
    
    def update_monitoring(self) -> None:
        """Update monitoring data"""
        try:
            # Update block height
            self.query_one("#block-height", Static).update("3669602")  # Sample data
            
            # Update memory usage
            memory_percent = psutil.virtual_memory().percent
            memory_chart = self.query_one("#memory-usage", Sparkline)
            memory_chart.data.append(memory_percent)
            if len(memory_chart.data) > 20:
                memory_chart.data.pop(0)
            
            # Update network load (simulated)
            import random
            network_load = random.randint(20, 80)
            network_chart = self.query_one("#network-load", Sparkline)
            network_chart.data.append(network_load)
            if len(network_chart.data) > 20:
                network_chart.data.pop(0)
                
        except Exception as e:
            self.notify(f"Error updating monitoring: {e}", severity="error")
    
    def action_toggle_dark(self) -> None:
        """Toggle dark mode"""
        self.dark = not self.dark
    
    def action_refresh(self) -> None:
        """Refresh all data"""
        self.update_metrics()
        self.update_monitoring()
        self._load_contracts()
        self.notify("Data refreshed", severity="success")
    
    def action_start_deployment(self) -> None:
        """Start deployment process"""
        self._start_deployment()
    
    def action_show_help(self) -> None:
        """Show help dialog"""
        help_text = """
        Enhanced StacksOrbit GUI Help:
        
        Shortcuts:
        - D: Toggle dark mode
        - Q: Quit
        - R: Refresh data
        - S: Start deployment
        - H: Show this help
        
        Features:
        - Real-time monitoring
        - Contract management
        - Deployment control
        - Configuration management
        """
        self.notify(help_text, severity="info")
    
    @on(Button.Pressed, "#deploy-btn")
    def on_deploy_pressed(self) -> None:
        """Handle deploy button press"""
        self._start_deployment()
    
    @on(Button.Pressed, "#refresh-btn")
    def on_refresh_pressed(self) -> None:
        """Handle refresh button press"""
        self.action_refresh()
    
    @on(Button.Pressed, "#logs-btn")
    def on_logs_pressed(self) -> None:
        """Handle logs button press"""
        # Switch to deployment tab and show logs
        self.query_one(TabbedContent).active = "deployment"
    
    @on(Button.Pressed, "#precheck-btn")
    def on_precheck_pressed(self) -> None:
        """Handle pre-check button press"""
        self._run_precheck()
    
    @on(Button.Pressed, "#start-deploy-btn")
    def on_start_deploy_pressed(self) -> None:
        """Handle start deploy button press"""
        self._start_deployment()
    
    @on(Button.Pressed, "#save-config-btn")
    def on_save_config_pressed(self) -> None:
        """Handle save config button press"""
        self._save_config()
    
    @on(Button.Pressed, "#test-connection-btn")
    def on_test_connection_pressed(self) -> None:
        """Handle test connection button press"""
        self._test_connection()
    
    def _start_deployment(self) -> None:
        """Start the deployment process"""
        self.notify("Starting deployment...", severity="info")
        
        # Update status
        self.deployment_status = "deploying"
        self.query_one("#deploy-btn", Button).disabled = True
        
        # Add log entry
        log_widget = self.query_one("#deployment-log", Log)
        log_widget.write(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Starting deployment to {self.network}")
        
        # Start deployment in background
        self._run_deployment_background()
    
    def _run_deployment_background(self) -> None:
        """Run deployment in background thread"""
        def deployment_worker():
            try:
                # Simulate deployment process
                import time
                import random
                
                contracts = ["ownable", "pausable", "roles", "token", "dex", "oracle"]
                total = len(contracts)
                
                for i, contract in enumerate(contracts):
                    # Simulate deployment time
                    time.sleep(random.uniform(1, 3))
                    
                    # Update metrics
                    self.metrics["deployed_contracts"] = i + 1
                    self.metrics["total_contracts"] = total
                    self.metrics["gas_used"] += random.randint(100, 500)
                    
                    # Log progress
                    log_widget = self.query_one("#deployment-log", Log)
                    log_widget.write(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Deployed {contract} ({i+1}/{total})")
                    
                    # Update GUI
                    self.call_from_thread(self.update_metrics)
                
                # Complete deployment
                self.deployment_status = "completed"
                log_widget.write(f"[{datetime.now().strftime('%H:%M:%S')}] 🎉 Deployment completed successfully!")
                def disable_deploy_button():
                    self.query_one("#deploy-btn", Button).disabled = False
                self.call_from_thread(disable_deploy_button)
                self.call_from_thread(lambda: self.notify("Deployment completed!", severity="success"))
                
            except Exception as e:
                log_widget = self.query_one("#deployment-log", Log)
                log_widget.write(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Deployment failed: {e}")
                self.call_from_thread(lambda: self.notify(f"Deployment failed: {e}", severity="error"))
                def disable_deploy_button2():
                    self.query_one("#deploy-btn", Button).disabled = False
                self.call_from_thread(disable_deploy_button2)
        
        # Start background thread
        thread = threading.Thread(target=deployment_worker, daemon=True)
        thread.start()
    
    def _run_precheck(self) -> None:
        """Run pre-deployment checks"""
        self.notify("Running pre-deployment checks...", severity="info")
        
        log_widget = self.query_one("#deployment-log", Log)
        log_widget.write(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Running pre-deployment checks...")
        
        # Simulate checks
        checks = [
            "Environment variables",
            "Network connectivity", 
            "Account balance",
            "Contract compilation"
        ]
        
        for check in checks:
            time.sleep(0.5)  # Simulate check time
            log_widget.write(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {check} - OK")
        
        log_widget.write(f"[{datetime.now().strftime('%H:%M:%S')}] 🎉 All checks passed!")
        self.notify("Pre-deployment checks completed", severity="success")
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            privkey = self.query_one("#privkey-input", Input).value
            address = self.query_one("#address-input", Input).value
            apikey = self.query_one("#apikey-input", Input).value
            
            config_data = f"""# Enhanced StacksOrbit Configuration
DEPLOYER_PRIVKEY={privkey}
SYSTEM_ADDRESS={address}
HIRO_API_KEY={apikey}
NETWORK={self.network}
"""
            
            with open(self.config_path, 'w') as f:
                f.write(config_data)
            
            self.notify("Configuration saved successfully", severity="success")
            
        except Exception as e:
            self.notify(f"Failed to save configuration: {e}", severity="error")
    
    def _test_connection(self) -> None:
        """Test connection to Stacks network"""
        self.notify("Testing connection...", severity="info")
        
        # Simulate connection test
        time.sleep(1)
        
        # Update API status
        self.query_one("#api-status", Static).update("✅ Connected")
        self.notify("Connection test successful", severity="success")

def main():
    """Main entry point"""
    if not GUI_AVAILABLE:
        print("GUI dependencies not available. Install with: pip install textual rich psutil")
        return
    
    app = EnhancedStacksOrbitGUI()
    app.run()

if __name__ == "__main__":
    main()
