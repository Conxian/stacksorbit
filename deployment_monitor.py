#!/usr/bin/env python3
"""
Comprehensive Deployment Monitoring System for Conxian
Real-time monitoring and verification using Hiro API
"""

import os
import json
import time
import requests
import functools
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
import argparse

# Setup colored logging
try:
    import colorama
    from colorama import Fore, Style
    colorama.init()
    USE_COLORS = True
except ImportError:
    USE_COLORS = False

def cache_api_call(func):
    """Decorator to cache API calls with a timeout."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Create a cache key from the function name and arguments
        # Note: This is a simple key generation strategy. For complex arguments,
        # a more robust method (like hashing a serialized version of args) might be needed.
        key_args = [str(arg) for arg in args]
        key_kwargs = [f"{k}={v}" for k, v in sorted(kwargs.items())]
        cache_key = f"{func.__name__}_{'_'.join(key_args)}_{'_'.join(key_kwargs)}"

        with self.cache_lock:
            cached_data = self.cache.get(cache_key)
            if cached_data and (time.time() - cached_data['timestamp']) < self.cache_expiry:
                self.logger.debug(f"Cache hit for {cache_key}")
                return cached_data['data']

        self.logger.debug(f"Cache miss for {cache_key}, fetching from API")
        # Execute the function if no valid cache entry is found
        result = func(self, *args, **kwargs)

        # Store the new result in the cache
        with self.cache_lock:
            self.cache[cache_key] = {
                'timestamp': time.time(),
                'data': result
            }
        return result
    return wrapper


class DeploymentMonitor:
    """Real-time deployment monitoring with Hiro API integration"""

    def __init__(self, network: str = 'testnet', config: Dict = None):
        self.network = network
        self.config = config or {}
        self.api_url = self._get_api_url()
        self.session = requests.Session()
        self.session.timeout = 30

        # Monitoring state
        self.is_monitoring = False
        self.deployment_history = []
        self.contracts_deployed = set()
        self.failed_contracts = set()

        # Bolt ⚡: Add in-memory cache to reduce redundant API calls
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.cache_expiry = 30  # Cache for 30 seconds

        # Setup logging
        self.setup_logging()

    def _get_api_url(self) -> str:
        """Get API URL for network"""
        urls = {
            'mainnet': 'https://api.hiro.so',
            'testnet': 'https://api.testnet.hiro.so',
            'devnet': 'http://localhost:20443'
        }
        return urls.get(self.network, urls['testnet'])

    def setup_logging(self):
        """Setup comprehensive logging"""
        log_level = getattr(logging, self.config.get('LOG_LEVEL', 'INFO').upper())

        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Setup main logger
        self.logger = logging.getLogger('conxian_deployment')
        self.logger.setLevel(log_level)

        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # File handler
        if self.config.get('SAVE_LOGS', 'true').lower() == 'true':
            log_file = log_dir / f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        if USE_COLORS:
            class ColoredFormatter(logging.Formatter):
                def format(self, record):
                    message = super().format(record)
                    if record.levelno >= logging.ERROR:
                        return f"{Fore.RED}{message}{Style.RESET_ALL}"
                    elif record.levelno >= logging.WARNING:
                        return f"{Fore.YELLOW}{message}{Style.RESET_ALL}"
                    elif record.levelno >= logging.INFO:
                        return f"{Fore.GREEN}{message}{Style.RESET_ALL}"
                    return message

            console_formatter = ColoredFormatter('%(levelname)s: %(message)s')
        else:
            console_formatter = logging.Formatter('%(levelname)s: %(message)s')

        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

    def start_monitoring(self, callback: Optional[Callable] = None):
        """Start real-time monitoring"""
        self.is_monitoring = True
        self.logger.info("🚀 Starting deployment monitoring...")

        # Initial API check
        self.check_api_status()

        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitoring_loop, args=(callback,))
        monitor_thread.daemon = True
        monitor_thread.start()

        return monitor_thread

    def _monitoring_loop(self, callback: Optional[Callable] = None):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                self._check_for_new_deployments()
                self._check_network_health()

                if callback:
                    callback(self.get_monitoring_status())

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(30)  # Wait longer on errors

    def _check_for_new_deployments(self):
        """Check for new contract deployments"""
        address = self.config.get('SYSTEM_ADDRESS')
        if not address:
            return

        try:
            # Get account info
            account_info = self.get_account_info(address)
            if not account_info:
                return

            nonce_raw = account_info.get('nonce', 0)
            current_nonce = int(nonce_raw, 16) if isinstance(nonce_raw, str) and nonce_raw.startswith('0x') else int(nonce_raw)

            # Check if we have new transactions
            if current_nonce > len(self.deployment_history):
                self.logger.info(f"📦 New deployment detected! Nonce: {current_nonce}")
                self._analyze_new_deployment(current_nonce)

        except Exception as e:
            self.logger.error(f"Error checking deployments: {e}")

    def _analyze_new_deployment(self, nonce: int):
        """Analyze new deployment transaction"""
        address = self.config.get('SYSTEM_ADDRESS')
        if not address:
            return

        try:
            # This would typically involve analyzing the transaction
            # For now, we'll just log the deployment
            deployment_info = {
                'timestamp': datetime.now().isoformat(),
                'nonce': nonce,
                'network': self.network,
                'address': address
            }

            self.deployment_history.append(deployment_info)
            self.logger.info(f"📋 New deployment recorded: nonce {nonce}")

        except Exception as e:
            self.logger.error(f"Error analyzing deployment: {e}")

    def _check_network_health(self):
        """Check network health and performance"""
        try:
            api_status = self.check_api_status()
            if api_status['status'] != 'online':
                self.logger.warning(f"🌐 Network connectivity issue: {api_status.get('error', 'Unknown')}")

        except Exception as e:
            self.logger.error(f"Network health check failed: {e}")

    @cache_api_call
    def check_api_status(self) -> Dict:
        """Check Hiro API status."""
        try:
            response = self.session.get(f"{self.api_url}/v2/info", timeout=10)
            response.raise_for_status()
            data = response.json()

            status = {
                'status': 'online',
                'block_height': data.get('stacks_tip_height', 0),
                'network_id': data.get('network_id', 'unknown'),
                'server_version': data.get('server_version', 'unknown'),
                'burn_block_height': data.get('burn_block_height', 0),
                'tps': data.get('tps', 0)
            }
            self.logger.debug(f"API Status: {status['network_id']} @ {status['block_height']}")
            return status

        except Exception as e:
            self.logger.error(f"API status check failed: {e}")
            return {'status': 'offline', 'error': str(e)}

    @cache_api_call
    def get_account_info(self, address: str) -> Optional[Dict]:
        """Get comprehensive account information."""
        try:
            response = self.session.get(f"{self.api_url}/v2/accounts/{address}")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None

    @cache_api_call
    def get_transaction_info(self, tx_id: str) -> Optional[Dict]:
        """Get detailed transaction information"""
        try:
            response = self.session.get(f"{self.api_url}/v2/transactions/{tx_id}")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error(f"Error getting transaction info: {e}")
            return None

    def wait_for_transaction(self, tx_id: str, timeout: int = 300) -> Optional[Dict]:
        """Wait for transaction confirmation with exponential backoff."""
        self.logger.info(f"⏳ Waiting for transaction confirmation: {tx_id}")

        start_time = time.time()
        last_status = None
        # Bolt ⚡: Implement exponential backoff for polling.
        # This reduces the number of API calls for long-running transactions by
        # starting with a short polling interval and increasing it over time.
        # This is more efficient than a fixed interval.
        poll_interval = 2  # Start with a 2-second interval
        max_poll_interval = 30  # Cap at 30 seconds

        while time.time() - start_time < timeout:
            tx_info = self.get_transaction_info(tx_id)

            if tx_info:
                status = tx_info.get('tx_status', 'unknown')

                if status != last_status:
                    self.logger.info(f"📊 Transaction status: {status}")
                    last_status = status
                    poll_interval = 2  # Reset interval on status change

                if status == 'success':
                    self.logger.info("✅ Transaction confirmed successfully!")
                    return tx_info
                elif status == 'error':
                    self.logger.error(f"❌ Transaction failed: {tx_info.get('tx_result', 'Unknown error')}")
                    return tx_info

            time.sleep(poll_interval)
            poll_interval = min(poll_interval * 2, max_poll_interval)

        self.logger.warning("⏰ Transaction confirmation timeout")
        return None

    def wait_for_confirmation(self, tx_id: str, timeout: int = 300) -> bool:
        """Wait for transaction confirmation, returns boolean for compatibility."""
        tx_info = self.wait_for_transaction(tx_id, timeout)
        return tx_info is not None and tx_info.get('tx_status') == 'success'

    def get_transaction_status(self, tx_id: str) -> Optional[Dict]:
        """Alias for get_transaction_info for compatibility."""
        return self.get_transaction_info(tx_id)

    @cache_api_call
    def get_deployed_contracts(self, address: str) -> List[Dict]:
        """Get list of deployed contracts."""
        try:
            response = self.session.get(f"{self.api_url}/v2/accounts/{address}/contracts")
            response.raise_for_status()
            data = response.json()

            contracts = data.get('contracts', [])
            self.logger.info(f"📦 Found {len(contracts)} deployed contracts")
            return contracts

        except Exception as e:
            self.logger.error(f"Error getting deployed contracts: {e}")
            return []

    @cache_api_call
    def get_recent_transactions(self, address: str, limit: int = 50) -> List[Dict]:
        """Get recent transactions for an address."""
        try:
            response = self.session.get(
                f"{self.api_url}/v2/accounts/{address}/transactions?limit={limit}",
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            self.logger.error(f"Error getting recent transactions: {e}")
            return []

    @cache_api_call
    def get_contract_details(self, contract_id: str) -> Optional[Dict]:
        """Get contract details, including source code."""
        try:
            # The contract_id is in the format 'address.name'
            address, name = contract_id.split('.')
            url = f"{self.api_url}/v2/contracts/interface/{address}/{name}"
            response = self.session.get(url)
            response.raise_for_status()
            # We are primarily interested in the source code
            source_data = response.json()
            return {"source_code": source_data.get("source", "Source not available")}
        except Exception as e:
            self.logger.error(f"Error getting contract details for {contract_id}: {e}")
            return None

    def verify_deployment(self, expected_contracts: List[str], address: str) -> Dict:
        """Verify deployment completeness"""
        self.logger.info("🔍 Verifying deployment...")

        deployed_contracts = self.get_deployed_contracts(address)
        deployed_names = [c.get('contract_id', '').split('.')[-1] for c in deployed_contracts]

        verification = {
            'timestamp': datetime.now().isoformat(),
            'network': self.network,
            'address': address,
            'expected': expected_contracts,
            'deployed': deployed_names,
            'verified': [],
            'missing': [],
            'extra': []
        }

        # Check expected contracts
        for contract in expected_contracts:
            if contract in deployed_names:
                verification['verified'].append(contract)
                self.logger.info(f"✅ {contract}")
            else:
                verification['missing'].append(contract)
                self.logger.error(f"❌ {contract} (missing)")

        # Check for unexpected contracts
        for deployed in deployed_names:
            if deployed not in expected_contracts:
                verification['extra'].append(deployed)
                self.logger.warning(f"⚠️  {deployed} (unexpected)")

        # Summary
        verification['success'] = len(verification['missing']) == 0

        self.logger.info("📊 Verification Summary:")
        self.logger.info(f"   Expected: {len(verification['expected'])}")
        self.logger.info(f"   Verified: {len(verification['verified'])}")
        self.logger.info(f"   Missing: {len(verification['missing'])}")
        self.logger.info(f"   Extra: {len(verification['extra'])}")

        return verification

    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        api_status = self.check_api_status()

        address = self.config.get('SYSTEM_ADDRESS')
        account_info = None
        deployed_contracts = []

        if address:
            account_info = self.get_account_info(address)
            deployed_contracts = self.get_deployed_contracts(address)

        return {
            'monitoring_active': self.is_monitoring,
            'api_status': api_status,
            'account_info': account_info,
            'deployed_contracts': len(deployed_contracts),
            'deployment_history': len(self.deployment_history),
            'timestamp': datetime.now().isoformat()
        }

    def stop_monitoring(self):
        """Stop monitoring"""
        self.logger.info("🛑 Stopping deployment monitoring...")
        self.is_monitoring = False

        # Save monitoring summary
        self.save_monitoring_summary()

    def save_monitoring_summary(self):
        """Save monitoring summary to file"""
        summary = {
            'end_time': datetime.now().isoformat(),
            'network': self.network,
            'total_deployments': len(self.deployment_history),
            'contracts_deployed': len(self.contracts_deployed),
            'failed_contracts': len(self.failed_contracts),
            'monitoring_duration': 'unknown'  # Would need start time tracking
        }

        summary_path = Path("logs") / "monitoring_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        self.logger.info(f"💾 Monitoring summary saved to {summary_path}")

    def _show_deployment_cost_warnings(self, available_stx: float):
        """Show deployment cost warnings based on available balance"""
        # Estimate deployment costs (rough estimates)
        base_cost_per_contract = 0.5  # STX per contract
        max_contracts = 20  # Estimated max contracts to deploy
        total_estimated_cost = base_cost_per_contract * max_contracts

        print(f"\n💰 Deployment Cost Estimate:")
        print(f"   Estimated: {total_estimated_cost:,.2f} STX (for ~20 contracts)")

        if available_stx < 1.0:
            print(f"   {Fore.RED}⚠️  WARNING: Insufficient funds for deployment!{Style.RESET_ALL}")
            print(f"   {Fore.YELLOW}💡 Add STX to your wallet before deploying{Style.RESET_ALL}")
        elif available_stx < total_estimated_cost:
            print(f"   {Fore.YELLOW}⚠️  WARNING: Limited funds for full deployment{Style.RESET_ALL}")
            print(f"   {Fore.YELLOW}💡 Consider adding more STX or deploying fewer contracts{Style.RESET_ALL}")
        else:
            print(f"   {Fore.GREEN}✅ Sufficient funds for deployment{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}💡 Ready to deploy!{Style.RESET_ALL}")

def main():
    """Main monitoring CLI function"""
    parser = argparse.ArgumentParser(description='Conxian Deployment Monitor')
    parser.add_argument('--config', default='.env', help='Configuration file path')
    parser.add_argument('--network', choices=['devnet', 'testnet', 'mainnet'], default='testnet')
    parser.add_argument('--address', help='Address to monitor')
    parser.add_argument('--verify', nargs='*', help='Contracts to verify (space-separated)')
    parser.add_argument('--follow', action='store_true', help='Follow deployment in real-time')
    parser.add_argument('--timeout', type=int, default=300, help='Monitoring timeout in seconds')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    try:
        # Load configuration
        config = {}
        if Path(args.config).exists():
            with open(args.config, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"')

        # Override with command line arguments
        if args.network:
            config['NETWORK'] = args.network
        if args.address:
            config['SYSTEM_ADDRESS'] = args.address

        # Initialize monitor
        monitor = DeploymentMonitor(
            network=config.get('NETWORK', 'testnet'),
            config=config
        )

        if args.verbose:
            config['LOG_LEVEL'] = 'DEBUG'

        # Run specific monitoring tasks
        if args.verify:
            # Verification mode
            address = config.get('SYSTEM_ADDRESS')
            if not address:
                print("❌ No address specified for verification")
                return 1

            print("🔍 Running deployment verification...")
            verification = monitor.verify_deployment(args.verify, address)

            if verification['success']:
                print("✅ All expected contracts are deployed")
                return 0
            else:
                print(f"❌ Missing contracts: {verification['missing']}")
                return 1

        elif args.follow:
            # Real-time monitoring mode
            print("📊 Starting real-time deployment monitoring...")
            print("📝 Press Ctrl+C to stop monitoring\n")

            # Start monitoring
            monitor_thread = monitor.start_monitoring()

            try:
                # Keep main thread alive
                while monitor.is_monitoring:
                    time.sleep(1)

            except KeyboardInterrupt:
                print("\n🛑 Stopping monitor...")

            monitor.stop_monitoring()
            print("✅ Monitoring stopped")

        else:
            # One-time status check
            print("📊 Network Status:")
            api_status = monitor.check_api_status()
            print(f"   Status: {api_status['status']}")
            print(f"   Network: {api_status.get('network_id', 'unknown')}")
            print(f"   Block Height: {api_status.get('block_height', 0)}")

            address = config.get('SYSTEM_ADDRESS')
            if address:
                print(f"\n👤 Account Status:")
                account_info = monitor.get_account_info(address)
                if account_info:
                    balance_raw = account_info.get('balance', 0)
                    balance_microstx = int(balance_raw, 16) if isinstance(balance_raw, str) and balance_raw.startswith('0x') else int(balance_raw)
                    balance_stx = balance_microstx / 1000000
                    
                    locked_raw = account_info.get('locked', 0)
                    locked_balance = (int(locked_raw, 16) if isinstance(locked_raw, str) and locked_raw.startswith('0x') else int(locked_raw)) / 1000000
                    available_stx = balance_stx - locked_balance
                    nonce_raw = account_info.get('nonce', 0)
                    nonce = int(nonce_raw, 16) if isinstance(nonce_raw, str) and nonce_raw.startswith('0x') else int(nonce_raw)

                    # Helper function to get recent transactions
                    def get_recent_transactions(address, limit=10):
                        recent_transactions = monitor.get_recent_transactions(address, limit)
                        return recent_transactions
                    print(f"   Balance: {Fore.GREEN}{balance_stx:,.6f} STX{Style.RESET_ALL}")

                    if locked_balance > 0:
                        print(f"   Locked: {Fore.YELLOW}{locked_balance:,.6f} STX{Style.RESET_ALL}")

                    print(f"   Available: {Fore.BLUE}{available_stx:,.6f} STX{Style.RESET_ALL}")
                    print(f"   Nonce: {nonce}")

                    # Show deployment cost warnings
                    monitor._show_deployment_cost_warnings(available_stx)

                print(f"\n📦 Deployed Contracts:")
                contracts = monitor.get_deployed_contracts(address)
                for contract in contracts:
                    print(f"   - {contract.get('contract_id', 'unknown')}")

            return 0

    except KeyboardInterrupt:
        print("\n🛑 Monitoring cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
