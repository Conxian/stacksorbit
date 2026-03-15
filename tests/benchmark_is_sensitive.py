import time
import sys
from stacksorbit_secrets import is_sensitive_value

def benchmark_is_sensitive():
    print("⚡ Bolt: Benchmarking is_sensitive_value directly...")

    # 10MB string WITHOUT whitespace to trigger zero-copy fast-fail
    large_string = "A" * (10 * 1024 * 1024)

    # Warmup
    is_sensitive_value("test")

    start = time.perf_counter()
    iterations = 50
    for _ in range(iterations):
        _ = is_sensitive_value(large_string)
    end = time.perf_counter()

    avg_time = (end - start) / iterations
    print(f"📊 Average is_sensitive_value Time (10MB string): {avg_time:.6f}s")

if __name__ == "__main__":
    benchmark_is_sensitive()
