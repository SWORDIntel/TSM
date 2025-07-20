import os
import time
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

class TransportEncryption:
    """
    Provides encryption and decryption using ChaCha20-Poly1305 with rekeying.
    """
    REKEY_BYTES_THRESHOLD = 1024 * 1024 * 1024  # 1 GB
    REKEY_TIME_THRESHOLD = 300  # 5 minutes

    def __init__(self, initial_key):
        self._key = initial_key
        self._bytes_encrypted = 0
        self._last_rekey_time = time.time()
        self._aead = ChaCha20Poly1305(self._key)

    def _rekey(self):
        """
        Derives a new key using HKDF-SHA3-512.
        """
        hkdf = HKDF(
            algorithm=hashes.SHA3_512(),
            length=32,
            salt=None,
            info=b'rekeying',
        )
        self._key = hkdf.derive(self._key)
        self._aead = ChaCha20Poly1305(self._key)
        self._bytes_encrypted = 0
        self._last_rekey_time = time.time()

    def _should_rekey(self):
        """
        Checks if a rekey is needed based on bytes encrypted or time elapsed.
        """
        if self._bytes_encrypted >= self.REKEY_BYTES_THRESHOLD:
            return True
        if time.time() - self._last_rekey_time >= self.REKEY_TIME_THRESHOLD:
            return True
        return False

    def encrypt(self, plaintext, associated_data=None):
        """
        Encrypts the given plaintext.
        """
        if self._should_rekey():
            self._rekey()

        nonce = os.urandom(12)
        ciphertext = self._aead.encrypt(nonce, plaintext, associated_data)
        self._bytes_encrypted += len(ciphertext)
        return nonce + ciphertext

    def decrypt(self, ciphertext, associated_data=None):
        """
        Decrypts the given ciphertext.
        """
        nonce = ciphertext[:12]
        ciphertext = ciphertext[12:]
        return self._aead.decrypt(nonce, ciphertext, associated_data)
