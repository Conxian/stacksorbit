import time
import sys
import os
from stacksorbit_secrets import redact_recursive

def generate_benchmark_data(num_contracts=50, source_size_kb=100):
    """Generate data structure with many large strings."""
    # Create a string that is approximately source_size_kb
    base_source = "(define-public (test-function) (ok true))\n"
    multiplier = (source_size_kb * 1024) // len(base_source)
    source = base_source * multiplier

    data = {
        "project_name": "Benchmark Project",
        "contracts": [
            {
                "name": f"contract_{i}",
                "source_code": source,
                "metadata": {"version": "1.0", "author": "Bolt"}
            }
            for i in range(num_contracts)
        ],
        "metrics": [i for i in range(1000)],
        "is_active": True
    }
    return data

def run_benchmark():
    print("⚡ Bolt: Initializing Redaction Benchmark...")
    # 50 contracts * 100KB = 5MB of source code to process
    data = generate_benchmark_data()

    # Warmup
    redact_recursive({"test": "data"})

    start = time.perf_counter()
    iterations = 20
    for _ in range(iterations):
        _ = redact_recursive(data)
    end = time.perf_counter()

    avg_time = (end - start) / iterations
    print(f"📊 Average Redaction Time (5MB dataset): {avg_time:.6f}s")

if __name__ == "__main__":
    run_benchmark()
