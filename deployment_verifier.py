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
from datetime import datetime
import argparse

# Import monitoring components
from deployment_monitor import DeploymentMonitor


class DeploymentVerifier:
    """Comprehensive deployment verification system"""

    def __init__(self, network: str = "testnet", config: Dict = None):
        self.network = network
        self.config = config or {}
        self.monitor = DeploymentMonitor(network, config)

        # Verification results
        self.verification_results = {
            "timestamp": datetime.now().isoformat(),
            "network": network,
            "overall_status": "unknown",
            "checks": {},
            "contracts": {},
            "recommendations": [],
        }

    def run_comprehensive_verification(
        self, expected_contracts: Optional[List[str]] = None
    ) -> Dict:
        """Run comprehensive deployment verification"""
        print("🔍 Starting comprehensive deployment verification...\n")

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

        for check_name, check_func in checks:
            print(f"🔍 {check_name}...")

            try:
                result = check_func(address, expected_contracts)
                self.verification_results["checks"][check_name] = result

                if not result["passed"]:
                    all_passed = False
                    print(
                        f"❌ {check_name} failed: {result.get('error', 'Unknown error')}"
                    )
                else:
                    print(f"✅ {check_name} passed")

            except Exception as e:
                print(f"❌ {check_name} error: {e}")
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

            verified = []
            missing = []

            for contract in expected_contracts:
                if contract in deployed_names:
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
            # Get account transactions
            response = requests.get(
                f"{self.monitor.api_url}/v2/accounts/{address}/transactions?limit=50",
                timeout=10,
            )
            response.raise_for_status()
            transactions = response.json().get("results", [])

            # Analyze recent transactions
            recent_txs = [
                tx
                for tx in transactions
                if datetime.fromisoformat(tx["burn_block_time"].replace("Z", "+00:00"))
                > datetime.now() - timedelta(hours=24)
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

        for contract in deployed_contracts:
            contract_id = contract.get("contract_id", "")
            contract_name = contract_id.split(".")[-1]

            if contract_name in test_contracts:
                tested.append(contract_name)

                # Try to read contract interface
                try:
                    response = requests.get(
                        f"{self.monitor.api_url}/v2/contracts/interface/{contract_id}",
                        timeout=10,
                    )

                    if response.status_code == 200:
                        working.append(contract_name)
                    else:
                        print(f"⚠️  {contract_name}: Interface not accessible")

                except Exception as e:
                    print(f"⚠️  {contract_name}: Error checking interface: {e}")

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

        with open(results_path, "w") as f:
            json.dump(self.verification_results, f, indent=2)

        print(f"💾 Verification results saved to {results_path}")

    def print_verification_summary(self):
        """Print comprehensive verification summary"""
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT VERIFICATION SUMMARY")
        print("=" * 60)

        print(f"🕐 Timestamp: {self.verification_results['timestamp']}")
        print(f"🌐 Network: {self.verification_results['network']}")
        print(
            f"📊 Overall Status: {self.verification_results['overall_status'].upper()}"
        )

        print("\n🔍 Individual Checks:")
        for check_name, result in self.verification_results["checks"].items():
            status = "✅ PASS" if result.get("passed") else "❌ FAIL"
            error = result.get("error", "")
            print(f"   {status} {check_name}")
            if error and not result.get("passed"):
                print(f"       Error: {error}")

        print("📦 Contract Status:")
        contract_check = self.verification_results["checks"].get(
            "Contract Deployment", {}
        )
        details = contract_check.get("details", {})

        if details:
            print(f"   Total deployed: {details.get('total_deployed', 0)}")
            print(f"   Expected: {details.get('expected', 0)}")
            print(f"   Verified: {details.get('verified', 0)}")
            print(f"   Missing: {details.get('missing', 0)}")

        if self.verification_results["recommendations"]:
            print("💡 Recommendations:")
            for rec in self.verification_results["recommendations"]:
                print(f"   • {rec}")

        print("\n" + "=" * 60)


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
            print(f"Warning: Could not parse Clarinet.toml: {e}")

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
        # Load configuration
        config = {}
        if Path(args.config).exists():
            with open(args.config, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip().strip('"')

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
        print(f"❌ Verification failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
