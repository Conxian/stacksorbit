import os
import sys
import argparse
import toml
from dotenv import dotenv_values
from stacksorbit_secrets import SECRET_KEYS, is_sensitive_key, redact_recursive


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
        env_path = os.path.join(self.base_path, ".env")
        file_vars = {}

        # Sentinel Security Enhancement:
        # 1. Inspect the .env file for secrets before loading it.
        if os.path.exists(env_path):
            # Use dotenv_values to get the contents of the .env file as a dict without modifying the environment.
            file_vars = dotenv_values(dotenv_path=env_path)

            # 🛡️ Sentinel: Enforce security policy - no secrets in .env
            # We iterate over all keys in the file and use is_sensitive_key to identify secrets.
            for key, value in file_vars.items():
                if is_sensitive_key(key) and value not in (
                    "",
                    "your_private_key_here",
                    "your_hiro_api_key",
                ):
                    # If a secret is found, raise an error and exit immediately.
                    error_message = (
                        f"🛡️ Sentinel Security Error: Secret key '{key}' found in .env file.\n"
                        "   Storing secrets in plaintext files is a critical security risk and is not permitted.\n"
                        "   For your protection, please move this secret to an environment variable and remove it from the .env file.\n"
                        f"   Example: export {key}='your_secret_value_here'"
                    )
                    raise ValueError(error_message)

            self.config["env_loaded"] = True
            print(f"Loaded and validated .env file from: {env_path}")
        else:
            print(f"No .env file found at: {env_path}")

        # 3. Build the config, starting with file variables.
        self.config.update(file_vars)

        # 🛡️ Sentinel: Secure and broadened environment variable loading.
        # Load any environment variable that is in the .env file OR matches our
        # specific app secrets (SECRET_KEYS) OR has a safe app-specific prefix.
        env_overrides = {
            k: v
            for k, v in os.environ.items()
            if k in file_vars
            or k in SECRET_KEYS
            or k.startswith(("STACKS_", "STACKSORBIT_"))
        }
        self.config.update(env_overrides)

        # Load .toml files (e.g., Clarinet.toml)
        # Bolt ⚡: Optimize configuration scanning by skipping heavy directories.
        # This significantly reduces I/O and CPU usage during startup.
        ignore_dirs = {
            "node_modules",
            ".git",
            "dist",
            "build",
            ".stacksorbit",
            "logs",
            "target",
            "__pycache__",
        }

        for root, dirs, files in os.walk(self.base_path):
            # Bolt ⚡: Skip ignored and hidden directories in-place.
            dirs[:] = [
                d for d in dirs if d not in ignore_dirs and not d.startswith(".")
            ]

            for file in files:
                if file == "Clarinet.toml":
                    toml_path = os.path.join(root, file)
                    try:
                        with open(toml_path, "r", encoding="utf-8") as f:
                            toml_config = toml.load(f)
                        self.config["Clarinet.toml"] = toml_config
                        print(f"Loaded Clarinet.toml from: {toml_path}")
                    except Exception as e:
                        print(f"Error loading {file} from {toml_path}: {e}")
        return self.config

    def get_config(self):
        return self.config


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="StackOrbit Configuration Manager - scans target directory for config files"
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Target directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--target-dir", help="Alternative way to specify target directory"
    )

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

    # Redact sensitive information before printing.
    redacted_configs = redact_recursive(loaded_configs)

    print("\n--- Loaded Configurations (Redacted) ---")

    # Pretty print the redacted configuration using a helper function
    # to handle nested dictionaries with proper indentation.
    def pretty_print_config(config, indent=0):
        for key, value in config.items():
            prefix = " " * indent
            if isinstance(value, dict):
                print(f"{prefix}{key}:")
                pretty_print_config(value, indent + 2)
            else:
                print(f"{prefix}{key}: {value}")

    pretty_print_config(redacted_configs)

    # Show summary
    print(f"\n[SUMMARY] Scan Summary:")
    print(f"   Directory scanned: {target_dir}")
    print(f"   .env files found: {1 if loaded_configs.get('env_loaded') else 0}")
    print(
        f"   Clarinet.toml files found: {1 if 'Clarinet.toml' in loaded_configs else 0}"
    )
    print(f"   Total config files: {len(loaded_configs)}")

    if "Clarinet.toml" in loaded_configs:
        clarinet_config = loaded_configs["Clarinet.toml"]
        if "contracts" in clarinet_config:
            contract_count = len(clarinet_config["contracts"])
            print(f"   Contracts in Clarinet.toml: {contract_count}")
        if "project" in clarinet_config:
            project_name = clarinet_config["project"].get("name", "Unknown")
            print(f"   Project name: {project_name}")

    print(f"\n[SUCCESS] Configuration scan complete!")
