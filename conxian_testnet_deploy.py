#!/usr/bin/env python3
"""
Conxian Testnet Deployment Script - Enhanced Version
Complete deployment system with CLI integration, monitoring, and verification
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Force UTF-8 encoding for stdout on Windows to handle emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Import our enhanced modules
from enhanced_conxian_deployment import EnhancedConfigManager, EnhancedConxianDeployer
from deployment_monitor import DeploymentMonitor
from deployment_verifier import DeploymentVerifier, load_expected_contracts


class ConxianTestnetDeployer:
    """Complete Conxian testnet deployment system"""

    def __init__(self, config_path: str = ".env", verbose: bool = False):
        self.config_path = config_path
        self.verbose = verbose

        # Initialize components
        self.config_manager = EnhancedConfigManager(config_path)
        self.config = self.config_manager.load_config()

        # Validate configuration
        is_valid, errors = self.config_manager.validate_config()
        if not is_valid:
            raise ValueError(f"Configuration validation failed: {errors}")

        print("✅ Configuration loaded and validated")

    def deploy_to_testnet(self, options: Dict) -> Dict:
        """Deploy Conxian protocol to testnet"""
        print("🚀 Conxian Protocol - Testnet Deployment")
        print("=" * 60)

        # Update config with deployment options
        self.config.update(options)

        # Initialize deployer
        deployer = EnhancedConxianDeployer(self.config, self.verbose)

        # Run pre-deployment checks
        if not options.get("skip_checks", False):
            print("\n🔍 Running pre-deployment checks...")
            if not deployer.run_pre_checks():
                if not options.get("force", False):
                    raise ValueError(
                        "Pre-deployment checks failed. Use --force to continue."
                    )

        # Execute deployment
        print(
            f"\n🚀 Starting deployment in {self.config.get('DEPLOYMENT_MODE', 'full')} mode..."
        )

        results = deployer.deploy_conxian(
            category=options.get("category"), dry_run=options.get("dry_run", False)
        )

        # Post-deployment verification
        if not options.get("dry_run", False) and results.get("successful"):
            print("\n🔍 Running post-deployment verification...")
            self._run_post_deployment_checks(results)

        return results

    def _run_post_deployment_checks(self, results: Dict):
        """Run post-deployment verification"""
        address = self.config.get("SYSTEM_ADDRESS")
        if not address:
            print("⚠️  Skipping verification - no address configured")
            return

        # Get expected contracts
        expected_contracts = load_expected_contracts()

        # Initialize verifier
        verifier = DeploymentVerifier(
            network=self.config.get("NETWORK", "testnet"), config=self.config
        )

        # Run verification
        verification_results = verifier.run_comprehensive_verification(
            expected_contracts
        )

        # Print summary
        verifier.print_verification_summary()

        # Save deployment manifest
        self._save_deployment_manifest(results, verification_results)

    def _save_deployment_manifest(
        self, deployment_results: Dict, verification_results: Dict
    ):
        """Save comprehensive deployment manifest"""
        manifest = {
            "deployment": {
                "timestamp": datetime.now().isoformat(),
                "network": self.config.get("NETWORK", "testnet"),
                "deployer": self.config.get("SYSTEM_ADDRESS", ""),
                "results": deployment_results,
                "verification": verification_results,
            },
            "config": {
                "deployment_mode": self.config.get("DEPLOYMENT_MODE", "full"),
                "total_contracts": len(deployment_results.get("successful", []))
                + len(deployment_results.get("failed", []))
                + len(deployment_results.get("skipped", [])),
                "successful": len(deployment_results.get("successful", [])),
                "failed": len(deployment_results.get("failed", [])),
                "gas_estimate": self._calculate_gas_estimate(deployment_results),
            },
            "metadata": {
                "tool": "StacksOrbit Enhanced",
                "version": "1.2.0",
                "protocol": "Conxian",
            },
        }

        # Save manifest
        manifest_path = Path("deployment") / "testnet_complete_manifest.json"
        manifest_path.parent.mkdir(exist_ok=True)

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"💾 Complete deployment manifest saved to {manifest_path}")

    def _calculate_gas_estimate(self, results: Dict) -> float:
        """Calculate estimated gas usage"""
        successful_count = len(results.get("successful", []))
        return successful_count * 1.0  # 1 STX per contract estimate

    def monitor_deployment(self, options: Dict) -> None:
        """Monitor deployment progress"""
        print("📊 Starting deployment monitoring...")

        # Initialize monitor
        monitor = DeploymentMonitor(
            network=self.config.get("NETWORK", "testnet"), config=self.config
        )

        # Show initial status
        print("\n🌐 Network Status:")
        api_status = monitor.check_api_status()
        print(f"   Status: {api_status['status']}")
        print(f"   Network: {api_status.get('network_id', 'unknown')}")
        print(f"   Block Height: {api_status.get('block_height', 0)}")

        address = self.config.get("SYSTEM_ADDRESS")
        if address:
            print("\n👤 Account Status:")

            account_info = monitor.get_account_info(address)
            if account_info:
                balance = int(account_info.get("balance", 0)) / 1000000
                print(f"   Balance: {balance} STX")
                print(f"   Nonce: {account_info.get('nonce', 0)}")

            print("\n📦 Deployed Contracts:")
            contracts = monitor.get_deployed_contracts(address)
            print(f"   Count: {len(contracts)}")

            for contract in contracts:
                print(f"   - {contract.get('contract_id', 'unknown')}")

        # Start real-time monitoring
        if options.get("follow", False):
            print("\n🔄 Starting real-time monitoring...")
            print("📝 Press Ctrl+C to stop monitoring\n")

            monitor_thread = monitor.start_monitoring()

            try:
                while monitor.is_monitoring:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping monitoring...")

            monitor.stop_monitoring()
            print("✅ Monitoring stopped")

    def verify_deployment(self, options: Dict) -> None:
        """Verify deployment completeness"""
        print("🔍 Running deployment verification...")

        address = self.config.get("SYSTEM_ADDRESS")
        if not address:
            raise ValueError("SYSTEM_ADDRESS not configured")

        # Get expected contracts
        expected_contracts = options.get("contracts") or load_expected_contracts()

        if not expected_contracts:
            print("⚠️  No contracts specified for verification")
            print(
                "💡 Use --contracts to specify contracts or ensure Clarinet.toml exists"
            )
            return

        # Initialize verifier
        verifier = DeploymentVerifier(
            network=self.config.get("NETWORK", "testnet"), config=self.config
        )

        # Run comprehensive verification
        results = verifier.run_comprehensive_verification(expected_contracts)

        # Print detailed summary
        verifier.print_verification_summary()

        # Exit with appropriate code
        if results["overall_status"] != "success":
            print("\n❌ Deployment verification failed")
            sys.exit(1)
        else:
            print("\n✅ Deployment verification successful")

    def initialize_setup(self, options: Dict) -> None:
        """Initialize deployment setup"""
        print("⚙️  Initializing Conxian deployment setup...")

        # Create configuration
        self.config_manager._create_default_config()

        # Generate wallet if requested
        if options.get("generate_wallet", False):
            print("\n🔑 Generating testnet wallet...")

            # This would typically use the Stacks wallet SDK
            # For now, we'll provide instructions
            print("💡 Wallet generation requires Node.js Stacks SDK")
            print("💡 Run: npx stacks-wallet-generate --network testnet")
            print("💡 Or use the GUI: stacksorbit gui")

        # Update configuration
        network = options.get("network", "testnet")
        self.config["NETWORK"] = network

        if options.get("api_key"):
            self.config["HIRO_API_KEY"] = options["api_key"]

        self.config_manager.save_config(self.config)

        print("\n✅ Setup initialized!")
        print(f"📝 Configuration saved to {self.config_path}")
        print("\n📋 Next steps:")
        print("1. Edit .env file with your private key and address")
        print("2. Fund your address with STX tokens")
        print("3. Run: python conxian_testnet_deploy.py check")
        print("4. Run: python conxian_testnet_deploy.py deploy --dry-run")
        print("5. Run: python conxian_testnet_deploy.py deploy")

    def run_diagnostics(self, options: Dict) -> None:
        """Run comprehensive diagnostics"""
        print("🔍 Running comprehensive diagnostics...")

        # Load configuration
        config = self.config_manager.load_config()

        # Initialize deployer
        deployer = EnhancedConxianDeployer(config, self.verbose)

        # Run all checks
        print("\n📊 System Diagnostics:")
        print("-" * 40)

        # Environment
        print("\n🔧 Environment:")
        for key, value in config.items():
            if key in ["DEPLOYER_PRIVKEY", "HIRO_API_KEY"]:
                print(f"   {key}: {value[:10]}...")
            else:
                print(f"   {key}: {value}")

        # Pre-checks
        print("\n🔍 Pre-deployment Checks:")
        checks_passed = deployer.run_pre_checks()

        # Expected contracts
        print("\n📦 Expected Contracts:")
        expected_contracts = load_expected_contracts()
        print(f"   Total: {len(expected_contracts)} contracts")

        # Network status
        print("\n🌐 Network Status:")
        monitor = DeploymentMonitor(config.get("NETWORK", "testnet"), config)
        api_status = monitor.check_api_status()
        print(f"   API Status: {api_status['status']}")
        print(f"   Network: {api_status.get('network_id', 'unknown')}")
        print(f"   Block Height: {api_status.get('block_height', 0)}")

        # Account status
        address = config.get("SYSTEM_ADDRESS")
        if address:
            print("\n👤 Account Status:")
            account_info = monitor.get_account_info(address)
            if account_info:
                balance = int(account_info.get("balance", 0)) / 1000000
                print(f"   Balance: {balance} STX")
                print(f"   Nonce: {account_info.get('nonce', 0)}")

            print("\n📦 Deployed Contracts:")
            contracts = monitor.get_deployed_contracts(address)
            print(f"   Count: {len(contracts)}")

        print("\n📊 Diagnostics Complete")
        print(f"✅ Overall Status: {'READY' if checks_passed else 'NEEDS ATTENTION'}")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Conxian Testnet Deployment - Enhanced Version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize setup
  python conxian_testnet_deploy.py init --network testnet

  # Run diagnostics
  python conxian_testnet_deploy.py check --verbose

  # Dry run deployment
  python conxian_testnet_deploy.py deploy --dry-run

  # Deploy specific category
  python conxian_testnet_deploy.py deploy --category core

  # Full deployment
  python conxian_testnet_deploy.py deploy --batch-size 5

  # Monitor deployment
  python conxian_testnet_deploy.py monitor --follow

  # Verify deployment
  python conxian_testnet_deploy.py verify --contracts all-traits cxd-token dex-factory
        """,
    )

    parser.add_argument("--config", default=".env", help="Configuration file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--network", choices=["devnet", "testnet", "mainnet"], default="testnet"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy to testnet")
    deploy_parser.add_argument(
        "--category",
        choices=[
            "core",
            "tokens",
            "dex",
            "dimensional",
            "oracle",
            "security",
            "monitoring",
        ],
    )
    deploy_parser.add_argument(
        "--batch-size", type=int, default=5, help="Contracts per batch"
    )
    deploy_parser.add_argument("--dry-run", action="store_true", help="Perform dry run")
    deploy_parser.add_argument(
        "--skip-checks", action="store_true", help="Skip pre-deployment checks"
    )
    deploy_parser.add_argument(
        "--force", action="store_true", help="Force deployment despite check failures"
    )

    # Check command
    check_parser = subparsers.add_parser("check", help="Run diagnostics")
    check_parser.add_argument(
        "--env-only", action="store_true", help="Check only environment"
    )
    check_parser.add_argument(
        "--network-only", action="store_true", help="Check only network"
    )
    check_parser.add_argument(
        "--compile-only", action="store_true", help="Check only compilation"
    )

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor deployment")
    monitor_parser.add_argument(
        "--follow", action="store_true", help="Follow in real-time"
    )
    monitor_parser.add_argument(
        "--api-only", action="store_true", help="Check only API status"
    )

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify deployment")
    verify_parser.add_argument(
        "--contracts", nargs="*", help="Specific contracts to verify"
    )
    verify_parser.add_argument(
        "--comprehensive", action="store_true", help="Run comprehensive verification"
    )

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize setup")
    init_parser.add_argument(
        "--generate-wallet", action="store_true", help="Generate wallet"
    )
    init_parser.add_argument("--api-key", help="Hiro API key")

    args = parser.parse_args()

    try:
        # Initialize deployer
        deployer = ConxianTestnetDeployer(args.config, args.verbose)

        # Override network if specified
        if args.network:
            deployer.config["NETWORK"] = args.network

        # Execute command
        if args.command == "deploy":
            options = {
                "category": getattr(args, "category", None),
                "batch_size": getattr(args, "batch_size", 5),
                "dry_run": getattr(args, "dry_run", False),
                "skip_checks": getattr(args, "skip_checks", False),
                "force": getattr(args, "force", False),
            }

            results = deployer.deploy_to_testnet(options)

            if args.dry_run:
                print("\n🔍 Dry run completed successfully")
            elif results.get("successful"):
                print("\n🎉 Deployment completed successfully!")
                print("💡 Use 'monitor' command to track confirmation")
            else:
                print("\n❌ Deployment had issues")
                sys.exit(1)

        elif args.command == "check":
            options = {
                "env_only": getattr(args, "env_only", False),
                "network_only": getattr(args, "network_only", False),
                "compile_only": getattr(args, "compile_only", False),
            }
            deployer.run_diagnostics(options)

        elif args.command == "monitor":
            options = {
                "follow": getattr(args, "follow", False),
                "api_only": getattr(args, "api_only", False),
            }
            deployer.monitor_deployment(options)

        elif args.command == "verify":
            options = {
                "contracts": getattr(args, "contracts", None),
                "comprehensive": getattr(args, "comprehensive", False),
            }
            deployer.verify_deployment(options)

        elif args.command == "init":
            options = {
                "generate_wallet": getattr(args, "generate_wallet", False),
                "api_key": getattr(args, "api_key", None),
            }
            deployer.initialize_setup(options)

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
