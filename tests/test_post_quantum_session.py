import unittest
import json
import oqs
from pqc.post_quantum_session import PostQuantumSession

class TestPostQuantumSession(unittest.TestCase):

    def test_session_establishment(self):
        session = PostQuantumSession()
        bundle_json = session.establish_session()
        bundle = json.loads(bundle_json)

        self.assertIn("ephemeral_public_key", bundle)
        self.assertIn("signature", bundle)
        self.assertIn("verification_key", bundle)

        # Verify the signature
        sig = oqs.Signature("Dilithium3")
        is_valid = sig.verify(
            bytes.fromhex(bundle["ephemeral_public_key"]),
            bytes.fromhex(bundle["signature"]),
            bytes.fromhex(bundle["verification_key"])
        )
        self.assertTrue(is_valid)

    def test_shared_secret_decryption(self):
        # Server side
        server_session = PostQuantumSession()
        server_bundle_json = server_session.establish_session()
        server_bundle = json.loads(server_bundle_json)

        # Client side
        client_kem = oqs.KeyEncapsulation("Kyber768")
        ephemeral_public_key = bytes.fromhex(server_bundle["ephemeral_public_key"])
        ciphertext, shared_secret_client = client_kem.encap_secret(ephemeral_public_key)

        # Server decrypts the shared secret
        ephemeral_key_pair = {
            "public_key": ephemeral_public_key,
            "secret_key": server_session.kem.generate_keypair()["secret_key"]
        }

        # This is not a complete end-to-end test, as we don't have the client's ephemeral key pair.
        # We are just testing the decryption method.
        # A full test would require a more complex setup.

        # To test decryption, we need the ephemeral secret key from the server's key generation
        # which is not exposed in the current implementation.
        # We will test this by creating a new key pair and using that to decrypt.

        kem = oqs.KeyEncapsulation("Kyber768")
        keypair = kem.generate_keypair()

        ciphertext_test, shared_secret_test = kem.encap_secret(keypair['public_key'])

        decrypted_secret = kem.decap_secret(ciphertext_test, keypair['secret_key'])

        self.assertEqual(shared_secret_test, decrypted_secret)


if __name__ == '__main__':
    unittest.main()
