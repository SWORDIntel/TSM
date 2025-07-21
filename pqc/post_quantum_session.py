import oqs
import json

class PostQuantumSession:
    """
    Establishes a post-quantum secure session using CRYSTALS-Kyber and CRYSTALS-Dilithium.
    """

    def __init__(self):
        self.kem = oqs.KeyEncapsulation("Kyber768")
        self.sig = oqs.Signature("Dilithium3")

        self.key_pair = self.sig.generate_keypair()
        self.public_key = self.key_pair["public_key"]

    def establish_session(self):
        """
        Generates ephemeral keys and produces a signed public key bundle.
        """
        ephemeral_key_pair = self.kem.generate_keypair()
        ephemeral_public_key = ephemeral_key_pair["public_key"]

        # Sign the ephemeral public key
        signature = self.sig.sign(ephemeral_public_key, self.key_pair["secret_key"])

        # Create the public key bundle
        public_key_bundle = {
            "ephemeral_public_key": ephemeral_public_key.hex(),
            "signature": signature.hex(),
            "verification_key": self.public_key.hex()
        }

        return json.dumps(public_key_bundle)

    def decrypt_shared_secret(self, ciphertext, ephemeral_key_pair):
        """
        Decrypts the shared secret using the ephemeral private key.
        """
        shared_secret = self.kem.decap_secret(ciphertext, ephemeral_key_pair["secret_key"])
        return shared_secret
