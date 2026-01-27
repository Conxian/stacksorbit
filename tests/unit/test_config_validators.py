import unittest
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from enhanced_conxian_deployment import EnhancedConfigManager


class TestConfigValidators(unittest.TestCase):
    def test_valid_testnet_config(self):
        cfg = {
            'DEPLOYER_PRIVKEY': 'A' * 64,
            'SYSTEM_ADDRESS': 'ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM',
            'NETWORK': 'testnet'
        }
        manager = EnhancedConfigManager('.env')
        manager.config = cfg
        ok, errs = manager.validate_config()
        self.assertTrue(ok)
        self.assertEqual(errs, [])

    def test_reject_placeholder_private_key(self):
        cfg = {
            'DEPLOYER_PRIVKEY': 'your_private_key_here',
            'SYSTEM_ADDRESS': 'ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM',
            'NETWORK': 'testnet'
        }
        manager = EnhancedConfigManager('.env')
        manager.config = cfg
        ok, errs = manager.validate_config()
        self.assertFalse(ok)
        self.assertIn('DEPLOYER_PRIVKEY uses insecure placeholder value', errs)

    def test_address_prefix_by_network(self):
        # Mainnet must start with SP
        cfg_mainnet = {
            'DEPLOYER_PRIVKEY': 'A' * 64,
            'SYSTEM_ADDRESS': 'ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM',
            'NETWORK': 'mainnet'
        }
        manager = EnhancedConfigManager('.env')
        manager.config = cfg_mainnet
        ok, errs = manager.validate_config()
        self.assertFalse(ok)
        self.assertIn('Invalid SYSTEM_ADDRESS format', errs)

        # Testnet must start with ST
        cfg_testnet = {
            'DEPLOYER_PRIVKEY': 'A' * 64,
            'SYSTEM_ADDRESS': 'SP2J1BCZK8Q0CP3W4R1XX9TMKJ1N1S8QZ7K0B5N8',
            'NETWORK': 'testnet'
        }
        manager = EnhancedConfigManager('.env')
        manager.config = cfg_testnet
        ok, errs = manager.validate_config()
        self.assertFalse(ok)
        self.assertIn('Invalid SYSTEM_ADDRESS format', errs)

    def test_invalid_characters_in_address(self):
        cfg = {
            'DEPLOYER_PRIVKEY': 'B' * 64,
            'SYSTEM_ADDRESS': 'ST1OQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM',  # contains O
            'NETWORK': 'testnet'
        }
        manager = EnhancedConfigManager('.env')
        manager.config = cfg
        ok, errs = manager.validate_config()
        self.assertFalse(ok)
        self.assertIn('Invalid SYSTEM_ADDRESS format', errs)


if __name__ == '__main__':
    unittest.main()

