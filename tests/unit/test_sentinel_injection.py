import os
import unittest
from stacksorbit_secrets import save_secure_config

class TestSentinelInjection(unittest.TestCase):

    def setUp(self):
        self.test_file = ".env.injection.test"

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_save_secure_config_sanitizes_keys(self):
        # A malicious config dictionary with keys containing newlines and equals signs
        # We avoid using the word 'KEY' because it triggers secret redaction.
        malicious_config = {
            "NORMAL_VAR": "normal_value",
            "INJECTED\nVAR": "injected_value",
            "INJECTED\rVAR": "injected_value_r",
            "VAR_WITH=EQUALS": "value_with_equals"
        }

        save_secure_config(self.test_file, malicious_config)

        # Read the file and verify sanitization
        with open(self.test_file, "r") as f:
            content = f.read()

        # Check that newlines were removed from keys
        self.assertIn("INJECTEDVAR=injected_value", content)
        self.assertIn("INJECTEDVAR=injected_value_r", content)

        # Check that equals signs were removed from keys
        self.assertIn("VAR_WITHEQUALS=value_with_equals", content)

        # Verify normal key is still there
        self.assertIn("NORMAL_VAR=normal_value", content)

        # Verify no raw newlines in keys (which would cause multiple lines)
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        self.assertEqual(len(lines), 4)

if __name__ == '__main__':
    unittest.main()
