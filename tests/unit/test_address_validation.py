import unittest
from stacksorbit_secrets import validate_stacks_address

class TestAddressValidation(unittest.TestCase):
    def test_valid_testnet_address(self):
        # Valid ST address (41 chars, C32 charset)
        addr = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        self.assertTrue(validate_stacks_address(addr, "testnet"))
        self.assertTrue(validate_stacks_address(addr, "devnet"))
        # Should fail for mainnet
        self.assertFalse(validate_stacks_address(addr, "mainnet"))

    def test_valid_mainnet_address(self):
        # Valid SP address
        addr = "SP2J1BC9A5ZDM2DHF01N000000000000000000000"
        self.assertTrue(validate_stacks_address(addr, "mainnet"))
        # Should fail for testnet
        self.assertFalse(validate_stacks_address(addr, "testnet"))

    def test_invalid_length(self):
        addr = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZG" # 40 chars
        self.assertFalse(validate_stacks_address(addr))

        addr = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGMA" # 42 chars
        self.assertFalse(validate_stacks_address(addr))

    def test_invalid_charset(self):
        # I, L, O, U are not allowed in C32
        addr = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGI" # Ends with I
        self.assertFalse(validate_stacks_address(addr))

        addr = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGL" # Ends with L
        self.assertFalse(validate_stacks_address(addr))

    def test_invalid_prefix(self):
        addr = "SN1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM" # SN prefix
        self.assertFalse(validate_stacks_address(addr))

    def test_lowercase_conversion(self):
        # Should be case-insensitive
        addr = "st1pqhqkv0rjxzfy1dgx8mnsnyve3vgzjsrtpgzgm"
        self.assertTrue(validate_stacks_address(addr, "testnet"))

    def test_none_or_empty(self):
        self.assertFalse(validate_stacks_address(None))
        self.assertFalse(validate_stacks_address(""))

if __name__ == "__main__":
    unittest.main()
