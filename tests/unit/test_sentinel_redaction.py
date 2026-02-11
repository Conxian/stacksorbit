import unittest
from stacksorbit_secrets import redact_recursive

class TestSentinelRedaction(unittest.TestCase):

    def test_basic_redaction(self):
        data = {
            "NETWORK": "testnet",
            "DEPLOYER_PRIVKEY": "0000000000000000000000000000000000000000000000000000000000000001",
            "HIRO_API_KEY": "some_api_key"
        }
        redacted = redact_recursive(data)
        self.assertEqual(redacted["NETWORK"], "testnet")
        self.assertEqual(redacted["DEPLOYER_PRIVKEY"], "<redacted>")
        self.assertEqual(redacted["HIRO_API_KEY"], "<redacted>")

    def test_recursive_redaction(self):
        data = {
            "project": {
                "name": "my_project",
                "secret_token": "hidden_token"
            },
            "contracts": [
                {"name": "token", "owner_pass": "secret123"},
                {"name": "dex", "admin_key": "secret456"}
            ]
        }
        redacted = redact_recursive(data)
        self.assertEqual(redacted["project"]["name"], "my_project")
        self.assertEqual(redacted["project"]["secret_token"], "<redacted>")
        self.assertEqual(redacted["contracts"][0]["owner_pass"], "<redacted>")
        self.assertEqual(redacted["contracts"][1]["admin_key"], "<redacted>")

    def test_placeholder_preservation(self):
        data = {
            "DEPLOYER_PRIVKEY": "your_private_key_here",
            "HIRO_API_KEY": "your_hiro_api_key",
            "SYSTEM_ADDRESS": "your_stacks_address_here",
            "EMPTY_KEY": ""
        }
        redacted = redact_recursive(data)
        self.assertEqual(redacted["DEPLOYER_PRIVKEY"], "your_private_key_here")
        self.assertEqual(redacted["HIRO_API_KEY"], "your_hiro_api_key")
        self.assertEqual(redacted["SYSTEM_ADDRESS"], "your_stacks_address_here")
        self.assertEqual(redacted["EMPTY_KEY"], "")

    def test_type_preservation(self):
        data = {
            "MY_PASSWORD": "secret_pass",
            "AUTH_PORT": 8080,
            "SYSTEM_MNEMONIC": "word1 word2...",
            "nested": {
                "PRIVATE_VAL": 123.45,
                "USER_PWD": "password"
            }
        }
        redacted = redact_recursive(data)
        self.assertEqual(redacted["MY_PASSWORD"], "<redacted>")
        self.assertEqual(redacted["AUTH_PORT"], 0)
        self.assertEqual(redacted["SYSTEM_MNEMONIC"], "<redacted>")
        self.assertEqual(redacted["nested"]["PRIVATE_VAL"], 0)
        self.assertEqual(redacted["nested"]["USER_PWD"], "<redacted>")

if __name__ == "__main__":
    unittest.main()
