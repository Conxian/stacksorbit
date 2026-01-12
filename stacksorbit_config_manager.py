import os
import sys
import argparse
import toml
from dotenv import load_dotenv

class ConfigManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.config = {}

    def scan_and_load_configs(self):
        """
        Scans the base_path for .env and .toml files and loads their contents.
        """
        print(f"Scanning for configuration files in: {self.base_path}")

        # Load .env files
        env_path = os.path.join(self.base_path, '.env')
        if os.path.exists(env_path):
            # Sentinel Security Enhancement: Check for private key before loading
            with open(env_path, 'r') as f:
                for line in f:
                    if line.strip().startswith('DEPLOYER_PRIVKEY='):
                        # Check if the key has a value
                        value = line.split('=', 1)[1].strip()
                        if value and value != 'your_private_key_here':
                            raise ValueError(
                                "🛡️ Sentinel Security Error: DEPLOYER_PRIVKEY found in .env file.\n"
                                "   Storing secrets in plaintext files is a critical security risk.\n"
                                "   For your protection, please move this secret to an environment variable."
                            )

            load_dotenv(dotenv_path=env_path)
            print(f"Loaded .env file from: {env_path}")
            # For demonstration, we'll just store a flag that it was loaded
            self.config['env_loaded'] = True
        else:
            print(f"No .env file found at: {env_path}")

        # Load .toml files (e.g., Clarinet.toml)
        for root, _, files in os.walk(self.base_path):
            for file in files:
                if file == 'Clarinet.toml':
                    toml_path = os.path.join(root, file)
                    try:
                        with open(toml_path, 'r', encoding='utf-8') as f:
                            toml_config = toml.load(f)
                        self.config['Clarinet.toml'] = toml_config
                        print(f"Loaded Clarinet.toml from: {toml_path}")
                    except Exception as e:
                        print(f"Error loading {file} from {toml_path}: {e}")
        return self.config

    def get_config(self):
        return self.config

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='StackOrbit Configuration Manager - scans target directory for config files')
    parser.add_argument('target', nargs='?', help='Target directory to scan (default: current directory)')
    parser.add_argument('--target-dir', help='Alternative way to specify target directory')

    # Parse arguments
    args = parser.parse_args()

    # Determine target directory
    # Use provided target directory or default to current directory
    if args.target_dir:
        target_dir = args.target_dir
    elif args.target:
        target_dir = args.target
    else:
        target_dir = os.getcwd()

    # Convert to absolute path and validate
    target_dir = os.path.abspath(target_dir)
    if not os.path.exists(target_dir):
        print(f"Error: Target directory does not exist: {target_dir}")
        sys.exit(1)

    if not os.path.isdir(target_dir):
        print(f"Error: Target path is not a directory: {target_dir}")
        sys.exit(1)

    print(f"[INFO] StackOrbit Configuration Manager")
    print(f"[INFO] Target directory: {target_dir}")
    print(f"[INFO] Starting scan...\n")

    # Create config manager and scan
    config_manager = ConfigManager(target_dir)
    loaded_configs = config_manager.scan_and_load_configs()

    print("\n--- Loaded Configurations ---")
    for key, value in loaded_configs.items():
        print(f"{key}: {value}")

    # Show summary
    print(f"\n[SUMMARY] Scan Summary:")
    print(f"   Directory scanned: {target_dir}")
    print(f"   .env files found: {1 if loaded_configs.get('env_loaded') else 0}")
    print(f"   Clarinet.toml files found: {1 if 'Clarinet.toml' in loaded_configs else 0}")
    print(f"   Total config files: {len(loaded_configs)}")

    if 'Clarinet.toml' in loaded_configs:
        clarinet_config = loaded_configs['Clarinet.toml']
        if 'contracts' in clarinet_config:
            contract_count = len(clarinet_config['contracts'])
            print(f"   Contracts in Clarinet.toml: {contract_count}")
        if 'project' in clarinet_config:
            project_name = clarinet_config['project'].get('name', 'Unknown')
            print(f"   Project name: {project_name}")

    print(f"\n[SUCCESS] Configuration scan complete!")