import unittest
import os
import json
from secure_audit_logger import SecureAuditLogger

class TestSecureAuditLogger(unittest.TestCase):

    def setUp(self):
        self.log_file = "test_audit_log.json"
        self.logger = SecureAuditLogger(log_file_path=self.log_file)

    def tearDown(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def test_log_creation(self):
        self.logger.log("user1", "SESSION_LOGIN", "session1", "SUCCESS", "192.168.1.1")
        self.assertTrue(os.path.exists(self.log_file))

    def test_log_chaining(self):
        self.logger.log("user1", "SESSION_LOGIN", "session1", "SUCCESS", "192.168.1.1")
        with open(self.log_file, "r") as f:
            first_log_entry = json.loads(f.readline())

        self.logger.log("user2", "SESSION_LOGIN", "session2", "SUCCESS", "192.168.1.2")
        with open(self.log_file, "r") as f:
            lines = f.readlines()
            second_log_entry = json.loads(lines[1])

        import hashlib
        first_log_hash = hashlib.sha256(json.dumps(first_log_entry).encode()).hexdigest()
        # The hash is of the line, not the json object
        first_log_hash = hashlib.sha256((json.dumps(first_log_entry) + '\n').encode()).hexdigest()
        self.assertEqual(second_log_entry["previousEntryHash"], first_log_hash)

if __name__ == '__main__':
    unittest.main()
