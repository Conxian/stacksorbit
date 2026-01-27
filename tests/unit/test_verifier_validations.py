import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from deployment_verifier import DeploymentVerifier


class TestVerifierValidations(unittest.TestCase):
    def test_missing_address_raises(self):
        verifier = DeploymentVerifier(network='testnet', config={})
        with self.assertRaises(ValueError):
            verifier.run_comprehensive_verification([])


if __name__ == '__main__':
    unittest.main()

