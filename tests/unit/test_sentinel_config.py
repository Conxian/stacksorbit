import os
import unittest
from enhanced_conxian_deployment import EnhancedConfigManager

class TestSentinelConfig(unittest.TestCase):

    def setUp(self):
        self.config_path = ".env.test"
        self.environ_backup = os.environ.copy()

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.environ.clear()
        os.environ.update(self.environ_backup)

    def test_should_raise_error_if_secret_in_env_file(self):
        # Create a dummy .env file with a secret
        with open(self.config_path, "w") as f:
            f.write("SYSTEM_PRIVKEY=a_very_secret_key\n")

        config_manager = EnhancedConfigManager(config_path=self.config_path)

        # Verify that loading the config raises a ValueError
        with self.assertRaises(ValueError) as context:
            config_manager.load_config()

        self.assertIn("Sentinel Security Error", str(context.exception))
        self.assertIn("SYSTEM_PRIVKEY", str(context.exception))

if __name__ == '__main__':
    unittest.main()
