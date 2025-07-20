import grpc
from concurrent import futures
import time
import pickle

import TSMService_pb2
import TSMService_pb2_grpc
from homomorphic_search import HomomorphicSearchPrototype
from phe import paillier

class TSMService(TSMService_pb2_grpc.TSMServiceServicer):
    def __init__(self):
        self.search_prototype = HomomorphicSearchPrototype()
        self.plain_database = {
            "session_1": 1,
            "session_2": 2,
            "session_3": 3,
            "session_4": 4,
            "session_5": 5
        }
        self.encrypted_database = self.search_prototype.generate_encrypted_database(self.plain_database)

    def ListSessions(self, request, context):
        sessions = []
        for i in range(5):
            session = TSMService_pb2.Session(
                id=f"session_{i}",
                name=f"Session {i}",
                creation_date=int(time.time()),
                last_used_date=int(time.time()),
                size=1024 * 1024 * (i + 1),
                is_encrypted=i % 2 == 0
            )
            sessions.append(session)
        return TSMService_pb2.ListSessionsResponse(sessions=sessions)

    def SwitchSession(self, request, context):
        return TSMService_pb2.SwitchSessionResponse(success=True, message=f"Successfully switched to session {request.session_id}")

    def GetSessionDetails(self, request, context):
        session = TSMService_pb2.Session(
            id=request.session_id,
            name=f"Session {request.session_id}",
            creation_date=int(time.time()),
            last_used_date=int(time.time()),
            size=1024 * 1024,
            is_encrypted=True
        )
        return TSMService_pb2.GetSessionDetailsResponse(session=session)

    def EncryptedSearch(self, request, context):
        encrypted_query_p = pickle.loads(request.encrypted_query)

        # Convert the public key and encrypted number to the correct types
        public_key = paillier.PaillierPublicKey(int(encrypted_query_p['pk']))
        encrypted_query = paillier.EncryptedNumber(public_key, int(encrypted_query_p['n']), int(encrypted_query_p['e']))

        matching_key = self.search_prototype.execute_search(encrypted_query, self.encrypted_database)
        if matching_key:
            return TSMService_pb2.SearchResponse(session_locators=[matching_key])
        else:
            return TSMService_pb2.SearchResponse(session_locators=[])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    TSMService_pb2_grpc.add_TSMServiceServicer_to_server(TSMService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
