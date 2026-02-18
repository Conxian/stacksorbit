#!/usr/bin/env python3
import time
from pathlib import Path
from unittest.mock import MagicMock
from enhanced_auto_detector import GenericStacksAutoDetector

def benchmark():
    # Mocking external calls
    import deployment_monitor
    deployment_monitor.DeploymentMonitor.get_account_info = MagicMock(return_value={"balance": "0", "nonce": 0})
    deployment_monitor.DeploymentMonitor.get_deployed_contracts = MagicMock(return_value=[])
    deployment_monitor.DeploymentMonitor.check_api_status = MagicMock(return_value={"status": "online", "block_height": 0})

    detector = GenericStacksAutoDetector()

    # Simulate a large project by adding many files to the cache
    cache_key = str(Path.cwd())
    detector.project_files_cache[cache_key] = []
    for i in range(1000):
        detector.project_files_cache[cache_key].append({
            "rel_path": f"contracts/contract_{i}.clar",
            "mtime": time.time(),
            "size": 1024
        })
        detector.project_files_cache[cache_key].append({
            "rel_path": f"deployment/manifest_{i}.json",
            "mtime": time.time(),
            "size": 1024
        })

    # Warm up
    detector.detect_and_analyze()

    start_time = time.perf_counter()
    iterations = 20
    for _ in range(iterations):
        detector.contract_cache.clear()
        detector.json_cache.clear()
        detector.detect_and_analyze()

    end_time = time.perf_counter()
    total_time = end_time - start_time
    avg_time = total_time / iterations

    print(f"Total time for {iterations} iterations: {total_time:.4f}s")
    print(f"Average time per iteration: {avg_time:.4f}s")

if __name__ == "__main__":
    benchmark()
