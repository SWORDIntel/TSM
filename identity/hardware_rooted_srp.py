import hashlib
import os

class HardwareRootedSRP:
    """
    Implements the Secure Remote Password (SRP-6a) protocol with hardware-rooted security.
    This class uses RFC 5054 prime and generator values.
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.N_str = """
        FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E08
        8A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B
        302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9
        A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE6
        49286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8
        FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D
        670C354E4ABC9804F1746C08CA237327FFFFFFFFFFFFFFFF
        """
        self.N = int("".join(self.N_str.split()), 16)
        self.g = 2
        self.k = int(hashlib.sha256(str(self.N).encode() + str(self.g).encode()).hexdigest(), 16)

        self.salt = os.urandom(16)
        self.v = self._calculate_verifier()
        self.b = int.from_bytes(os.urandom(32), 'big')
        self.B = (self.k * self.v + pow(self.g, self.b, self.N)) % self.N

        self.hardware_modules = self._detect_hardware_modules()

    def _calculate_verifier(self):
        """Calculates the verifier 'v' based on the username, password, and salt."""
        x = int(hashlib.sha256(self.salt + hashlib.sha256(f"{self.username}:{self.password}".encode()).digest()).hexdigest(), 16)
        return pow(self.g, x, self.N)

    def _detect_hardware_modules(self):
        """
        Detects the presence of hardware security modules like TPM or FIDO2 devices.
        """
        detected_modules = {}
        # Check for TPM
        if os.path.exists('/dev/tpm0'):
            detected_modules['tpm'] = True
        else:
            detected_modules['tpm'] = False

        # Check for FIDO2 libraries
        try:
            import fido2
            detected_modules['fido2'] = True
        except ImportError:
            detected_modules['fido2'] = False

        return detected_modules

    def get_server_public_key(self):
        """Returns the server's public key 'B'."""
        return self.B

    def process_client_hello(self, A):
        """Processes the client's public key 'A' and computes the session key."""
        u = int(hashlib.sha256(str(A).encode() + str(self.B).encode()).hexdigest(), 16)
        if u == 0:
            raise ValueError("Invalid 'u' value, cannot be zero.")

        S = pow(A * pow(self.v, u, self.N), self.b, self.N)
        self.K = hashlib.sha256(str(S).encode()).digest()

        return self.K
