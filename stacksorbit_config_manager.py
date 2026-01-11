import os
import sys
import argparse
import toml
from dotenv import load_dotenv, dotenv_values

class ConfigManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.config = {}

    def scan_and_load_configs(self):
        """
        Scans the base_path for .env and .toml files and loads their contents.
        """
        print(f"Scanning for configuration files in: {self.base_path}")

        # Load .env files and environment variables
        env_path = os.path.join(self.base_path, '.env')

        # Sentinel Security Enhancement:
        # 1. Inspect the .env file for secrets before loading it.
        if os.path.exists(env_path):
            # Use dotenv_values to get the contents of the .env file as a dict without modifying the environment.
            file_vars = dotenv_values(dotenv_path=env_path)

            privkey_names = ['DEPLOYER_PRIVKEY', 'STACKS_DEPLOYER_PRIVKEY', 'STACKS_PRIVKEY']
            is_privkey_in_env = any(os.environ.get(key) for key in privkey_names)

            # If a private key is NOT set in the environment, check if it's in the .env file.
            if not is_privkey_in_env:
                for key_name in privkey_names:
                    # If the key is in the file with a non-placeholder value, it's a security risk.
                    if file_vars.get(key_name) and file_vars[key_name] not in ('', 'your_private_key_here'):
                        error_message = (
                            f"🛡️ Sentinel Security Error: {key_name} found in .env file.\n"
                            "   Storing secrets in plaintext files is a critical security risk.\n"
                            "   For your protection, please move this secret to an environment variable and remove it from the .env file.\n"
                            "   Example: export DEPLOYER_PRIVKEY='your_private_key_here'"
                        )
                        raise ValueError(error_message)

            # 2. If the security check passes, load the .env file into the environment.
            # This preserves the original behavior for all other variables.
            load_dotenv(dotenv_path=env_path)
            self.config['env_loaded'] = True
            print(f"Loaded and validated .env file from: {env_path}")
        else:
            print(f"No .env file found at: {env_path}")

        # 3. Populate self.config from the environment, ensuring env vars take precedence.
        self.config.update(os.environ)

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