from stacksorbit_secrets import is_sensitive_key

def check_key(key):
    is_sensitive = is_sensitive_key(key)
    print(f"Key: {key:30} | Sensitive: {is_sensitive}")
    return is_sensitive

keys_to_test = [
    "PUBLIC_RECOVERY_PHRASE",
    "ADDR_SEED_PHRASE",
    "PUBLIC_MASTER_KEY",
    "VAULT_PUBLIC_KEY",
    "XPRV_PUBLIC_KEY",
    "ADMIN_PUBLIC_KEY",
    "ROOT_PUBLIC_KEY",
]

print("Checking potential security bypasses in is_sensitive_key:")
results = [check_key(k) for k in keys_to_test]

if any(not r for r in results):
    print("\n❌ SECURITY BYPASS DETECTED: Some sensitive keys with public prefixes are not being redacted.")
else:
    print("\n✅ All tested keys are correctly identified as sensitive.")
