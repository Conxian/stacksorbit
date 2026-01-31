#!/usr/bin/env python3
"""
Enhanced StacksOrbit Auto-Detection System CLI
Generic integration that works with any Stacks contracts
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Import the generic auto-detector
from enhanced_auto_detector import GenericStacksAutoDetector


class StacksOrbitCLIIntegration:
    """Generic CLI integration for StacksOrbit auto-detection"""

    def __init__(self):
        # Use generic mode by default, Conxian mode only if explicitly requested
        use_conxian = os.getenv("STACKSORBIT_CONXIAN_MODE", "false").lower() == "true"
        self.auto_detector = GenericStacksAutoDetector(use_conxian_mode=use_conxian)
        self.current_analysis = None

    def run_detection(self, directory: Optional[str] = None) -> Dict:
        """Run detection (CLI command)"""
        if directory:
            os.chdir(directory)

        self.current_analysis = self.auto_detector.detect_and_analyze()
        return self.current_analysis

    def show_detection_results(self):
        """Show detection results in CLI format"""
        if not self.current_analysis:
            print("❌ No analysis available. Run detection first.")
            return

        analysis = self.current_analysis
        detection = analysis["detection"]
        deployment_plan = analysis["deployment_plan"]

        print("🔍 StacksOrbit Auto-Detection Results")
        print("=" * 50)
        print(f"📂 Directory: {detection['directory']}")
        print(f"📦 Contracts found: {detection['contracts_found']}")
        print(f"📊 Deployment mode: {deployment_plan['deployment_mode']}")
        print(f"🚀 To deploy: {deployment_plan['contracts_to_deploy']}")
        print(f"⏭️  To skip: {deployment_plan['contracts_to_skip']}")
        print(f"⛽ Est. gas: {deployment_plan['estimated_gas']:.1f} STX")
        print(f"⏰ Est. time: {deployment_plan['estimated_time']} minutes")

        # Show recommendations
        recommendations = self.auto_detector.get_deployment_recommendations(analysis)
        if recommendations:
            print("\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   {rec}")

        # Show contracts
        contracts = detection.get("contracts", [])
        if contracts and isinstance(contracts, list):
            print("\n📋 Available contracts:")
            for i, contract in enumerate(contracts[:15], 1):
                status = (
                    "✅"
                    if isinstance(deployment_plan.get("contracts_to_deploy", []), list)
                    and contract["name"] in deployment_plan["contracts_to_deploy"]
                    else "⏭️ "
                )
                print(f"   {status} {contract['name']} ({contract['source']})")

            print(f"   ... and {len(contracts) - 15} more")

        print(f"\n✅ Ready for deployment: {analysis['ready']}")

    def generate_deployment_command(self) -> str:
        """Generate appropriate deployment command"""
        if not self.current_analysis:
            return "python ultimate_stacksorbit.py deploy --dry-run"

        analysis = self.current_analysis
        deployment_plan = analysis["deployment_plan"]

        # Base command
        command = "python ultimate_stacksorbit.py deploy"

        # Add options based on analysis
        if deployment_plan["deployment_mode"] == "upgrade":
            command += " --upgrade"
        elif deployment_plan["deployment_mode"] == "full":
            command += " --full"

        # Add batch size recommendation
        if deployment_plan["contracts_to_deploy"] > 10:
            command += " --batch-size 5"
        elif deployment_plan["contracts_to_deploy"] > 20:
            command += " --batch-size 3"

        # Add parallel deployment for large sets
        if deployment_plan["contracts_to_deploy"] > 15:
            command += " --parallel"

        # Always recommend dry run first
        dry_run_command = command + " --dry-run"

        return dry_run_command

    def test_auto_detection(self) -> bool:
        """Test auto-detection in various scenarios"""
        print("🧪 Testing Enhanced Auto-Detection System\n")

        test_scenarios = [
            ("Current directory", Path.cwd()),
            ("Test directory", Path("test_auto_detection")),
            ("Parent directory", Path("..")),
        ]

        all_passed = True

        for scenario_name, test_path in test_scenarios:
            if not test_path.exists():
                continue

            print(f"📍 Testing: {scenario_name} ({test_path})")

            try:
                # Change to test directory
                original_dir = Path.cwd()
                os.chdir(test_path)

                # Run detection
                analysis = self.auto_detector.detect_and_analyze()

                # Check results
                contracts_found = analysis["detection"]["contracts_found"]
                deployment_mode = analysis["deployment_plan"]["deployment_mode"]

                print(f"   ✅ Contracts: {contracts_found}")
                print(f"   📊 Mode: {deployment_mode}")
                print(
                    f"   🚀 To deploy: {analysis['deployment_plan']['contracts_to_deploy']}"
                )

                if contracts_found > 0:
                    print("   ✅ Detection successful")
                else:
                    print("   ⚠️  No contracts found")
                    all_passed = False

                # Change back
                os.chdir(original_dir)

            except Exception as e:
                print(f"   ❌ Test failed: {e}")
                all_passed = False

            print()

        return all_passed


def main():
    """Main CLI function for enhanced auto-detection"""
    parser = argparse.ArgumentParser(
        description="Enhanced StacksOrbit Auto-Detection System"
    )
    parser.add_argument(
        "command",
        choices=["detect", "test", "analyze", "deploy-plan"],
        help="Command to run",
    )
    parser.add_argument("--directory", "-d", help="Directory to analyze")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    # Initialize integration
    integration = StacksOrbitCLIIntegration()

    try:
        if args.command == "detect":
            # Run detection
            if args.directory:
                os.chdir(args.directory)

            analysis = integration.run_detection()
            integration.show_detection_results()

            if args.json:
                print(json.dumps(analysis, indent=2))

            return 0 if analysis["ready"] else 1

        elif args.command == "test":
            # Run comprehensive tests
            success = integration.test_auto_detection()
            return 0 if success else 1

        elif args.command == "analyze":
            # Analyze current directory
            analysis = integration.run_detection(args.directory)
            integration.show_detection_results()

            if args.json:
                print(json.dumps(analysis, indent=2))

            return 0

        elif args.command == "deploy-plan":
            # Generate deployment plan
            analysis = integration.run_detection(args.directory)

            if analysis["ready"]:
                command = integration.generate_deployment_command()
                print(f"🚀 Recommended deployment command:\n   {command}")
                print("📋 Deployment plan:")
                print(f"   Mode: {analysis['deployment_plan']['deployment_mode']}")
                print(
                    f"   Contracts: {analysis['deployment_plan']['contracts_to_deploy']}"
                )
                print(f"   Gas: {analysis['deployment_plan']['estimated_gas']:.1f} STX")
                print(
                    f"   Time: {analysis['deployment_plan']['estimated_time']} minutes"
                )
                return 0
            else:
                print("❌ Not ready for deployment. Run 'stacksorbit detect' first.")
                return 1

        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        print("\n🛑 Auto-detection cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Auto-detection failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
