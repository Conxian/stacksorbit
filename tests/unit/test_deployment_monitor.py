import unittest
from unittest.mock import patch, MagicMock
import time
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from deployment_monitor import DeploymentMonitor

class TestDeploymentMonitorCache(unittest.TestCase):
    """Tests for the caching functionality in DeploymentMonitor."""

    def setUp(self):
        """Set up a DeploymentMonitor instance for testing."""
        self.monitor = DeploymentMonitor(network='testnet', config={'LOG_LEVEL': 'DEBUG'})
        # Lower the expiry for faster testing
        self.monitor.cache_expiry = 2

    @patch('requests.Session.get')
    def test_get_recent_transactions_caching(self, mock_get):
        """Verify that get_recent_transactions caches results."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"tx_id": "0x123"}]}
        mock_get.return_value = mock_response

        address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"

        # --- First call (should hit API) ---
        result1 = self.monitor.get_recent_transactions(address)
        self.assertEqual(len(result1), 1)
        self.assertEqual(result1[0]['tx_id'], "0x123")
        mock_get.assert_called_once()

        # --- Second call (should be cached) ---
        result2 = self.monitor.get_recent_transactions(address)
        self.assertEqual(len(result2), 1)
        # The mock should still have been called only once
        mock_get.assert_called_once()

        # --- Wait for cache to expire ---
        time.sleep(self.monitor.cache_expiry + 0.1)

        # --- Third call (should hit API again) ---
        result3 = self.monitor.get_recent_transactions(address)
        self.assertEqual(len(result3), 1)
        # The mock should now have been called a second time
        self.assertEqual(mock_get.call_count, 2)

if __name__ == '__main__':
    unittest.main()
