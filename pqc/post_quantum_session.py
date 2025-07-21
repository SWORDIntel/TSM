import oqs

class PostQuantumSession:
    """
    Establishes a secure session using a post-quantum key-encapsulation mechanism (KEM).

    This class uses Kyber, a candidate in the NIST Post-Quantum Cryptography
    standardization process.
    """
    def __init__(self):
        self.kem = oqs.KeyEncapsulation("Kyber768")
        self.public_key, self.secret_key = self.kem.generate_keypair()
        self.shared_secret = None

    def get_public_key(self) -> bytes:
        """Returns the public key for the session."""
        return self.public_key

    def generate_shared_secret(self, remote_public_key: bytes) -> bytes:
        """
        Generates a shared secret using the remote public key.

        This is the client-side operation.
        """
        ciphertext, shared_secret = self.kem.encap_secret(remote_public_key)
        self.shared_secret = shared_secret
        return ciphertext

    def decrypt_shared_secret(self, ciphertext: bytes) -> None:
        """
        Decrypts the ciphertext to get the shared secret.

        This is the server-side operation.
        """
        self.shared_secret = self.kem.decap_secret(self.secret_key, ciphertext)
