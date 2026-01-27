import unittest
from unittest.mock import patch
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from deployment_verifier import DeploymentVerifier


class TestVerifierApiConnectivity(unittest.TestCase):
    @patch('deployment_verifier.DeploymentMonitor.check_api_status')
    @patch('deployment_verifier.DeploymentMonitor.get_account_info')
    @patch('deployment_verifier.DeploymentMonitor.get_deployed_contracts')
    def test_api_offline_marks_failure(self, mock_deployed, mock_account, mock_api):
        mock_api.return_value = {'status': 'offline', 'block_height': 0}
        mock_account.return_value = {'balance': '1000000', 'nonce': 0}
        mock_deployed.return_value = []

        verifier = DeploymentVerifier(network='testnet', config={'SYSTEM_ADDRESS': 'ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM'})
        results = verifier.run_comprehensive_verification([])
        self.assertEqual(results['overall_status'], 'failed')
        self.assertIn('API Connectivity', results['checks'])
        self.assertFalse(results['checks']['API Connectivity']['passed'])


if __name__ == '__main__':
    unittest.main()

