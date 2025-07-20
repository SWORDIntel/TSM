import unittest
import sys
import os

# Add the pqc directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pqc.quantum_crypto import QuantumResistantCrypto

class TestQuantumResistantCrypto(unittest.TestCase):
    """
    Unit tests for the QuantumResistantCrypto class.
    """

    def test_initialization_default(self):
        """
        Tests that the class initializes with default settings.
        """
        crypto = QuantumResistantCrypto()
        self.assertTrue(crypto.hybrid_mode)

    def test_initialization_no_hybrid_mode(self):
        """
        Tests that the class initializes correctly with hybrid mode disabled.
        """
        crypto = QuantumResistantCrypto(hybrid_mode=False)
        self.assertFalse(crypto.hybrid_mode)

    def test_initialization_type_error(self):
        """
        Tests that a TypeError is raised for invalid hybrid_mode type.
        """
        with self.assertRaises(TypeError):
            QuantumResistantCrypto(hybrid_mode="not a boolean")

if __name__ == '__main__':
    unittest.main()
