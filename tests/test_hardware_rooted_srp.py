import unittest
from identity.hardware_rooted_srp import HardwareRootedSRP

class TestHardwareRootedSRP(unittest.TestCase):

    def test_srp_protocol(self):
        # Server side
        server = HardwareRootedSRP("testuser", "password123")
        B = server.get_server_public_key()

        # Client side
        a = 12345
        A = pow(server.g, a, server.N)

        # Server receives A and computes session key
        server_K = server.process_client_hello(A)

        # Client computes session key
        u = int(__import__('hashlib').sha256(str(A).encode() + str(B).encode()).hexdigest(), 16)
        x = int(__import__('hashlib').sha256(server.salt + __import__('hashlib').sha256(b"testuser:password123").digest()).hexdigest(), 16)
        S_client = pow(B - server.k * pow(server.g, x, server.N), a + u * x, server.N)
        client_K = __import__('hashlib').sha256(str(S_client).encode()).digest()

        self.assertEqual(server_K, client_K)

    def test_hardware_detection(self):
        server = HardwareRootedSRP("testuser", "password123")
        modules = server._detect_hardware_modules()
        self.assertIn('tpm', modules)
        self.assertIn('fido2', modules)

if __name__ == '__main__':
    unittest.main()
