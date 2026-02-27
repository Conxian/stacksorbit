import unittest
import json
import io
from stacksorbit_secrets import is_sensitive_key, is_sensitive_value, redact_recursive
from wallet_connect import WalletConnectHandler

class TestSentinelHardenV2(unittest.TestCase):
    def test_new_sensitive_keywords(self):
        """Verify that new keywords are correctly identified as sensitive."""
        new_keywords = [
            "MASTER_KEY", "ROOT_PASSWORD", "ADMIN_TOKEN", "BIP32_XPRV",
            "BIP39_MNEMONIC", "KUBECONFIG_DATA", "DOCKER_CONFIG",
            "DATABASE_URL", "DB_PASSWORD"
        ]
        for kw in new_keywords:
            self.assertTrue(is_sensitive_key(kw), f"Keyword '{kw}' should be sensitive")

    def test_expanded_mnemonic_lengths(self):
        """Verify that 15, 18, and 21 word mnemonics are identified as sensitive values."""
        mnemonics = {
            15: "art forum decade glow blue case mouse track merit label logic adjust total script real",
            18: "art forum decade glow blue case mouse track merit label logic adjust total script real blue case mouse",
            21: "art forum decade glow blue case mouse track merit label logic adjust total script real blue case mouse track merit label",
        }
        for length, m in mnemonics.items():
            self.assertTrue(is_sensitive_value(m), f"{length}-word mnemonic should be sensitive")

        # Also verify 12 and 24 still work
        self.assertTrue(is_sensitive_value("art forum decade glow blue case mouse track merit label logic adjust"), "12-word mnemonic should be sensitive")
        self.assertTrue(is_sensitive_value("art forum decade glow blue case mouse track merit label logic adjust total script real blue case mouse track merit label logic adjust total"), "24-word mnemonic should be sensitive")

    def test_redaction_with_new_keywords(self):
        """Verify that values associated with new keywords are redacted."""
        config = {
            "DATABASE_URL": "postgres://user:pass@localhost:5432/db",
            "DOCKER_CONFIG": '{"auths": {"https://index.docker.io/v1/": {"auth": "YWRtaW46cGFzc3dvcmQ="}}}',
            "nested": {
                "ADMIN_TOKEN": "super-secret-token"
            }
        }
        redacted = redact_recursive(config)
        self.assertEqual(redacted["DATABASE_URL"], "<redacted>")
        self.assertEqual(redacted["DOCKER_CONFIG"], "<redacted>")
        self.assertEqual(redacted["nested"]["ADMIN_TOKEN"], "<redacted>")

class MockHeaders:
    def __init__(self, headers):
        self.headers = headers
    def get(self, key, default=None):
        return self.headers.get(key, default)

class MockRequest:
    def __init__(self, body):
        self.body = body
    def makefile(self, mode, *args, **kwargs):
        return io.BytesIO(self.body)

class TestWalletConnectHardening(unittest.TestCase):
    def test_negative_content_length(self):
        """Verify that negative Content-Length returns 400."""
        # We need to mock the handler's environment
        class MockHandler(WalletConnectHandler):
            def __init__(self):
                self.headers = MockHeaders({'Content-Length': '-1'})
                self.path = '/wallet-connected'
                self.rfile = io.BytesIO(b"")
                self.wfile = io.BytesIO()
                self.error_code = None
                self.error_message = None

            def send_error(self, code, message=None, explain=None):
                self.error_code = code
                self.error_message = message

        handler = MockHandler()
        handler.do_POST()
        self.assertEqual(handler.error_code, 400)
        self.assertEqual(handler.error_message, "Invalid Content-Length")

if __name__ == "__main__":
    unittest.main()
