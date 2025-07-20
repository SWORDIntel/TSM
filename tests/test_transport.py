import unittest
import os
import time
from transport.encryption import TransportEncryption
from transport.metadata import MetadataProtection

class TestTransportEncryption(unittest.TestCase):

    def test_encrypt_decrypt(self):
        initial_key = os.urandom(32)
        encryptor = TransportEncryption(initial_key)
        plaintext = b"test message"
        ciphertext = encryptor.encrypt(plaintext)
        decrypted_plaintext = encryptor.decrypt(ciphertext)
        self.assertEqual(plaintext, decrypted_plaintext)

    def test_rekey_on_bytes(self):
        initial_key = os.urandom(32)
        encryptor = TransportEncryption(initial_key)
        encryptor.REKEY_BYTES_THRESHOLD = 100
        plaintext = b"test message"
        # Encrypt enough to trigger rekey
        for _ in range(10):
            encryptor.encrypt(plaintext)
        # The key should have changed
        self.assertNotEqual(initial_key, encryptor._key)

    def test_rekey_on_time(self):
        initial_key = os.urandom(32)
        encryptor = TransportEncryption(initial_key)
        encryptor.REKEY_TIME_THRESHOLD = 0.1
        time.sleep(0.2)
        encryptor.encrypt(b"test")
        # The key should have changed
        self.assertNotEqual(initial_key, encryptor._key)

class TestMetadataProtection(unittest.TestCase):

    def test_padding(self):
        protector = MetadataProtection(lambda x: None)
        message = b"short message"
        padded_message = protector.prepare_message(message)
        self.assertIn(len(padded_message), protector.SIZE_BUCKETS)
        self.assertTrue(padded_message.startswith(message))

    def test_dummy_traffic(self):
        sent_messages = []
        def send_callback(message):
            sent_messages.append(message)

        protector = MetadataProtection(send_callback)
        protector.start()
        time.sleep(0.5)
        protector.stop()
        self.assertGreater(len(sent_messages), 0)

if __name__ == '__main__':
    unittest.main()
