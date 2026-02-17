import unittest
from stacksorbit_secrets import validate_private_key

class TestPKValidation(unittest.TestCase):
    def test_valid_pks(self):
        self.assertTrue(validate_private_key("a" * 64))
        self.assertTrue(validate_private_key("1" * 66))
        self.assertTrue(validate_private_key("ABCDEF" * 10 + "1234"))
        self.assertTrue(validate_private_key("0" * 64))

    def test_invalid_lengths(self):
        self.assertFalse(validate_private_key("a" * 63))
        self.assertFalse(validate_private_key("a" * 65))
        self.assertFalse(validate_private_key("a" * 67))
        self.assertFalse(validate_private_key(""))

    def test_invalid_chars(self):
        self.assertFalse(validate_private_key("a" * 63 + "g"))
        self.assertFalse(validate_private_key("a" * 63 + " "))
        self.assertFalse(validate_private_key("a" * 63 + "!"))
        self.assertFalse(validate_private_key("your_private_key_here"))

    def test_non_string(self):
        self.assertFalse(validate_private_key(None))
        self.assertFalse(validate_private_key(123))

if __name__ == "__main__":
    unittest.main()
