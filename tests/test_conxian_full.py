import unittest
import os
import sys
import shutil
import tempfile
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_conxian_deployment import EnhancedConxianDeployer, EnhancedConfigManager
from deployment_verifier import DeploymentVerifier

class TestConxianFullIntegration(unittest.TestCase):
    """Full integration tests for Conxian using Stacksorbit"""

    @classmethod
    def setUpClass(cls):
        # path to Conxian workspace
        cls.conxian_path = Path("c:/Users/bmokoka/anyachainlabs/Conxian")
        cls.stacksorbit_path = Path("c:/Users/bmokoka/anyachainlabs/stacksorbit")
        
        if not cls.conxian_path.exists():
            raise unittest.SkipTest("Conxian workspace not found at expected path")

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock .env for testing
        self.config_path = os.path.join(self.temp_dir, '.env')
        with open(self.config_path, 'w') as f:
            f.write("DEPLOYER_PRIVKEY=753b7cc01a1a2e86221266a154af739463fce51219d97e4f856cd7200c3bd2a601\n")
            f.write("SYSTEM_ADDRESS=ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM\n") # Testnet addr
            f.write("NETWORK=testnet\n")
            
        self.config_manager = EnhancedConfigManager(self.config_path)
        self.config = self.config_manager.load_config()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_01_verify_clarinet_toml(self):
        """Test that Conxian Clarinet.toml is valid and parseable"""
        clarinet_path = self.conxian_path / "Clarinet.toml"
        self.assertTrue(clarinet_path.exists(), "Clarinet.toml should exist in Conxian")
        
        with open(clarinet_path, 'r') as f:
            content = f.read()
            self.assertIn("[project]", content)
            self.assertIn("name = \"Conxian\"", content)
            
    def test_02_deployment_simulation(self):
        """Test deployment simulation (dry-run)"""
        # We need to temporarily mock the current working directory or adjust the deployer 
        # to accept a project path, but EnhancedConxianDeployer might depend on CWD.
        # Check if we can pass a path or if we need to chdir.
        
        # Saving CWD
        original_cwd = os.getcwd()
        try:
            os.chdir(self.conxian_path)
            
            deployer = EnhancedConxianDeployer(self.config, verbose=True)
            
            # Run pre-checks
            checks_passed = deployer.run_pre_checks()
            self.assertTrue(checks_passed, "Pre-deployment checks should pass")
            
            # Run dry-run deployment
            results = deployer.deploy_conxian(
                category=None, # Deploy all
                dry_run=True
            )
            
            self.assertTrue(results['success'], "Dry run should be successful")
            
        finally:
            os.chdir(original_cwd)

    def test_03_contract_verification(self):
        """Verify that expected contracts match Clarinet.toml"""
        
        # We'll use the DeploymentVerifier to check what it expects
        verifier = DeploymentVerifier(
            network='testnet',
            config=self.config
        )
        # Note: DeploymentVerifier.load_expected_contracts typically loads from a local file.
        # We might need to point it to Conxian's Clarinet.toml explicitly or ensure it uses it.
        
        # For this test, we verify that the verifier can at least init and validate structure
        # Assuming the verifier has logic to parse Clarinet.toml if we are in the dir
        
        original_cwd = os.getcwd()
        try:
            os.chdir(self.conxian_path)
             # Re-init verifier in the correct directory
            verifier = DeploymentVerifier(
                network='testnet',
                config=self.config
            )
            
            # It might fail if it can't find deployed contracts on chain (since we didn't deploy),
            # but we can check if it can load the expected contracts list correctly.
            
            # Using a private method or internal logic if available, otherwise just checking init
            # If load_expected_contracts is a standalone function in deployment_verifier.py:
            from deployment_verifier import load_expected_contracts
            expected = load_expected_contracts()
            self.assertTrue(len(expected) > 0, "Should find contracts in Clarinet.toml")
            self.assertIn("cxd-token", expected, "Should find cxd-token")
            
        finally:
            os.chdir(original_cwd)

if __name__ == '__main__':
    unittest.main()
