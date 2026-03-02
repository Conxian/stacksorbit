import time
import sys
from pathlib import Path
from stacksorbit_secrets import redact_recursive, is_sensitive_value

def generate_large_data(n=1000):
    """Generate a large data structure typical for blockchain apps."""
    contract_source = "(define-public (hello) (ok \"world\"))\n" * 1000 # ~30KB
    data = {
        "status": "online",
        "block_height": 85000,
        "contracts": [],
        "transactions": [],
        "large_numbers": [i for i in range(10000)],
        "booleans": [True, False] * 5000
    }

    for i in range(n):
        data["contracts"].append({
            "name": f"contract-{i}",
            "source": contract_source,
            "deployed_at": 84000 + i,
            "is_active": True
        })
        data["transactions"].append({
            "tx_id": "0x" + "a" * 64,
            "nonce": i,
            "fee": 1000,
            "sender": "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM",
            "is_confirmed": True
        })
    return data

def benchmark_redaction():
    data = generate_large_data(200) # 200 contracts, each with 30KB source
    print(f"Benchmarking redaction of {len(data['contracts'])} contracts...")

    start_time = time.perf_counter()
    iterations = 10
    for _ in range(iterations):
        redacted = redact_recursive(data)

    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f"Total time for {iterations} iterations: {total_time:.4f}s")
    print(f"Average time per iteration: {total_time / iterations:.4f}s")

if __name__ == "__main__":
    benchmark_redaction()
