import unittest
from zk_session_proof import ZKSessionProof

class TestZKSessionProof(unittest.TestCase):
    def test_generate_and_verify_proof(self):
        # 1. Create a ZKSessionProof object
        zk_session_proof = ZKSessionProof()

        # 2. Generate a proof for a known secret
        session_secret = "my_secret_password"
        H, proof = zk_session_proof.generate_proof(session_secret)

        # 3. Verify the proof
        self.assertTrue(zk_session_proof.verify_proof(H, proof))

if __name__ == '__main__':
    unittest.main()
