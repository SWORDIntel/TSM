import pytest
import grpc
import time
from concurrent import futures
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mock_server')))

import TSMService_pb2
import TSMService_pb2_grpc
from mock_server.server import TSMService
from mock_server.database import Database
import pickle

@pytest.fixture(scope="module")
def grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    TSMService_pb2_grpc.add_TSMServiceServicer_to_server(TSMService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    yield server
    server.stop(0)

@pytest.fixture(scope="module")
def grpc_stub(grpc_server):
    channel = grpc.insecure_channel('localhost:50051')
    return TSMService_pb2_grpc.TSMServiceStub(channel)

def test_graceful_crypto_failure(grpc_stub):
    """
    Tests that the server handles corrupted data gracefully.
    """
    # Get the service and corrupt a session's data
    service = TSMService()
    session_id = "session_alpha"
    original_data = service.db.get_session(session_id)["encrypted_data"]
    corrupted_data = b"corrupted_data"
    service.db.conn.execute(
        "UPDATE sessions SET encrypted_data = ? WHERE id = ?",
        (pickle.dumps(corrupted_data), session_id),
    )
    service.db.conn.commit()

    # Attempt to get the session data
    with pytest.raises(grpc.RpcError) as e:
        grpc_stub.GetSessionData(TSMService_pb2.GetSessionDataRequest(session_id=session_id))

    # Assert that the server returned an error
    assert e.value.code() == grpc.StatusCode.UNKNOWN

    # Restore the original data
    service.db.conn.execute(
        "UPDATE sessions SET encrypted_data = ? WHERE id = ?",
        (original_data, session_id),
    )
    service.db.conn.commit()

def test_ai_interceptor_allows_low_risk_request(grpc_stub, mocker):
    """
    Tests that the AI interceptor allows low-risk requests.
    """
    # Mock the AI analysis to return a low risk score
    mocker.patch(
        "mock_server.ai_interceptor.SessionSecurityAI.analyze_session",
        return_value=mocker.Mock(risk_score=0.1, threats=[]),
    )

    # Call a method that is intercepted by the AI security layer
    response = grpc_stub.GetSessionData(TSMService_pb2.GetSessionDataRequest(session_id="session_alpha"))

    # Assert that the request was successful
    assert response.decrypted_data
