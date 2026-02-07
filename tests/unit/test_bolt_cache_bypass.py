import unittest
from unittest.mock import patch, MagicMock
import time
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from deployment_monitor import DeploymentMonitor

class TestBoltCacheBypass(unittest.TestCase):
    """Verify Bolt's cache bypass optimization."""

    def setUp(self):
        self.test_cache_path = "logs/test_bolt_cache.json"
        if os.path.exists(self.test_cache_path):
            os.remove(self.test_cache_path)

        self.monitor = DeploymentMonitor(network='testnet')
        self.monitor.cache_path = Path(self.test_cache_path)
        self.monitor.cache = {}
        self.monitor.cache_expiry = 300 # 5 minutes

    def tearDown(self):
        if os.path.exists(self.test_cache_path):
            os.remove(self.test_cache_path)

    @patch('requests.Session.get')
    def test_cache_bypass_logic(self, mock_get):
        """Verify that bypass_cache=True skips the cache and updates it."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_get.return_value = mock_response

        tx_id = "0x" + "a" * 64

        # 1. First call - should hit API
        self.monitor.get_transaction_info(tx_id)
        self.assertEqual(mock_get.call_count, 1)

        # 2. Second call without bypass - should hit CACHE
        self.monitor.get_transaction_info(tx_id)
        self.assertEqual(mock_get.call_count, 1) # Still 1

        # 3. Third call WITH bypass - should hit API
        self.monitor.get_transaction_info(tx_id, bypass_cache=True)
        self.assertEqual(mock_get.call_count, 2) # Incremented to 2

    @patch('requests.Session.get')
    def test_cache_bypass_updates_cache(self, mock_get):
        """Verify that a bypassed call updates the cache with new data."""
        tx_id = "0x" + "b" * 64

        # First API response
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {"status": "pending"}

        # Second API response
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"status": "success"}

        mock_get.side_effect = [mock_response1, mock_response2]

        # 1. Initial call - caches "pending"
        res1 = self.monitor.get_transaction_info(tx_id)
        self.assertEqual(res1['status'], "pending")

        # 2. Bypassed call - fetches "success" and updates cache
        res2 = self.monitor.get_transaction_info(tx_id, bypass_cache=True)
        self.assertEqual(res2['status'], "success")

        # 3. Subsequent call without bypass - should now get "success" from cache
        res3 = self.monitor.get_transaction_info(tx_id)
        self.assertEqual(res3['status'], "success")
        self.assertEqual(mock_get.call_count, 2)

if __name__ == '__main__':
    unittest.main()
