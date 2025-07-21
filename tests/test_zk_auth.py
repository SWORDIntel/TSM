import unittest
import grpc
from concurrent import futures
import time
import os
import sys
import json

# Configure the Python path to find our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mock_server')))

import TSMService_pb2
import TSMService_pb2_grpc
from mock_server.server import TSMService
from zk_session_proof import ZKSessionProof
from zkp_utils import serialize_point, deserialize_point

class ZKAuthTest(unittest.TestCase):
    def setUp(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        TSMService_pb2_grpc.add_TSMServiceServicer_to_server(TSMService(), self.server)
        self.server.add_insecure_port('[::]:50051')
        self.server.start()
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = TSMService_pb2_grpc.TSMServiceStub(self.channel)

    def tearDown(self):
        self.server.stop(0)

    def test_zk_auth_flow(self):
        # 1. Start the authentication process
        start_request = TSMService_pb2.ZKAuthenticationRequest(username="testuser")
        start_response = self.stub.StartZKAuthentication(start_request)
        self.assertIsNotNone(start_response.H)
        H = deserialize_point(json.loads(start_response.H))

        # 2. Generate the proof
        zk = ZKSessionProof()
        _, proof = zk.generate_proof("password")

        # 3. Verify the proof
        verify_request = TSMService_pb2.ZKProofRequest(username="testuser", proof=json.dumps(serialize_point(proof)))
        verify_response = self.stub.VerifyZKProof(verify_request)
        self.assertEqual(verify_response.session_token, "dummy_token")

if __name__ == '__main__':
    unittest.main()
