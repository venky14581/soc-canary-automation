import unittest
import os
import shutil
from app.generator import SyntheticFileGenerator
from app.engine import DeploymentEngine

class TestCanaryPlatform(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.getcwd(), "test_sandbox")
        os.makedirs(self.test_dir, exist_ok=True)
        self.engine = DeploymentEngine()

    def test_synthetic_generation_integrity(self):
        path = SyntheticFileGenerator.create_synthetic_file("Finance", self.test_dir)
        self.assertTrue(os.path.exists(path))
        self.assertGreater(os.path.getsize(path), 0)

    def test_local_deployment_and_hash_validation(self):
        source = SyntheticFileGenerator.create_synthetic_file("Engineering", self.test_dir)
        host_info = {
            "Hostname": "localhost",
            "IP Address": "127.0.0.1",
            "Deployment Method": "Local"
        }
        target_dest = os.path.join(self.test_dir, "deployed_out")
        
        result = self.engine.deploy_to_endpoint(host_info, source, target_dest)
        self.assertEqual(result["status"], "Success")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

if __name__ == "__main__":
    unittest.main()