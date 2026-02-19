#!/usr/bin/env python3
"""
Conxian Deployment Verification System
Comprehensive validation and testing of deployed contracts
"""

import os
import json
import time
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import monitoring components
from deployment_monitor import DeploymentMonitor
from stacksorbit_secrets import (
    SECRET_KEYS,
    is_sensitive_key,
    is_placeholder,
    save_secure_config,
    redact_recursive,
)


class DeploymentVerifier:
    """Comprehensive deployment verification system"""

    def __init__(self, network: str = "testnet", config: Dict = None):
        self.network = network
        self.config = config or {}
        self.verbose = self.config.get("VERBOSE", False) or self.config.get(
            "verbose", False
        )
        self.monitor = DeploymentMonitor(network, config)
        self.print_lock = threading.Lock()

        # Verification results
        self.verification_results = {
            "timestamp": datetime.now().isoformat(),
            "network": network,
            "overall_status": "unknown",
            "checks": {},
            "contracts": {},
            "recommendations": [],
        }

    def _safe_print(self, *args, **kwargs):
        """Thread-safe printing"""
        with self.print_lock:
            print(*args, **kwargs)

    def run_comprehensive_verification(
        self, expected_contracts: Optional[List[str]] = None
    ) -> Dict:
        """Run comprehensive deployment verification"""
        self._safe_print("🔍 Starting comprehensive deployment verification...\n")

        address = self.config.get("SYSTEM_ADDRESS")
        if not address:
            raise ValueError("SYSTEM_ADDRESS not configured")

        # Run all verification checks
        checks = [
            ("API Connectivity", self._verify_api_connectivity),
            ("Account Status", self._verify_account_status),
            ("Contract Deployment", self._verify_contract_deployment),
            ("Transaction History", self._verify_transaction_history),
            ("Network Health", self._verify_network_health),
            ("Gas Usage", self._verify_gas_usage),
            ("Contract Functionality", self._verify_contract_functionality),
        ]

        all_passed = True

        # Bolt ⚡: Parallelize verification checks to reduce total latency.
        # This is especially effective when network calls are involved.
        with ThreadPoolExecutor(max_workers=len(checks)) as executor:
            future_to_check = {
                executor.submit(check_func, address, expected_contracts): check_name
                for check_name, check_func in checks
            }

            for future in as_completed(future_to_check):
                check_name = future_to_check[future]
                try:
                    result = future.result()
                    self.verification_results["checks"][check_name] = result

                    if not result["passed"]:
                        all_passed = False
                        self._safe_print(
                            f"❌ {check_name} failed: {result.get('error', 'Unknown error')}"
                        )
                    else:
                        self._safe_print(f"✅ {check_name} passed")

                except Exception as e:
                    # 🛡️ Sentinel: Prevent sensitive information disclosure.
                    if self.verbose:
                        self._safe_print(f"❌ {check_name} error: {e}")
                    else:
                        self._safe_print(
                            f"❌ {check_name} error (use --verbose for details)"
                        )
                    self.verification_results["checks"][check_name] = {
                        "passed": False,
                        "error": str(e),
                    }
                    all_passed = False

        # Overall status
        self.verification_results["overall_status"] = (
            "success" if all_passed else "failed"
        )

        # Generate recommendations
        self._generate_recommendations()

        # Save verification results
        self._save_verification_results()

        return self.verification_results

    def _verify_api_connectivity(
        self, address: str, expected_contracts: Optional[List[str]] = None
    ) -> Dict:
        """Verify API connectivity and basic functionality"""
        api_status = self.monitor.check_api_status()

        passed = api_status["status"] == "online"
        return {
            "passed": passed,
            "details": api_status,
            "error": api_status.get("error") if not passed else None,
        }

    def _verify_account_status(
        self, address: str, expected_contracts: Optional[List[str]] = None
    ) -> Dict:
        """Verify account status and balance"""
        account_info = self.monitor.get_account_info(address)

        if not account_info:
            return {"passed": False, "error": "Could not retrieve account information"}

        balance = int(account_info.get("balance", 0)) / 1000000
        nonce = account_info.get("nonce", 0)

        # Basic validation
        min_balance = 1.0  # Minimum 1 STX
        passed = balance >= min_balance

        return {
            "passed": passed,
            "details": {"balance": balance, "nonce": nonce, "min_balance": min_balance},
            "error": f"Low balance: {balance} STX" if not passed else None,
        }

    def _verify_contract_deployment(
        self, address: str, expected_contracts: Optional[List[str]] = None
    ) -> Dict:
        """Verify contract deployment status"""
        deployed_contracts = self.monitor.get_deployed_contracts(address)

        if expected_contracts:
            deployed_names = [
                c.get("contract_id", "").split(".")[-1] for c in deployed_contracts
            ]
            # Bolt ⚡: Optimization - Use set for O(1) lookup to avoid O(N^2) complexity.
            deployed_names_set = set(deployed_names)

            verified = []
            missing = []

            for contract in expected_contracts:
                if contract in deployed_names_set:
                    verified.append(contract)
                else:
                    missing.append(contract)

            passed = len(missing) == 0

            return {
                "passed": passed,
                "details": {
                    "total_deployed": len(deployed_contracts),
                    "expected": len(expected_contracts),
                    "verified": len(verified),
                    "missing": len(missing),
                    "missing_contracts": missing,
                },
                "error": f"Missing contracts: {missing}" if missing else None,
            }
        else:
            # Just verify some contracts are deployed
            passed = len(deployed_contracts) > 0
            return {
                "passed": passed,
                "details": {"total_deployed": len(deployed_contracts)},
                "error": "No contracts deployed" if not passed else None,
            }

    def _verify_transaction_history(
        self, address: str, expected_contracts: Optional[List[str]] = None
    ) -> Dict:
        """Verify recent transaction history"""
        try:
            # Bolt ⚡: Use cached monitor method instead of direct requests.get
            transactions = self.monitor.get_recent_transactions(address, limit=50)

            # Bolt ⚡: Move datetime.now outside the loop for consistency and efficiency
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(hours=24)

            # Analyze recent transactions
            recent_txs = [
                tx
                for tx in transactions
                if datetime.fromisoformat(tx["burn_block_time"].replace("Z", "+00:00"))
                > cutoff
            ]

            # Look for contract deployment transactions
            deploy_txs = [
                tx for tx in recent_txs if tx.get("tx_type") == "contract_call"
            ]

            return {
                "passed": True,
                "details": {
                    "total_transactions": len(transactions),
                    "recent_transactions": len(recent_txs),
                    "deployment_transactions": len(deploy_txs),
                },
            }

        except Exception as e:
            return {
                "passed": False,
                "error": f"Could not verify transaction history: {e}",
            }

    def _verify_network_health(
        self, address: str, expected_contracts: Optional[List[str]] = None
    ) -> Dict:
        """Verify network health and performance"""
        api_status = self.monitor.check_api_status()

        # Check if network is healthy
        passed = (
            api_status["status"] == "online" and api_status.get("block_height", 0) > 0
        )

        return {
            "passed": passed,
            "details": api_status,
            "error": "Network health check failed" if not passed else None,
        }

    def _verify_gas_usage(
        self, address: str, expected_contracts: Optional[List[str]] = None
    ) -> Dict:
        """Verify gas usage and account activity"""
        account_info = self.monitor.get_account_info(address)

        if not account_info:
            return {"passed": False, "error": "Could not retrieve account information"}

        balance = int(account_info.get("balance", 0)) / 1000000
        nonce = account_info.get("nonce", 0)

        # Estimate gas usage (very rough)
        estimated_gas_per_tx = 0.1  # 0.1 STX per transaction
        estimated_gas_used = nonce * estimated_gas_per_tx

        return {
            "passed": True,
            "details": {
                "current_balance": balance,
                "transaction_count": nonce,
                "estimated_gas_used": estimated_gas_used,
                "remaining_balance": balance - estimated_gas_used,
            },
        }

    def _verify_contract_functionality(
        self, address: str, expected_contracts: Optional[List[str]] = None
    ) -> Dict:
        """Verify basic contract functionality"""
        deployed_contracts = self.monitor.get_deployed_contracts(address)

        if not deployed_contracts:
            return {"passed": False, "error": "No contracts deployed to test"}

        # Test a few key contracts
        test_contracts = ["all-traits", "cxd-token", "dex-factory", "governance-token"]
        tested = []
        working = []

        # Bolt ⚡: Create a lookup map to avoid O(N*M) search and improve performance
        deployed_names_map = {
            c.get("contract_id", "").split(".")[-1]: c.get("contract_id")
            for c in deployed_contracts
        }

        # Bolt ⚡: Parallelize contract interface verification to reduce latency.
        # This is particularly useful when checking multiple contracts.
        contract_tasks = []
        for contract_name in test_contracts:
            if contract_name in deployed_names_map:
                contract_id = deployed_names_map[contract_name]
                tested.append(contract_name)
                contract_tasks.append((contract_name, contract_id))

        def check_contract(name, cid):
            try:
                if self.monitor.get_contract_details(cid):
                    return name, True, None
                else:
                    return name, False, "Interface not accessible"
            except Exception as e:
                return name, False, str(e)

        if contract_tasks:
            with ThreadPoolExecutor(max_workers=len(contract_tasks)) as executor:
                future_to_contract = {
                    executor.submit(check_contract, name, cid): name
                    for name, cid in contract_tasks
                }

                for future in as_completed(future_to_contract):
                    name, is_working, error = future.result()
                    if is_working:
                        working.append(name)
                    else:
                        if error:
                            if self.verbose:
                                self._safe_print(
                                    f"⚠️  {name}: Error checking interface: {error}"
                                )
                            else:
                                self._safe_print(f"⚠️  {name}: {error}")

        passed = len(working) > 0  # At least some contracts should be working

        return {
            "passed": passed,
            "details": {
                "tested_contracts": len(tested),
                "working_contracts": len(working),
                "tested": tested,
                "working": working,
            },
            "error": "No contracts responding" if not working else None,
        }

    def _generate_recommendations(self):
        """Generate deployment recommendations"""
        recommendations = []

        # Check API status
        api_check = self.verification_results["checks"].get("API Connectivity", {})
        if not api_check.get("passed"):
            recommendations.append("Fix API connectivity issues before proceeding")

        # Check account balance
        account_check = self.verification_results["checks"].get("Account Status", {})
        if not account_check.get("passed"):
            recommendations.append("Fund account with sufficient STX balance")

        # Check contract deployment
        contract_check = self.verification_results["checks"].get(
            "Contract Deployment", {}
        )
        if not contract_check.get("passed"):
            missing = contract_check.get("details", {}).get("missing_contracts", [])
            if missing:
                recommendations.append(
                    f"Deploy missing contracts: {', '.join(missing)}"
                )

        # Network health
        network_check = self.verification_results["checks"].get("Network Health", {})
        if not network_check.get("passed"):
            recommendations.append("Wait for network stability before continuing")

        self.verification_results["recommendations"] = recommendations

    def _save_verification_results(self):
        """Save verification results to file"""
        results_path = Path("logs") / "verification_results.json"
        results_path.parent.mkdir(exist_ok=True)

        # 🛡️ Sentinel: Use secure persistence with standardized automatic redaction and 0600 permissions.
        # Passing the dictionary directly with json_format=True is more robust and consistent.
        save_secure_config(
            str(results_path), self.verification_results, json_format=True
        )

        self._safe_print(f"💾 Verification results saved to {results_path}")

    def print_verification_summary(self):
        """Print comprehensive verification summary"""
        self._safe_print("\n" + "=" * 60)
        self._safe_print("📊 DEPLOYMENT VERIFICATION SUMMARY")
        self._safe_print("=" * 60)

        self._safe_print(f"🕐 Timestamp: {self.verification_results['timestamp']}")
        self._safe_print(f"🌐 Network: {self.verification_results['network']}")
        self._safe_print(
            f"📊 Overall Status: {self.verification_results['overall_status'].upper()}"
        )

        self._safe_print("\n🔍 Individual Checks:")
        for check_name, result in self.verification_results["checks"].items():
            status = "✅ PASS" if result.get("passed") else "❌ FAIL"
            error = result.get("error", "")
            self._safe_print(f"   {status} {check_name}")
            if error and not result.get("passed"):
                self._safe_print(f"       Error: {error}")

        self._safe_print("📦 Contract Status:")
        contract_check = self.verification_results["checks"].get(
            "Contract Deployment", {}
        )
        details = contract_check.get("details", {})

        if details:
            self._safe_print(f"   Total deployed: {details.get('total_deployed', 0)}")
            self._safe_print(f"   Expected: {details.get('expected', 0)}")
            self._safe_print(f"   Verified: {details.get('verified', 0)}")
            self._safe_print(f"   Missing: {details.get('missing', 0)}")

        if self.verification_results["recommendations"]:
            self._safe_print("💡 Recommendations:")
            for rec in self.verification_results["recommendations"]:
                self._safe_print(f"   • {rec}")

        self._safe_print("\n" + "=" * 60)


def load_expected_contracts() -> List[str]:
    """Load expected contracts from Clarinet.toml"""
    contracts = []
    clarinet_path = Path("Clarinet.toml")

    if clarinet_path.exists():
        try:
            with open(clarinet_path, "r") as f:
                content = f.read()

            # Extract contract names
            import re

            contract_matches = re.findall(r"\[contracts\.([^\]]+)\]", content)
            contracts = [match for match in contract_matches]

        except Exception as e:
            # 🛡️ Sentinel: Prevent sensitive information disclosure.
            # In library functions, we might not have a verbose flag easily,
            # but we can try to be quiet and provide a generic warning.
            print("Warning: Could not parse Clarinet.toml (use --verbose for details)")

    return contracts


def main():
    """Main verification CLI function"""
    parser = argparse.ArgumentParser(description="Conxian Deployment Verification")
    parser.add_argument("--config", default=".env", help="Configuration file path")
    parser.add_argument(
        "--network", choices=["devnet", "testnet", "mainnet"], default="testnet"
    )
    parser.add_argument("--address", help="Address to verify")
    parser.add_argument("--contracts", nargs="*", help="Specific contracts to verify")
    parser.add_argument(
        "--comprehensive", action="store_true", help="Run comprehensive verification"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        # 🛡️ Sentinel: Secure configuration loading.
        config = {}
        if Path(args.config).exists():
            from dotenv import dotenv_values

            file_config = dotenv_values(dotenv_path=args.config)

            # Enforce security policy - no secrets in .env
            for key, value in file_config.items():
                if is_sensitive_key(key) and not is_placeholder(value):
                    error_message = (
                        f"🛡️ Sentinel Security Error: Secret key '{key}' found in .env file.\n"
                        "   Storing secrets in plaintext files is a critical security risk and is not permitted.\n"
                        "   For your protection, please move this secret to an environment variable and remove it from the .env file.\n"
                        f"   Example: export {key}='your_secret_value_here'"
                    )
                    raise ValueError(error_message)
                config[key] = value

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

        # Override with command line arguments
        if args.network:
            config["NETWORK"] = args.network
        if args.address:
            config["SYSTEM_ADDRESS"] = args.address

        # Load expected contracts
        expected_contracts = args.contracts or load_expected_contracts()

        if not expected_contracts:
            print("⚠️  No contracts specified for verification")
            print(
                "💡 Use --contracts to specify contracts or ensure Clarinet.toml exists"
            )
            return 1

        # Initialize verifier
        verifier = DeploymentVerifier(
            network=config.get("NETWORK", "testnet"), config=config
        )

        # Run verification
        results = verifier.run_comprehensive_verification(expected_contracts)

        # Print summary
        verifier.print_verification_summary()

        # Exit with appropriate code
        return 0 if results["overall_status"] == "success" else 1

    except KeyboardInterrupt:
        print("\n🛑 Verification cancelled by user")
        return 1
    except Exception as e:
        # 🛡️ Sentinel: Prevent sensitive information disclosure.
        if args.verbose:
            print(f"❌ Verification failed: {e}")
            import traceback

            traceback.print_exc()
        else:
            print("❌ Verification failed (use --verbose for details)")
        return 1


if __name__ == "__main__":
    exit(main())
