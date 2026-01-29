#!/usr/bin/env python3
"""
StacksOrbit - Main Entry Point
Bridges the package to the CLI implementation
"""

import sys
from stacksorbit_cli import main as cli_main

def main():
    """Main entry point for the stacksorbit package"""
    return cli_main()

if __name__ == "__main__":
    sys.exit(main())
