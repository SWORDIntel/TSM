import unittest
import time
import grpc
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server_manager import ServerManager

class TestServerManager(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Create a minimal test server script"""
        cls.test_server_script = Path('test_server.py')
        
        # Create a minimal gRPC server for testing
        cls.test_server_script.write_text('''
import grpc
from concurrent import futures
import time
import sys

# Simple test service
class TestService:
    def Test(self, request, context):
        return request

def serve(port=50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"Test server started on port {port}", flush=True)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    port = 50051
    for i, arg in enumerate(sys.argv):
        if arg == '--port' and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
    serve(port)
''')
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test server script"""
        if cls.test_server_script.exists():
            cls.test_server_script.unlink()
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = None
        self.test_port = 50052  # Use different port to avoid conflicts
    
    def tearDown(self):
        """Clean up after each test"""
        if self.manager:
            self.manager.stop()
        
        # Clean up log files
        log_file = Path(f'server_{self.test_port}.log')
        if log_file.exists():
            log_file.unlink()
    
    def test_server_start_stop(self):
        """Test basic server start and stop"""
        self.manager = ServerManager(
            server_script=str(self.test_server_script),
            port=self.test_port,
            startup_timeout=10
        )
        
        # Start server
        self.manager.start()
        
        # Verify process is running
        self.assertIsNotNone(self.manager.process)
        self.assertIsNone(self.manager.process.poll())
        
        # Verify we can connect
        channel = grpc.insecure_channel(f'localhost:{self.test_port}')
        try:
            grpc.channel_ready_future(channel).result(timeout=2)
        except grpc.FutureTimeoutError:
            self.fail("Could not connect to started server")
        finally:
            channel.close()
        
        # Stop server
        self.manager.stop()
        
        # Verify process is stopped
        self.assertIsNone(self.manager.process)
    
    def test_server_already_running(self):
        """Test starting server when already running"""
        self.manager = ServerManager(
            server_script=str(self.test_server_script),
            port=self.test_port
        )
        
        # Start server
        self.manager.start()
        first_pid = self.manager.process.pid
        
        # Try to start again
        self.manager.start()
        
        # Should still be the same process
        self.assertEqual(self.manager.process.pid, first_pid)
    
    def test_server_script_not_found(self):
        """Test handling of missing server script"""
        with self.assertRaises(FileNotFoundError):
            ServerManager(server_script='nonexistent.py')
    
    def test_context_manager(self):
        """Test using ServerManager as context manager"""
        with ServerManager(
            server_script=str(self.test_server_script),
            port=self.test_port
        ) as manager:
            # Server should be running
            self.assertIsNotNone(manager.process)
            self.assertIsNone(manager.process.poll())
            
            # Can connect
            channel = grpc.insecure_channel(f'localhost:{self.test_port}')
            try:
                grpc.channel_ready_future(channel).result(timeout=2)
            except grpc.FutureTimeoutError:
                self.fail("Could not connect to server in context manager")
            finally:
                channel.close()
        
        # Server should be stopped after context
        self.assertIsNone(manager.process)
    
    def test_server_crash_during_startup(self):
        """Test handling of server crash during startup"""
        # Create a script that crashes immediately
        crash_script = Path('crash_server.py')
        crash_script.write_text('import sys; sys.exit(1)')
        
        try:
            manager = ServerManager(
                server_script=str(crash_script),
                port=self.test_port,
                startup_timeout=5
            )
            
            with self.assertRaises(RuntimeError) as cm:
                manager.start()
            
            self.assertIn("Server process died", str(cm.exception))
        
        finally:
            crash_script.unlink()
    
    def test_startup_timeout(self):
        """Test server startup timeout"""
        # Create a script that never opens the port
        slow_script = Path('slow_server.py')
        slow_script.write_text('import time; time.sleep(60)')
        
        try:
            manager = ServerManager(
                server_script=str(slow_script),
                port=self.test_port,
                startup_timeout=2  # Short timeout
            )
            
            with self.assertRaises(TimeoutError) as cm:
                manager.start()
            
            self.assertIn("failed to start within", str(cm.exception))
            
            # Clean up the slow process
            if manager.process:
                manager.stop()
        
        finally:
            slow_script.unlink()

if __name__ == '__main__':
    unittest.main(verbosity=2)
