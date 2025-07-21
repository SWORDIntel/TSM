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

@pytest.fixture
def test_db():
    db = Database(db_name=":memory:")
    db.create_tables()
    # Add mock data
    session_names = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"]
    for i, name in enumerate(session_names):
        session = TSMService_pb2.Session(
            id=f"session_{name.lower()}",
            name=f"Session {name}",
            created_timestamp=int(time.time()) - (86400 * (5 - i)),
            size_bytes=1024 * 1024 * (i + 1),
            is_encrypted=True,
            tags=["test", f"tag_{i}"]
        )
        with db:
            db.upsert_session(session)
    return db

def test_list_sessions_returns_correct_data(grpc_stub):
    # Call the ListSessions method
    request = TSMService_pb2.Empty()
    response = grpc_stub.ListSessions(request)

    # Assert that the response contains the correct number of sessions
    assert len(response.sessions) == 5

    # Assert that the properties of the first session match the mock data
    assert response.sessions[0].id == "session_alpha"
    assert response.sessions[0].name == "Session Alpha"
    assert response.sessions[0].is_encrypted is True
    assert "test" in response.sessions[0].tags
    assert "tag_0" in response.sessions[0].tags

def test_get_session_data_returns_decrypted_data(grpc_stub):
    # Call the GetSessionData method
    request = TSMService_pb2.GetSessionDataRequest(session_id="session_alpha")
    response = grpc_stub.GetSessionData(request)

    # Assert that the response contains the decrypted data
    assert response.decrypted_data

def test_ai_interceptor_denies_high_risk_request(grpc_stub, mocker):
    # Mock the AI analysis to return a high risk score
    mocker.patch(
        "mock_server.ai_interceptor.SessionSecurityAI.analyze_session",
        return_value=mocker.Mock(risk_score=0.95, threats=["High risk of compromise"]),
    )

    # Call a method that is intercepted by the AI security layer
    with pytest.raises(grpc.RpcError) as e:
        grpc_stub.GetSessionData(TSMService_pb2.GetSessionDataRequest(session_id="session_alpha"))

    # Assert that the request was denied
    assert e.value.code() == grpc.StatusCode.PERMISSION_DENIED
