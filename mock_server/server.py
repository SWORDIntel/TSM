import grpc
from concurrent import futures
import time

import TSMService_pb2
import TSMService_pb2_grpc

class TSMService(TSMService_pb2_grpc.TSMServiceServicer):
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

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    TSMService_pb2_grpc.add_TSMServiceServicer_to_server(TSMService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
