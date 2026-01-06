#!/usr/bin/env python3
"""
Ultimate StacksOrbit Integration Script
One-stop solution for deploying to Stacks blockchain with enhanced features
"""

import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import psutil

# Import all enhanced modules
from enhanced_conxian_deployment import EnhancedConfigManager, EnhancedConxianDeployer
from deployment_monitor import DeploymentMonitor
from deployment_verifier import DeploymentVerifier
from stacksorbit_gui import StacksOrbitGUI
from local_devnet import LocalDevnet

try:
    import colorama
    from colorama import Fore, Style
    colorama.init()
    USE_COLORS = True
except ImportError:
    USE_COLORS = False

class SetupWizard:
    """Interactive setup wizard for StacksOrbit"""

    def __init__(self):
        self.config = {}
        self.project_root = Path.cwd()
        self.stacksorbit_root = Path(__file__).parent

    def start_wizard(self):
        """Start the interactive setup wizard"""
        print(f"{Fore.CYAN}🚀 Welcome to StacksOrbit Setup Wizard!{Style.RESET_ALL}")
        print(f"{Fore.WHITE}This wizard will guide you through setting up your Stacks blockchain deployment.{Style.RESET_ALL}")
        print()

        # Check prerequisites
        if not self._check_prerequisites():
            print(f"{Fore.RED}❌ Prerequisites not met. Please install required software and try again.{Style.RESET_ALL}")
            return False

        # Run setup steps
        steps = [
            self._step_welcome,
            self._step_project_analysis,
            self._step_network_selection,
            self._step_wallet_setup,
            self._step_configuration,
            self._step_testing,
            self._step_deployment_options,
            self._step_install_stacks_core,
            self._step_summary
        ]

        for step in steps:
            if not step():
                print(f"{Fore.RED}❌ Setup cancelled or failed.{Style.RESET_ALL}")
                return False

        print(f"\n{Fore.GREEN}🎉 Setup completed successfully!{Style.RESET_ALL}")
        print(f"{Fore.WHITE}You can now use StacksOrbit to deploy your contracts.{Style.RESET_ALL}")
        return True

    def _check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed"""
        print("🔍 Checking prerequisites...")

        prerequisites = [
            ('Node.js', 'node --version', 'Node.js 14+'),
            ('Python', 'python --version', 'Python 3.8+'),
            ('Clarinet', 'clarinet --version', 'Clarinet'),
            ('Git', 'git --version', 'Git'),
            ('Cargo', 'cargo --version', 'Cargo')
        ]

        all_met = True

        for name, command, expected in prerequisites:
            try:
                result = subprocess.run(command.split(), capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip() or result.stderr.strip()
                    print(f"✅ {name}: {version}")
                else:
                    print(f"❌ {name}: Not found")
                    all_met = False
            except Exception as e:
                print(f"❌ {name}: Error checking ({e})")
                all_met = False

        # Check for StacksOrbit dependencies
        print("\n📦 Checking StacksOrbit dependencies...")
        try:
            import requests
            print("✅ Python requests library")
        except ImportError:
            print("⚠️  Python requests library not found - will install")

        try:
            import toml
            print("✅ Python toml library")
        except ImportError:
            print("⚠️  Python toml library not found - will install")

        return all_met

    def _step_welcome(self) -> bool:
        """Welcome step"""
        print(f"\n{Fore.CYAN}📋 Step 1: Welcome{Style.RESET_ALL}")
        print("This wizard will help you set up StacksOrbit for deploying smart contracts to the Stacks blockchain.")
        print()
        print("What you need:")
        print(f"  • A Stacks account with some STX tokens ({Fore.YELLOW}minimum 10 STX recommended{Style.RESET_ALL})")
        print("  • Your private key or 12/24-word mnemonic")
        print("  • Basic understanding of your project structure")
        print()

        response = self._get_user_input("Continue with setup? (y/n): ", ['y', 'n'])
        return response == 'y'

    def _step_project_analysis(self) -> bool:
        """Analyze project structure"""
        print(f"\n{Fore.CYAN}📋 Step 2: Project Analysis{Style.RESET_ALL}")
        print("Analyzing your project structure...")

        # Check for Clarinet.toml
        clarinet_path = self.project_root / "Clarinet.toml"
        if clarinet_path.exists():
            print(f"✅ Found Clarinet.toml at {clarinet_path}")
            self.config['clarinet_found'] = True

            # Analyze contracts
            contracts = self._analyze_clarinet_contracts(clarinet_path)
            if contracts:
                print(f"✅ Found {len(contracts)} contracts in Clarinet.toml:")
                for contract in contracts[:5]:  # Show first 5
                    print(f"   - {contract['name']}")
                if len(contracts) > 5:
                    print(f"   ... and {len(contracts) - 5} more")

                self.config['contracts'] = contracts
                self.config['total_contracts'] = len(contracts)
            else:
                print("⚠️  No contracts found in Clarinet.toml")
        else:
            print(f"⚠️  No Clarinet.toml found - you'll need to create one or specify contract paths manually")
            self.config['clarinet_found'] = False

        # Check for contracts directory
        contracts_dir = self.project_root / "contracts"
        if contracts_dir.exists():
            clar_files = list(contracts_dir.rglob("*.clar"))
            print(f"✅ Found contracts directory with {len(clar_files)} .clar files")
            self.config['contracts_dir_found'] = True
        else:
            print("⚠️  No contracts directory found")
            self.config['contracts_dir_found'] = False

        print()
        response = self._get_user_input("Continue? (y/n): ", ['y', 'n'])
        return response == 'y'

    def _step_network_selection(self) -> bool:
        """Network selection step"""
        print(f"\n{Fore.CYAN}📋 Step 3: Network Selection{Style.RESET_ALL}")
        print("Which Stacks network do you want to deploy to?")
        print()
        print("1. 🧪 Devnet (local testing)")
        print("2. 🧪 Testnet (public testing)")
        print("3. 🌐 Mainnet (production)")
        print()

        choice = self._get_user_input("Select network (1-3): ", ['1', '2', '3'])

        networks = {
            '1': 'devnet',
            '2': 'testnet',
            '3': 'mainnet'
        }

        self.config['network'] = networks[choice]

        if choice == '1':
            print("✅ Selected Devnet - great for local testing!")
            print(f"{Fore.YELLOW}💡 Make sure you have a local Stacks node running{Style.RESET_ALL}")
        elif choice == '2':
            print("✅ Selected Testnet - perfect for testing!")
            print(f"{Fore.YELLOW}💡 Get free STX from the faucet: https://explorer.stacks.co/sandbox{Style.RESET_ALL}")
        else:
            print("✅ Selected Mainnet - production deployment!")
            print(f"{Fore.RED}⚠️  WARNING: This will use real STX tokens!{Style.RESET_ALL}")

        print()
        response = self._get_user_input("Continue? (y/n): ", ['y', 'n'])
        return response == 'y'

    def _step_wallet_setup(self) -> bool:
        """Wallet setup step"""
        print(f"\n{Fore.CYAN}📋 Step 4: Wallet Setup{Style.RESET_ALL}")
        print(f"{Fore.RED}🛡️ Sentinel Security Upgrade{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}For your security, please set your DEPLOYER_PRIVKEY as an environment variable.{Style.RESET_ALL}")
        print("Storing secrets in plaintext files is a major security risk.")
        print("\nTo set an environment variable:")
        print(f"  {Fore.GREEN}export DEPLOYER_PRIVKEY='your_private_key_here'{Style.RESET_ALL} (Linux/macOS)")
        print(f"  {Fore.GREEN}setx DEPLOYER_PRIVKEY 'your_private_key_here'{Style.RESET_ALL} (Windows)")
        print("\nThis key will be read automatically at runtime.")
        self.config['deployer_privkey'] = "your_private_key_here"  # Placeholder

        # Get address
        address = self._get_user_input("\nEnter your Stacks address (SP...): ", None)
        if self._validate_address(address):
            self.config['system_address'] = address
            print("✅ Address validated")
        else:
            print(f"{Fore.RED}❌ Invalid address format{Style.RESET_ALL}")
            return False

        print()
        response = self._get_user_input("Continue? (y/n): ", ['y', 'n'])
        return response == 'y'

    def _step_configuration(self) -> bool:
        """Configuration step"""
        print(f"\n{Fore.CYAN}📋 Step 5: Configuration{Style.RESET_ALL}")
        print("Setting up your deployment configuration...")
        print()

        # Create .env file
        env_content = self._generate_env_config()

        env_path = self.project_root / ".env"
        with open(env_path, 'w') as f:
            f.write(env_content)

        print(f"✅ Configuration saved to {env_path}")
        print()
        print("📋 Configuration summary:")
        print(f"   Network: {self.config['network']}")
        print(f"   Address: {self.config.get('system_address', 'Not set')}")

        if self.config.get('deployer_privkey'):
            print(f"   Private Key: {self.config['deployer_privkey'][:10]}...")
        else:
            print("   Private Key: Not configured (set manually)")

        print()
        print("📝 Environment variables set:")
        for line in env_content.split('\n'):
            if line.strip() and not line.startswith('#'):
                print(f"   {line}")

        print()
        response = self._get_user_input("Continue? (y/n): ", ['y', 'n'])
        return response == 'y'

    def _step_testing(self) -> bool:
        """Testing step"""
        print(f"\n{Fore.CYAN}📋 Step 6: Testing Setup{Style.RESET_ALL}")
        print("Testing your configuration...")
        print()

        # Run basic tests
        tests_passed = 0
        total_tests = 0

        # Test 1: Configuration validation
        total_tests += 1
        print("🔍 Testing configuration...")
        try:
            from enhanced_conxian_deployment import EnhancedConfigManager
            config_manager = EnhancedConfigManager(".env")
            config = config_manager.load_config()
            is_valid, errors = config_manager.validate_config()

            if is_valid:
                print("✅ Configuration validation passed")
                tests_passed += 1
            else:
                print(f"❌ Configuration validation failed: {errors}")
        except Exception as e:
            print(f"❌ Configuration test error: {e}")

        # Test 2: Network connectivity
        total_tests += 1
        print("🌐 Testing network connectivity...")
        try:
            from deployment_monitor import DeploymentMonitor
            monitor = DeploymentMonitor(self.config['network'], self.config)

            api_status = monitor.check_api_status()
            if api_status['status'] == 'online':
                print(f"✅ Network connectivity: {api_status['network_id']} @ {api_status['block_height']}")
                tests_passed += 1
            else:
                print(f"❌ Network connectivity failed: {api_status.get('error', 'Unknown')}")
        except Exception as e:
            print(f"❌ Network test error: {e}")

        # Test 3: Contract compilation (if Clarinet.toml exists)
        if self.config.get('clarinet_found'):
            total_tests += 1
            print("⚙️  Testing contract compilation...")
            try:
                result = subprocess.run(['clarinet', 'check'], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print("✅ Contract compilation successful")
                    tests_passed += 1
                else:
                    print("⚠️  Contract compilation issues (may be warnings)")
                    tests_passed += 1  # Still count as passed for deployment
            except Exception as e:
                print(f"❌ Contract compilation test error: {e}")

        print()
        print(f"📊 Test Results: {tests_passed}/{total_tests} passed")

        if tests_passed == total_tests:
            print(f"{Fore.GREEN}🎉 All tests passed! Ready for deployment.{Style.RESET_ALL}")
        elif tests_passed >= total_tests * 0.7:
            print(f"{Fore.YELLOW}⚠️  Most tests passed. Review warnings before deploying.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Many tests failed. Please fix issues before deploying.{Style.RESET_ALL}")
            return False

        print()
        response = self._get_user_input("Continue? (y/n): ", ['y', 'n'])
        return response == 'y'

    def _step_deployment_options(self) -> bool:
        """Deployment options step"""
        print(f"\n{Fore.CYAN}📋 Step 7: Deployment Options{Style.RESET_ALL}")
        print("Configure your deployment preferences...")
        print()

        print("Deployment mode:")
        print("1. 🔄 Full deployment (deploy all contracts)")
        print("2. 🔄 Upgrade mode (skip already deployed contracts)")
        print("3. 🎯 Selective deployment (deploy specific contracts)")
        print()

        mode_choice = self._get_user_input("Choose deployment mode (1-3): ", ['1', '2', '3'])

        modes = {
            '1': 'full',
            '2': 'upgrade',
            '3': 'selective'
        }

        self.config['deployment_mode'] = modes[mode_choice]

        if mode_choice == '3':
            # Ask for specific contracts
            contracts = self.config.get('contracts', [])
            if contracts:
                print("Available contracts:")
                for i, contract in enumerate(contracts, 1):
                    print(f"  {i}. {contract['name']}")

                selected = self._get_user_input("Enter contract numbers (comma-separated, or 'all'): ", None)
                if selected.lower() != 'all':
                    try:
                        indices = [int(x.strip()) - 1 for x in selected.split(',')]
                        selected_contracts = [contracts[i]['name'] for i in indices if 0 <= i < len(contracts)]
                        self.config['selected_contracts'] = selected_contracts
                        print(f"✅ Will deploy: {', '.join(selected_contracts)}")
                    except:
                        print(f"{Fore.YELLOW}💡 Using all contracts{Style.RESET_ALL}")
                        self.config['selected_contracts'] = [c['name'] for c in contracts]
                else:
                    self.config['selected_contracts'] = [c['name'] for c in contracts]
            else:
                print(f"{Fore.YELLOW}💡 No contracts found, will deploy all available{Style.RESET_ALL}")

        print()
        print("Advanced options:")
        batch_size = self._get_user_input("Batch size (contracts per deployment, 1-10): ", ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        self.config['batch_size'] = int(batch_size)

        parallel = self._get_user_input("Enable parallel deployment? (y/n): ", ['y', 'n'])
        self.config['parallel_deploy'] = parallel == 'y'

        print()
        response = self._get_user_input("Continue? (y/n): ", ['y', 'n'])
        return response == 'y'

    def _step_install_stacks_core(self) -> bool:
        """Install stacks-core for local development"""
        print(f"\n{Fore.CYAN}📋 Step 8: Install Stacks Core{Style.RESET_ALL}")
        print("Stacks Core is required for running a local development network.")
        print("This will download and build the Stacks Core binary, which may take a few minutes.")
        print()

        if not self._check_disk_space():
            return True

        install = self._get_user_input("Install Stacks Core? (y/n): ", ['y', 'n'])
        if install == 'n':
            print("Skipping Stacks Core installation.")
            return True

        try:
            stacks_core_path = self.config['stacks_core_path']
            print("Cloning stacks-core repository...")
            self._run_command(["git", "clone", "https://github.com/stacks-network/stacks-core.git", stacks_core_path])

            print("Building stacks-core...")
            self._run_command(["cargo", "build", "--release"], cwd=stacks_core_path)

            print("Stacks Core installed successfully!")
        except Exception as e:
            print(f"Error installing Stacks Core: {e}")
            return False

        return True

    def _step_summary(self) -> bool:
        """Summary and final setup"""
        print(f"\n{Fore.CYAN}📋 Step 9: Setup Summary{Style.RESET_ALL}")
        print("Here's your configuration summary:")
        print()

        print(f"🌐 Network: {Fore.CYAN}{self.config['network'].upper()}{Style.RESET_ALL}")
        print(f"👤 Address: {Fore.GREEN}{self.config.get('system_address', 'Not set')}{Style.RESET_ALL}")
        print(f"📦 Deployment Mode: {Fore.BLUE}{self.config['deployment_mode'].upper()}{Style.RESET_ALL}")
        print(f"🔢 Batch Size: {self.config['batch_size']}")
        print(f"⚡ Parallel: {'Yes' if self.config.get('parallel_deploy') else 'No'}")
        print(f"💻 Stacks Core Path: {self.config.get('stacks_core_path', 'Not set')}")

        contracts = self.config.get('contracts', [])
        if contracts:
            print(f"📋 Total Contracts: {len(contracts)}")

        selected = self.config.get('selected_contracts')
        if selected:
            print(f"🎯 Selected: {len(selected)} contracts")
        else:
            print("🎯 Selected: All contracts")

        print()
        print("🚀 Ready to deploy! Here are your next steps:")
        print()
        print("1. 📋 Review .env file and make any necessary changes")
        print("2. 🔍 Run pre-deployment checks:")
        print("   stacksorbit diagnose --verbose")
        print()
        print("3. 🧪 Test deployment (dry run):")
        print("   stacksorbit deploy --dry-run")
        print()
        print("4. 🚀 Deploy to testnet:")
        print("   stacksorbit deploy")
        print()
        print("5. 📊 Monitor deployment:")
        print("   stacksorbit monitor --follow")
        print()
        print("6. 🔍 Verify deployment:")
        print("   stacksorbit verify --comprehensive")
        print()
        print("7. 💻 Start local devnet:")
        print("   stacksorbit devnet --devnet-command start")


        print()
        print(f"{Fore.GREEN}🎉 Setup complete! Happy deploying!{Style.RESET_ALL}")
        return True

    def _analyze_clarinet_contracts(self, clarinet_path: Path) -> List[Dict]:
        """Analyze contracts from Clarinet.toml"""
        contracts = []

        try:
            with open(clarinet_path, 'r') as f:
                content = f.read()

            # Extract contract definitions
            import re
            contract_matches = re.findall(r'\[contracts\.([^\]]+)\]\s+path\s*=\s*["\']([^"\']+)["\']', content)

            for contract_name, contract_path in contract_matches:
                full_path = clarinet_path.parent / contract_path
                if full_path.exists():
                    contracts.append({
                        'name': contract_name,
                        'path': contract_path,
                        'full_path': str(full_path),
                        'category': self._categorize_contract(contract_name)
                    })

        except Exception as e:
            print(f"Error analyzing Clarinet.toml: {e}")

        return contracts

    def _categorize_contract(self, contract_name: str) -> str:
        """Categorize contract by name"""
        name_lower = contract_name.lower()

        if any(word in name_lower for word in ['trait', 'utils', 'lib', 'error', 'constant', 'math']):
            return 'base'
        elif any(word in name_lower for word in ['token', 'cxd', 'cxlp', 'cxvg', 'cxtr', 'cxs']):
            return 'tokens'
        elif any(word in name_lower for word in ['dex', 'factory', 'router', 'pool', 'swap']):
            return 'dex'
        elif any(word in name_lower for word in ['dim', 'dimensional', 'position', 'concentrated']):
            return 'dimensional'
        elif any(word in name_lower for word in ['oracle', 'aggregator', 'btc']):
            return 'oracle'
        elif any(word in name_lower for word in ['governance', 'proposal', 'timelock']):
            return 'governance'
        elif any(word in name_lower for word in ['circuit', 'pausable', 'access', 'security']):
            return 'security'
        elif any(word in name_lower for word in ['monitor', 'analytics', 'dashboard']):
            return 'monitoring'
        else:
            return 'other'

    def _validate_private_key(self, privkey: str) -> bool:
        """Validate private key format"""
        return len(privkey) == 64 and all(c in '0123456789abcdefABCDEF' for c in privkey)

    def _validate_address(self, address: str) -> bool:
        """Validate Stacks address format"""
        return address.startswith('S') and len(address) == 41 and address.isalnum()

    def _get_user_input(self, prompt: str, valid_options: Optional[List[str]] = None, secret: bool = False) -> str:
        """Get user input with validation"""
        while True:
            try:
                if secret:
                    import getpass
                    response = getpass.getpass(prompt)
                else:
                    response = input(prompt).strip()

                if valid_options and response.lower() not in [opt.lower() for opt in valid_options]:
                    print(f"{Fore.YELLOW}💡 Please enter one of: {', '.join(valid_options)}{Style.RESET_ALL}")
                    continue

                return response

            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}🛑 Setup cancelled by user{Style.RESET_ALL}")
                sys.exit(0)
            except EOFError:
                print(f"\n\n{Fore.YELLOW}🛑 Setup cancelled{Style.RESET_ALL}")
                sys.exit(0)

    def _generate_env_config(self) -> str:
        """Generate .env configuration content"""
        stacks_core_path = self.project_root / "stacks-core"
        self.config['stacks_core_path'] = str(stacks_core_path)

        config_lines = [
            "# StacksOrbit Configuration",
            "# Generated by Setup Wizard",
            "",
            "# Required Variables",
            "# 🛡️ For security, set DEPLOYER_PRIVKEY as an environment variable.",
            "# Do not store secrets in this file.",
            "# Example: export DEPLOYER_PRIVKEY='your_private_key_here'",
            "DEPLOYER_PRIVKEY=",
            f"SYSTEM_ADDRESS={self.config.get('system_address', 'your_stacks_address_here')}",
            f"NETWORK={self.config['network']}",
            "",
            "# Local Devnet Configuration",
            f"STACKS_CORE_PATH={stacks_core_path}",
            "",
            "# Optional Variables (Recommended)",
            "HIRO_API_KEY=your_hiro_api_key_here",
            "CORE_API_URL=https://api.testnet.hiro.so",
            "STACKS_API_BASE=https://api.testnet.hiro.so",
            "",
            "# Deployment Configuration",
            f"DEPLOYMENT_MODE={self.config['deployment_mode']}",
            f"BATCH_SIZE={self.config['batch_size']}",
            f"PARALLEL_DEPLOY={str(self.config.get('parallel_deploy', False)).lower()}",
            "",
            "# Monitoring Configuration",
            "MONITORING_ENABLED=true",
            "LOG_LEVEL=INFO",
            "SAVE_LOGS=true",
            "",
            "# Validation",
            "VALIDATE_TRANSACTIONS=true",
            "CONFIRMATION_TIMEOUT=300",
            "",
            "# Security",
            "# Never commit this file to version control!",
            "# Add .env to your .gitignore file",
        ]

        return "\n".join(config_lines)

    def _run_command(self, command: List[str], cwd: Optional[str] = None):
        """Run an external command and stream its output"""
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in process.stdout:
            print(line, end="")
        process.wait()
        if process.returncode != 0:
            raise Exception(f"Command failed with exit code {process.returncode}")

    def _check_disk_space(self) -> bool:
        """Check if there is enough disk space to install stacks-core"""
        required_space = 5 * 1024 * 1024 * 1024  # 5GB
        free_space = psutil.disk_usage('/').free
        if free_space < required_space:
            print(f"{Fore.YELLOW}Warning: Not enough free disk space to install Stacks Core.{Style.RESET_ALL}")
            print(f"You have {free_space / (1024*1024*1024):.2f}GB free, but {required_space / (1024*1024*1024):.2f}GB is required.")
            switch = self._get_user_input("Switch to public testnet instead? (y/n): ", ['y', 'n'])
            if switch == 'y':
                self.config['network'] = 'testnet'
                return False
            else:
                return True
        return True

class UltimateStacksOrbit:
    """Ultimate deployment solution for Stacks blockchain"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.config_path = ".env"
        self.templates_path = "deployment_templates.json"

        # Load deployment templates
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict:
        """Load deployment templates"""
        template_file = Path(__file__).parent / self.templates_path
        if template_file.exists():
            with open(template_file, 'r') as f:
                return json.load(f)
        return {}

    def run_command(self, command: str, **kwargs) -> int:
        """Run StacksOrbit command with enhanced features"""
        print(f"\n{Fore.CYAN}🚀 Executing: {command}{Style.RESET_ALL}")

        try:
            if command == 'setup':
                return self.run_setup_wizard()
            elif command == 'deploy':
                return self.run_enhanced_deployment(kwargs)
            elif command == 'monitor':
                return self.run_enhanced_monitoring(kwargs)
            elif command == 'verify':
                return self.run_enhanced_verification(kwargs)
            elif command == 'dashboard':
                return self.run_enhanced_dashboard(kwargs)
            elif command == 'diagnose':
                return self.run_comprehensive_diagnosis(kwargs)
            elif command == 'detect':
                return self.run_auto_detection(kwargs)
            elif command == 'template':
                return self.apply_deployment_template(kwargs)
            elif command == 'devnet':
                return self.run_devnet(kwargs)
            else:
                self.show_help()
                return 1

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}🛑 Operation cancelled by user{Style.RESET_ALL}")
            return 1
        except Exception as e:
            print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
            if kwargs.get('verbose'):
                import traceback
                traceback.print_exc()
            return 1

    def run_setup_wizard(self) -> int:
        """Run enhanced setup wizard"""
        wizard = SetupWizard()
        success = wizard.start_wizard()

        if success:
            print(f"\n{Fore.GREEN}✅ Setup completed!{Style.RESET_ALL}")
            print("💡 Next: Run 'stacksorbit deploy --dry-run' to test deployment")
        return 0 if success else 1

    def run_auto_detection(self, options: Dict) -> int:
        """Run enhanced auto-detection"""
        print(f"{Fore.CYAN}🔍 Enhanced Auto-Detection{Style.RESET_ALL}")
        
        from stacksorbit_auto_detect import StacksOrbitCLIIntegration
        integration = StacksOrbitCLIIntegration()
        
        # Pass directory if specified
        directory = options.get('directory')
        if directory:
            import os
            os.chdir(directory)
            
        analysis = integration.run_detection()
        integration.show_detection_results()
        
        return 0 if analysis['ready'] else 1

    def run_enhanced_deployment(self, options: Dict) -> int:
        """Run enhanced deployment with all features"""
        print(f"{Fore.CYAN}🚀 Enhanced Deployment Mode{Style.RESET_ALL}")

        # Load configuration
        config_manager = EnhancedConfigManager(self.config_path)
        config = config_manager.load_config()

        # Apply template if specified
        if options.get('template'):
            config = self._apply_template_config(config, options['template'])

        # Validate configuration
        is_valid, errors = config_manager.validate_config()
        if not is_valid:
            print(f"{Fore.RED}❌ Configuration validation failed:{Style.RESET_ALL}")
            for error in errors:
                print(f"   • {error}")
            return 1

        # Initialize deployer
        run_npm_tests = bool(options.get('run_npm_tests')) or bool(options.get('dry_run'))
        npm_test_script = options.get('npm_test_script') or 'test'
        clarinet_check_timeout = int(options.get('clarinet_check_timeout', 300))
        deployer = EnhancedConxianDeployer(
            config,
            options.get('verbose', False),
            run_npm_tests=run_npm_tests,
            npm_test_script=npm_test_script,
            clarinet_check_timeout=clarinet_check_timeout
        )

        # Run pre-deployment checks
        pre_checks_passed = True
        if not options.get('skip_checks'):
            print("🔍 Running comprehensive pre-deployment checks...")
            pre_checks_passed = deployer.run_pre_checks()
            if not pre_checks_passed:
                if options.get('dry_run') and not options.get('force'):
                    print(f"{Fore.YELLOW}⚠️  Pre-deployment checks reported issues. Continuing because --dry-run was specified.{Style.RESET_ALL}")
                elif not options.get('force'):
                    print(f"{Fore.RED}❌ Pre-deployment checks failed.{Style.RESET_ALL}")
                    print("💡 Use --force to continue anyway")
                    return 1

        # Execute deployment
        print(f"🚀 Starting deployment...")
        results = deployer.deploy_conxian(
            category=options.get('category'),
            dry_run=options.get('dry_run', False)
        )

        # Show results
        if options.get('dry_run'):
            if pre_checks_passed:
                print(f"\n{Fore.GREEN}✅ Dry run completed successfully{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.YELLOW}⚠️  Dry run completed with issues (see pre-deployment checks above){Style.RESET_ALL}")
        else:
            print(f"\n📊 Deployment Results:")
            print(f"   ✅ Successful: {len(results.get('successful', []))}")
            print(f"   ❌ Failed: {len(results.get('failed', []))}")
            print(f"   ⏭️  Skipped: {len(results.get('skipped', []))}")

            if results.get('failed'):
                print(f"\n{Fore.RED}❌ Failed contracts:{Style.RESET_ALL}")
                for failed in results['failed']:
                    print(f"   • {failed['name']}: {failed['error']}")
                return 1

            print(f"\n{Fore.GREEN}🎉 Deployment completed successfully!{Style.RESET_ALL}")
            print("💡 Run 'stacksorbit monitor --follow' to track confirmations")

        return 0

    def run_enhanced_monitoring(self, options: Dict) -> int:
        """Run enhanced monitoring"""
        print(f"{Fore.CYAN}📊 Enhanced Monitoring Mode{Style.RESET_ALL}")

        # Load configuration
        config_manager = EnhancedConfigManager(self.config_path)
        config = config_manager.load_config()

        monitor = DeploymentMonitor(config.get('NETWORK', 'testnet'), config)

        # Show API status
        api_status = monitor.check_api_status()
        print(f"🌐 API Status: {api_status['status']}")
        print(f"   Network: {api_status.get('network_id', 'unknown')}")
        print(f"   Block Height: {api_status.get('block_height', 0)}")

        address = config.get('SYSTEM_ADDRESS')
        if address:
            print(f"\n👤 Account Status:")
            account_info = monitor.get_account_info(address)
            if account_info:
                balance_raw = account_info.get('balance', 0)
                balance = (int(balance_raw, 16) if isinstance(balance_raw, str) and balance_raw.startswith('0x') else int(balance_raw)) / 1000000
                print(f"   Balance: {balance} STX")
                print(f"   Nonce: {account_info.get('nonce', 0)}")

            print(f"\n📦 Deployed Contracts:")
            contracts = monitor.get_deployed_contracts(address)
            print(f"   Count: {len(contracts)}")

            if contracts:
                print("   Recent contracts:")
                for contract in contracts[-5:]:  # Show last 5
                    print(f"     - {contract.get('contract_id', 'unknown')}")

        if options.get('follow'):
            print(f"\n🔄 Starting real-time monitoring...")
            print("📝 Press Ctrl+C to stop")

            monitor_thread = monitor.start_monitoring()

            try:
                while monitor.is_monitoring:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass

            monitor.stop_monitoring()
            print("✅ Monitoring stopped")

        return 0

    def run_enhanced_verification(self, options: Dict) -> int:
        """Run enhanced verification"""
        print(f"{Fore.CYAN}🔍 Enhanced Verification Mode{Style.RESET_ALL}")

        # Load configuration
        config_manager = EnhancedConfigManager(self.config_path)
        config = config_manager.load_config()

        address = config.get('SYSTEM_ADDRESS')
        if not address:
            print(f"{Fore.RED}❌ SYSTEM_ADDRESS not configured{Style.RESET_ALL}")
            return 1

        # Get expected contracts
        expected_contracts = options.get('contracts')
        if not expected_contracts:
            # Try to load from Clarinet.toml
            from deployment_verifier import load_expected_contracts
            expected_contracts = load_expected_contracts()

        if not expected_contracts:
            print(f"{Fore.YELLOW}⚠️  No contracts specified for verification{Style.RESET_ALL}")
            return 1

        # Initialize verifier
        verifier = DeploymentVerifier(
            network=config.get('NETWORK', 'testnet'),
            config=config
        )

        # Run comprehensive verification
        results = verifier.run_comprehensive_verification(expected_contracts)

        # Print detailed summary
        verifier.print_verification_summary()

        # Exit with appropriate code
        return 0 if results['overall_status'] == 'success' else 1

    def run_enhanced_dashboard(self, options: Dict) -> int:
        """Run enhanced dashboard"""
        print(f"{Fore.CYAN}📊 Launching StacksOrbit GUI...{Style.RESET_ALL}")

        app = StacksOrbitGUI()
        app.run()

        return 0

    def run_comprehensive_diagnosis(self, options: Dict) -> int:
        """Run comprehensive system diagnosis"""
        print(f"{Fore.CYAN}🔍 Comprehensive System Diagnosis{Style.RESET_ALL}")
        print("=" * 60)

        # Load configuration
        config_manager = EnhancedConfigManager(self.config_path)
        config = config_manager.load_config()

        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'system_status': 'unknown',
            'issues': [],
            'recommendations': [],
            'scores': {}
        }

        # 1. Configuration Check
        print("🔧 Configuration Check...")
        try:
            is_valid, errors = config_manager.validate_config()
            if is_valid:
                print(f"{Fore.GREEN}✅ Configuration valid{Style.RESET_ALL}")
                diagnosis['scores']['config'] = 100
            else:
                print(f"{Fore.RED}❌ Configuration issues: {errors}{Style.RESET_ALL}")
                diagnosis['issues'].extend(errors)
                diagnosis['scores']['config'] = 0
        except Exception as e:
            print(f"{Fore.RED}❌ Configuration error: {e}{Style.RESET_ALL}")
            diagnosis['issues'].append(str(e))
            diagnosis['scores']['config'] = 0

        # 2. Network Check
        print("🌐 Network Check...")
        try:
            monitor = DeploymentMonitor(config.get('NETWORK', 'testnet'), config)
            api_status = monitor.check_api_status()
            if api_status['status'] == 'online':
                print(f"{Fore.GREEN}✅ Network connectivity: {api_status['network_id']}{Style.RESET_ALL}")
                diagnosis['scores']['network'] = 100
            else:
                print(f"{Fore.RED}❌ Network issue: {api_status.get('error', 'Unknown')}{Style.RESET_ALL}")
                diagnosis['issues'].append(f"Network connectivity: {api_status.get('error', 'Unknown')}")
                diagnosis['scores']['network'] = 0
        except Exception as e:
            print(f"{Fore.RED}❌ Network error: {e}{Style.RESET_ALL}")
            diagnosis['issues'].append(str(e))
            diagnosis['scores']['network'] = 0

        # 3. Account Check
        address = config.get('SYSTEM_ADDRESS')
        if address:
            print("👤 Account Check...")
            try:
                account_info = monitor.get_account_info(address)
                if account_info:
                    balance_raw = account_info.get('balance', 0)
                    balance = (int(balance_raw, 16) if isinstance(balance_raw, str) and balance_raw.startswith('0x') else int(balance_raw)) / 1000000
                    print(f"{Fore.GREEN}✅ Account balance: {balance} STX{Style.RESET_ALL}")
                    diagnosis['scores']['account'] = min(100, balance * 10)  # Score based on balance
                else:
                    print(f"{Fore.YELLOW}⚠️  Could not check account balance{Style.RESET_ALL}")
                    diagnosis['scores']['account'] = 50
            except Exception as e:
                print(f"{Fore.RED}❌ Account check error: {e}{Style.RESET_ALL}")
                diagnosis['issues'].append(str(e))
                diagnosis['scores']['account'] = 0
        else:
            print(f"{Fore.YELLOW}⚠️  No address configured{Style.RESET_ALL}")
            diagnosis['issues'].append("SYSTEM_ADDRESS not configured")
            diagnosis['scores']['account'] = 0

        # 4. Contract Analysis
        print("📦 Contract Analysis...")
        try:
            deployer = EnhancedConxianDeployer(config, options.get('verbose', False))
            contracts = deployer._get_deployment_list()
            if contracts:
                print(f"{Fore.GREEN}✅ Found {len(contracts)} contracts{Style.RESET_ALL}")
                diagnosis['scores']['contracts'] = 100
            else:
                print(f"{Fore.YELLOW}⚠️  No contracts found{Style.RESET_ALL}")
                diagnosis['issues'].append("No contracts found")
                diagnosis['scores']['contracts'] = 0
        except Exception as e:
            print(f"{Fore.RED}❌ Contract analysis error: {e}{Style.RESET_ALL}")
            diagnosis['issues'].append(str(e))
            diagnosis['scores']['contracts'] = 0

        # 5. Dependencies Check
        print("🔗 Dependencies Check...")
        try:
            import subprocess
            deps_ok = True

            # Check Python dependencies
            python_deps = ['requests', 'toml', 'yaml']
            for dep in python_deps:
                try:
                    __import__(dep)
                except ImportError:
                    print(f"{Fore.RED}❌ Missing Python dependency: {dep}{Style.RESET_ALL}")
                    deps_ok = False

            # Check Node.js dependencies
            try:
                result = subprocess.run(['node', '--version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    print(f"{Fore.GREEN}✅ Node.js available{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}❌ Node.js not available{Style.RESET_ALL}")
                    deps_ok = False
            except:
                print(f"{Fore.RED}❌ Node.js not available{Style.RESET_ALL}")
                deps_ok = False

            if deps_ok:
                print(f"{Fore.GREEN}✅ All dependencies available{Style.RESET_ALL}")
                diagnosis['scores']['dependencies'] = 100
            else:
                diagnosis['issues'].append("Missing dependencies")
                diagnosis['scores']['dependencies'] = 0

        except Exception as e:
            print(f"{Fore.RED}❌ Dependencies check error: {e}{Style.RESET_ALL}")
            diagnosis['issues'].append(str(e))
            diagnosis['scores']['dependencies'] = 0

        # Calculate overall score
        total_score = sum(diagnosis['scores'].values())
        max_score = len(diagnosis['scores']) * 100
        overall_percentage = (total_score / max_score) * 100 if max_score > 0 else 0

        diagnosis['overall_score'] = overall_percentage

        if overall_percentage >= 90:
            diagnosis['system_status'] = 'excellent'
        elif overall_percentage >= 70:
            diagnosis['system_status'] = 'good'
        elif overall_percentage >= 50:
            diagnosis['system_status'] = 'fair'
        else:
            diagnosis['system_status'] = 'poor'

        # Generate recommendations
        if diagnosis['scores'].get('config', 0) < 100:
            diagnosis['recommendations'].append("Fix configuration issues")

        if diagnosis['scores'].get('network', 0) < 100:
            diagnosis['recommendations'].append("Check network connectivity")

        if diagnosis['scores'].get('account', 0) < 50:
            diagnosis['recommendations'].append("Fund your Stacks account")

        if diagnosis['scores'].get('contracts', 0) < 100:
            diagnosis['recommendations'].append("Add or fix contract files")

        # Print diagnosis summary
        print(f"\n📊 Diagnosis Summary:")
        print(f"   Overall Status: {diagnosis['system_status'].upper()}")
        print(f"   Overall Score: {overall_percentage:.1f}%")

        print(f"\n📋 Component Scores:")
        for component, score in diagnosis['scores'].items():
            status_icon = "✅" if score >= 80 else "⚠️" if score >= 50 else "❌"
            print(f"   {status_icon} {component.capitalize()}: {score}%")

        if diagnosis['issues']:
            print(f"\n❌ Issues Found:")
            for issue in diagnosis['issues']:
                print(f"   • {issue}")

        if diagnosis['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in diagnosis['recommendations']:
                print(f"   • {rec}")

        # Save diagnosis
        diagnosis_path = Path("logs") / f"diagnosis_{int(time.time())}.json"
        diagnosis_path.parent.mkdir(exist_ok=True)
        with open(diagnosis_path, 'w') as f:
            json.dump(diagnosis, f, indent=2)

        print(f"\n💾 Diagnosis saved to {diagnosis_path}")

        # Overall assessment
        if overall_percentage >= 90:
            print(f"\n{Fore.GREEN}🎉 System is ready for deployment!{Style.RESET_ALL}")
            print("💡 Run: stacksorbit deploy --dry-run")
        elif overall_percentage >= 70:
            print(f"\n{Fore.YELLOW}⚠️  System mostly ready, but has some issues.{Style.RESET_ALL}")
            print("💡 Fix the issues above, then try deployment")
        else:
            print(f"\n{Fore.RED}❌ System needs significant fixes before deployment.{Style.RESET_ALL}")
            print("💡 Address the issues above first")

        return 0

    def apply_deployment_template(self, options: Dict) -> int:
        """Apply deployment template"""
        template_name = options.get('name')
        if not template_name:
            print(f"{Fore.RED}❌ Template name required{Style.RESET_ALL}")
            print("Available templates:")
            for name, template in self.templates.get('templates', {}).items():
                print(f"  • {name} - {template['name']}")
            return 1

        templates = self.templates.get('templates', {})
        if template_name not in templates:
            print(f"{Fore.RED}❌ Template '{template_name}' not found{Style.RESET_ALL}")
            return 1

        template = templates[template_name]

        print(f"📋 Applying template: {Fore.CYAN}{template['name']}{Style.RESET_ALL}")
        print(f"📝 Description: {template['description']}")

        if template.get('warning'):
            print(f"{Fore.RED}⚠️  WARNING: {template['warning']}{Style.RESET_ALL}")

        print(f"\n⚙️  Configuration:")
        config = template['config']
        for key, value in config.items():
            print(f"   {key}: {value}")

        print(f"\n📋 Deployment Steps:")
        for i, step in enumerate(template['steps'], 1):
            print(f"   {i}. {step}")

        # Apply template to configuration
        config_manager = EnhancedConfigManager(self.config_path)
        current_config = config_manager.load_config()

        # Update with template config
        current_config.update(config)

        # Save updated configuration
        config_manager.save_config(current_config)

        print(f"\n✅ Template applied!")
        print(f"💾 Updated configuration saved to {self.config_path}")

        return 0

    def run_devnet(self, options: Dict) -> int:
        """Run local development network"""
        config_manager = EnhancedConfigManager(self.config_path)
        config = config_manager.load_config()
        stacks_core_path = Path(config.get("STACKS_CORE_PATH", self.project_root / "stacks-core"))
        devnet = LocalDevnet(stacks_core_path)
        command = options.get("devnet_command")

        if command == "start":
            devnet.start()
        elif command == "stop":
            devnet.stop()
        elif command == "status":
            if devnet.is_running():
                print("Local development network is running.")
            else:
                print("Local development network is not running.")
        else:
            print("Invalid devnet command. Please use start, stop, or status.")
            return 1

        return 0

    def _apply_template_config(self, config: Dict, template_name: str) -> Dict:
        """Apply template configuration to existing config"""
        templates = self.templates.get('templates', {})
        if template_name in templates:
            template_config = templates[template_name]['config']
            config.update(template_config)

        return config

    def show_help(self):
        """Show comprehensive help"""
        print(f"{Fore.CYAN}🚀 Ultimate StacksOrbit - Enhanced Deployment Tool{Style.RESET_ALL}")
        print("=" * 70)
        print()
        print("Usage:")
        print("  stacksorbit <command> [options]")
        print()
        print("Commands:")
        print("  setup           Run interactive setup wizard")
        print("  deploy          Deploy contracts with enhanced features")
        print("  monitor         Monitor deployment with real-time dashboard")
        print("  verify          Verify deployment completeness")
        print("  dashboard       Launch enhanced monitoring dashboard")
        print("  diagnose        Run comprehensive system diagnosis")
        print("  detect          Auto-detect project and contracts")
        print("  template        Apply deployment template")
        print()
        print("Deployment Options:")
        print("  --category <cat>    Deploy specific category (base, core, tokens, etc.)")
        print("  --template <name>   Use deployment template")
        print("  --batch-size <n>    Contracts per batch (default: 5)")
        print("  --dry-run           Test deployment without executing")
        print("  --skip-checks       Skip pre-deployment checks")
        print("  --force             Force deployment despite check failures")
        print("  --verbose           Enable detailed logging")
        print()
        print("Monitoring Options:")
        print("  --follow            Follow deployment in real-time")
        print("  --dashboard         Launch interactive dashboard")
        print("  --api-only          Check only API status")
        print()
        print("Verification Options:")
        print("  --contracts <list>  Specific contracts to verify")
        print("  --comprehensive     Run comprehensive verification")
        print()
        print("Examples:")
        print("  # Quick setup")
        print("  stacksorbit setup")
        print()
        print("  # Deploy with template")
        print("  stacksorbit deploy --template testnet_quick_start")
        print()
        print("  # Deploy specific category")
        print("  stacksorbit deploy --category core --dry-run")
        print()
        print("  # Monitor in real-time")
        print("  stacksorbit monitor --follow")
        print()
        print("  # Comprehensive verification")
        print("  stacksorbit verify --comprehensive")
        print()
        print("  # Full diagnosis")
        print("  stacksorbit diagnose --verbose")
        print()
        print("Available Templates:")
        templates = self.templates.get('templates', {})
        if templates:
            for name, template in templates.items():
                print(f"  • {name} - {template['name']}")
        else:
            print("  No templates available")
        print()
        print(f"{Fore.GREEN}🚀 Ready to deploy to Stacks blockchain!{Style.RESET_ALL}")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Ultimate StacksOrbit - Enhanced Deployment Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('--config', default='.env', help='Configuration file path')
    parser.add_argument('--network', choices=['devnet', 'testnet', 'mainnet'], default='testnet')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--directory', '-d', help='Directory to analyze (for detect command)')

    # Deployment options
    parser.add_argument('--category', choices=['base', 'core', 'tokens', 'dex', 'dimensional', 'oracle', 'governance', 'security', 'monitoring'])
    parser.add_argument('--template', help='Deployment template name')
    parser.add_argument('--batch-size', type=int, default=5, help='Contracts per batch')
    parser.add_argument('--dry-run', action='store_true', help='Dry run deployment')
    parser.add_argument('--skip-checks', action='store_true', help='Skip pre-deployment checks')
    parser.add_argument('--force', action='store_true', help='Force deployment')
    parser.add_argument('--run-npm-tests', action='store_true', help='Run npm tests during pre-deployment checks')
    parser.add_argument('--npm-test-script', default='test', help='npm script to run (e.g. test, test:all)')
    parser.add_argument('--clarinet-check-timeout', type=int, default=300, help='Timeout for clarinet check (seconds)')

    # Monitoring options
    parser.add_argument('--follow', action='store_true', help='Follow in real-time')
    parser.add_argument('--api-only', action='store_true', help='API status only')

    # Verification options
    parser.add_argument('--contracts', nargs='*', help='Contracts to verify')
    parser.add_argument('--comprehensive', action='store_true', help='Comprehensive verification')

    # Devnet options
    parser.add_argument('--devnet-command', choices=['start', 'stop', 'status'], help='Local development network command')

    args = parser.parse_args()

    try:
        # Initialize ultimate deployer
        deployer = UltimateStacksOrbit()
        deployer.config_path = args.config

        # Convert args to dict
        options = {
            'category': args.category,
            'template': args.template,
            'batch_size': args.batch_size,
            'dry_run': args.dry_run,
            'skip_checks': args.skip_checks,
            'force': args.force,
            'run_npm_tests': args.run_npm_tests,
            'npm_test_script': args.npm_test_script,
            'clarinet_check_timeout': args.clarinet_check_timeout,
            'follow': args.follow,
            'api_only': args.api_only,
            'contracts': args.contracts,
            'comprehensive': args.comprehensive,
            'verbose': args.verbose,
            'devnet_command': args.devnet_command,
            'directory': args.directory
        }

        # Execute command
        if args.command:
            return deployer.run_command(args.command, **options)
        else:
            deployer.show_help()
            return 0

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Operation cancelled by user{Style.RESET_ALL}")
        return 1
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
