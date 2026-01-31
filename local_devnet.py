#!/usr/bin/env python3
"""
Local Development Network for StacksOrbit
Provides a simple interface for managing a local Stacks development network
"""

import os
import sys
import subprocess
import time
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None


class LocalDevnet:
    """A simple interface for managing a local Stacks development network"""

    def __init__(self, stacks_core_path: Path):
        self.stacks_core_path = stacks_core_path
        self.pid_file = self.stacks_core_path / ".devnet.pid"

    def start(self):
        """Starts the local development network"""
        if self.is_running():
            print("Local development network is already running.")
            return

        print("Starting local development network...")
        process = subprocess.Popen(
            [
                "cargo",
                "run",
                "--bin",
                "stacks-node",
                "--",
                "mocknet",
            ],
            cwd=self.stacks_core_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        with open(self.pid_file, "w") as f:
            f.write(str(process.pid))

        print("Local development network started.")

    def stop(self):
        """Stops the local development network"""
        if not self.is_running():
            print("Local development network is not running.")
            return

        with open(self.pid_file, "r") as f:
            pid = int(f.read())

        print(f"Stopping local development network (pid: {pid})...")
        try:
            if psutil:
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait()
            else:
                os.kill(pid, 15)  # SIGTERM
        except (ProcessLookupError, psutil.NoSuchProcess):
            print(f"Process with pid {pid} not found.")

        self.pid_file.unlink()
        print("Local development network stopped.")

    def is_running(self) -> bool:
        """Returns True if the local development network is running"""
        if not self.pid_file.exists():
            return False

        with open(self.pid_file, "r") as f:
            try:
                pid = int(f.read())
            except ValueError:
                return False

        if not psutil:
            try:
                os.kill(pid, 0)
            except OSError:
                return False
            else:
                return True

        if psutil.pid_exists(pid):
            return True
        else:
            # The process is not running, so the PID file is stale.
            self.pid_file.unlink()
            return False
