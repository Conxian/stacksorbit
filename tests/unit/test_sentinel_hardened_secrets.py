import unittest
import os
import json
from stacksorbit_secrets import (
    redact_recursive,
    is_sensitive_key,
    save_secure_config,
)

class TestSentinelHardenedSecrets(unittest.TestCase):

    def test_new_sensitive_keywords(self):
        """Verify that new sensitive keywords are correctly identified."""
        new_keywords = [
            "MY_SALT",
            "USER_PASSPHRASE",
            "AUTH_SIGNATURE",
            "JWT_TOKEN",
            "USER_SESSION_ID",
            "HIRO_ACCESS_TOKEN",
            "CUSTOM_API_KEY",
            "DB_CREDENTIALS"
        ]
        for kw in new_keywords:
            self.assertTrue(is_sensitive_key(kw), f"Keyword {kw} should be sensitive")


    def test_newline_escaping_in_env(self):
        """Verify that newlines are escaped in .env files to prevent injection."""
        filepath = "test_newline.env"
        config = {
            "GREETING": "hello\nworld",
            "SYSTEM_ADDRESS": "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        }

        try:
            save_secure_config(filepath, config)

            with open(filepath, "r") as f:
                content = f.read()

            self.assertIn("GREETING=hello\\nworld\n", content)
            self.assertNotIn("hello\nworld", content) # Should not be a literal newline within the value

        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
            if os.path.exists(filepath + ".tmp"):
                os.remove(filepath + ".tmp")

if __name__ == '__main__':
    unittest.main()
