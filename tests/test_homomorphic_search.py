import unittest
import sys
import os
import logging
logging.basicConfig(level=logging.INFO)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mock_server')))
from homomorphic_search import HomomorphicSearchPrototype
from mock_server.encrypted_index_manager import EncryptedIndexManager
import TSMService_pb2

class TestBooleanHomomorphicSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.info("Setting up test class...")
        cls.engine = HomomorphicSearchPrototype()
        cls.index_manager = EncryptedIndexManager(search_prototype=cls.engine)
        cls._setup_test_data()

    @classmethod
    def _setup_test_data(cls):
        logging.info("Setting up test data...")
        cls.index_manager.update_index("session_1", ["project", "alpha", "secure"])
        cls.index_manager.update_index("session_2", ["bravo", "test"])
        cls.index_manager.update_index("session_3", ["gamma", "project"])

    def test_boolean_and_search_success(self):
        """Test AND search with matching session"""
        logging.info("Testing boolean AND search success...")
        # Session contains both "project" and "alpha"
        encrypted_terms = [
            self.engine.generate_encrypted_query(self.engine.public_key.encrypt(hash("project"))),
            self.engine.generate_encrypted_query(self.engine.public_key.encrypt(hash("alpha")))
        ]

        results, _ = self.index_manager.search_boolean(
            encrypted_terms,
            TSMService_pb2.EncryptedSearchRequest.AND
        )

        self.assertIn("session_1", results)
        self.assertEqual(len(results), 1)

    def test_boolean_and_search_failure(self):
        """Test AND search with non-matching sessions"""
        logging.info("Testing boolean AND search failure...")
        # No session contains both terms
        encrypted_terms = [
            self.engine.generate_encrypted_query(self.engine.public_key.encrypt(hash("project"))),
            self.engine.generate_encrypted_query(self.engine.public_key.encrypt(hash("zebra")))
        ]

        results, _ = self.index_manager.search_boolean(
            encrypted_terms,
            TSMService_pb2.EncryptedSearchRequest.AND
        )

        self.assertEqual(len(results), 0)

    def test_boolean_or_search_success(self):
        """Test OR search across multiple sessions"""
        logging.info("Testing boolean OR search success...")
        # "project" in session_1, "bravo" in session_2
        encrypted_terms = [
            self.engine.generate_encrypted_query(self.engine.public_key.encrypt(hash("project"))),
            self.engine.generate_encrypted_query(self.engine.public_key.encrypt(hash("bravo")))
        ]

        results, _ = self.index_manager.search_boolean(
            encrypted_terms,
            TSMService_pb2.EncryptedSearchRequest.OR
        )

        self.assertIn("session_1", results)
        self.assertIn("session_2", results)
        self.assertEqual(len(results), 2)

if __name__ == '__main__':
    unittest.main()
