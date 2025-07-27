import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server_manager import ServerManager, ServerConfig, HealthCheckType, TSMServerPresets

class TestServerManager(unittest.TestCase):

    def test_server_config_creation(self):
        """Test that ServerConfig objects can be created."""
        config = ServerConfig(
            name="test-server",
            command=["echo", "hello"],
            port=12345
        )
        self.assertEqual(config.name, "test-server")
        self.assertEqual(config.port, 12345)

    def test_server_manager_creation(self):
        """Test that ServerManager objects can be created."""
        manager = ServerManager()
        self.assertIsNotNone(manager)

    def test_presets(self):
        """Test TSMServerPresets"""
        grpc_config = TSMServerPresets.grpc_server()
        self.assertEqual(grpc_config.name, "tsm-grpc")
        self.assertEqual(grpc_config.port, 50051)
        self.assertEqual(grpc_config.health_check_type, HealthCheckType.GRPC)

if __name__ == '__main__':
    unittest.main(verbosity=2)
