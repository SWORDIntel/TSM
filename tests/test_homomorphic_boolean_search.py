import unittest
import pickle
import asyncio
import grpc

from homomorphic_search import HomomorphicSearchPrototype
from mock_server import TSMService_pb2, TSMService_pb2_grpc
from server_manager import ServerManager, TSMServerPresets

class TestHomomorphicBooleanSearch(unittest.TestCase):

    def test_placeholder(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
