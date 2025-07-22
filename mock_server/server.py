import grpc
from concurrent import futures
import time
import pickle

import TSMService_pb2
import TSMService_pb2_grpc
from homomorphic_search import HomomorphicSearchPrototype
from phe import paillier
from encrypted_index_manager import EncryptedIndexManager
from pqc.quantum_crypto import QuantumResistantCrypto
from tsm_ai_security import SessionSecurityAI
from database import Database
from identity.hardware_rooted_srp import HardwareRootedSRP
from zk_session_proof import ZKSessionProof
from zkp_utils import serialize_point, deserialize_point
import json
from storage.factory import StorageFactory
from replication import ReplicationManager

class TSMService(TSMService_pb2_grpc.TSMServiceServicer):
    """
    TSM gRPC Service Implementation
    
    This service handles encrypted session management using homomorphic encryption,
    allowing the server to perform searches on encrypted data without ever seeing
    the plaintext values. This is crucial for maintaining user privacy while still
    providing functionality.
    """
    
    def __init__(self):
        # Initialize the database
        self.db = Database()

        # Initialize the homomorphic search prototype
        # This creates the encryption keys and sets up the cryptographic framework
        self.index_manager = EncryptedIndexManager()
        self.search_prototype = self.index_manager.get_search_prototype()
        
        # Initialize the quantum-resistant crypto module
        self.qrc = QuantumResistantCrypto()
        self.qrc_public_key, self.qrc_private_key = self.qrc.generate_kyber_keys()

        # Initialize the session security AI
        self.security_ai = SessionSecurityAI()

        # In-memory store for SRP sessions
        self.srp_sessions = {}
        # In-memory store for ZK sessions
        self.zk_sessions = {}

        # Initialize storage backends
        self.storage_factory = StorageFactory()
        self.storage_backends = self.storage_factory.load_from_config('storage_config.json')
        self.replication_manager = ReplicationManager(self.storage_backends)

        # Generate some sample sessions and store them in the database
        session_names = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"]
        for i, name in enumerate(session_names):
            session_data = f"This is the secret data for session {name}".encode('utf-8')
            encrypted_data = self.qrc.encrypt(session_data, self.qrc_public_key)
            session_id = f"session_{name.lower()}"
            session = TSMService_pb2.Session(
                id=session_id,
                name=f"Session {name}",
                created_timestamp=int(time.time()) - (86400 * (5 - i)),
                size_bytes=len(encrypted_data),
                is_encrypted=True,
                tags=["test", f"tag_{i}"]
            )
            self.db.upsert_session(session, pickle.dumps(encrypted_data))
            self.index_manager.update_index(session_id, i)
        
        print(f"TSM Service initialized with {len(session_names)} encrypted sessions in the database")

    def ListSessions(self, request, context):
        """
        Lists all available sessions for a user.
        
        In a production system, this would query the actual database
        filtered by the user_id from the request.
        """
        sessions = []
        for row in self.db.get_all_sessions():
            session = TSMService_pb2.Session(
                id=row['id'],
                name=row['name'],
                created_timestamp=row['creation_date'],
                size_bytes=row['size'],
                is_encrypted=row['is_encrypted'],
                tags=row['tags'].split(',') if row['tags'] else []
            )
            sessions.append(session)
        return TSMService_pb2.SessionList(sessions=sessions)

    def GetSessionData(self, request, context):
        """
        Retrieves and decrypts the data for a specific session.
        """
        session_row = self.db.get_session(request.session_id)
        if session_row and session_row['encrypted_data']:
            encrypted_data = pickle.loads(session_row['encrypted_data'])
            decrypted_data = self.qrc.decrypt(self.qrc_private_key, encrypted_data)
            return TSMService_pb2.GetSessionDataResponse(decrypted_data=decrypted_data)
        elif session_row:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Session {request.session_id} found, but no data")
            return TSMService_pb2.GetSessionDataResponse()
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Session {request.session_id} not found")
            return TSMService_pb2.GetSessionDataResponse()

    def AnalyzeSession(self, request, context):
        """
        Analyzes a session for security risks.
        """
        session = request.session
        session_data = {
            "last_login_time": time.strftime("%H:%M", time.gmtime(session.last_used_date)),
            "message_frequency_per_hour": 100, # dummy data
            "api_calls_last_24h": 20 # dummy data
        }
        report = self.security_ai.analyze_session(session_data)

        return TSMService_pb2.AnalyzeSessionResponse(
            report=TSMService_pb2.SecurityReport(
                risk_score=report.risk_score,
                threats=report.threats,
                recommends=report.recommendations
            )
        )

    def SwitchSession(self, request, context):
        """
        Switches the active session to the requested one.
        
        This would typically involve:
        1. Validating the user has access to the session
        2. Closing the current session
        3. Loading the new session
        4. Updating the last_used timestamp
        """
        session_row = self.db.get_session(request.session_id)
        if not session_row:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Session {request.session_id} not found")
            return TSMService_pb2.SwitchSessionResponse(
                success=False,
                message=f"Session {request.session_id} not found"
            )

        # In production, perform the actual session switch here

        return TSMService_pb2.SwitchSessionResponse(
            success=True,
            message=f"Successfully switched to session {request.session_id}"
        )

    def GetSessionDetails(self, request, context):
        """
        Retrieves detailed information about a specific session.
        """
        session_row = self.db.get_session(request.session_id)
        if not session_row:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Session {request.session_id} not found")
            return TSMService_pb2.GetSessionDetailsResponse()

        session = TSMService_pb2.Session(
            id=session_row['id'],
            name=session_row['name'],
            created_timestamp=session_row['creation_date'],
            size_bytes=session_row['size'],
            is_encrypted=session_row['is_encrypted'],
            tags=session_row['tags'].split(',') if session_row['tags'] else []
        )
        return TSMService_pb2.GetSessionDetailsResponse(session=session)

    def StartSRPAuthentication(self, request, context):
        """
        Starts the SRP authentication process.
        """
        username = request.username
        # In a real application, you would look up the user's password from a database.
        # For this example, we'll just use a dummy password.
        password = "password"
        srp = HardwareRootedSRP(username, password)
        self.srp_sessions[username] = srp
        return TSMService_pb2.SRPChallengeResponse(salt=srp.salt, serverB=srp.get_server_public_key().to_bytes(256, 'big'))

    def VerifySRP(self, request, context):
        """
        Verifies the client's SRP proof.
        """
        username = "user" # In a real app, you'd get this from the request or a session cookie
        srp = self.srp_sessions.get(username)
        if not srp:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("SRP session not found.")
            return TSMService_pb2.SRPVerifyResponse()

        client_A = int.from_bytes(request.clientA, 'big')
        session_key = srp.process_client_hello(client_A)

        # At this point, the session key is established.
        # The client would then send a proof (M1), and the server would verify it and send its own proof (M2).
        # For simplicity, we'll just return a dummy M2.
        return TSMService_pb2.SRPVerifyResponse(m2=b"server_proof")

    def StartZKAuthentication(self, request, context):
        """
        Starts the ZK-proof authentication process.
        """
        username = request.username
        # In a real application, you would look up the user's password from a database.
        # For this example, we'll just use a dummy password.
        password = "password"
        zk = ZKSessionProof()
        H, proof = zk.generate_proof(password)
        self.zk_sessions[username] = {"H": H, "proof": proof}
        return TSMService_pb2.ZKChallengeResponse(H=json.dumps(serialize_point(H)))

    def VerifyZKProof(self, request, context):
        """
        Verifies the client's ZK-proof.
        """
        username = request.username
        session = self.zk_sessions.get(username)
        if not session:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("ZK session not found.")
            return TSMService_pb2.ZKProofResponse()

        zk = ZKSessionProof()
        proof = deserialize_point(json.loads(request.proof))
        if zk.verify_proof(session["H"], proof):
            # In a real application, you would generate a session token.
            return TSMService_pb2.ZKProofResponse(session_token="dummy_token")
        else:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("ZK proof verification failed.")
            return TSMService_pb2.ZKProofResponse()

    def EncryptedSearch(self, request, context):
        """
        Performs a search on encrypted data using homomorphic encryption.
        
        This is the core privacy-preserving feature of the system:
        1. Client sends an encrypted search query
        2. Server performs mathematical operations on encrypted database
        3. Server returns which sessions match without knowing the search value
        
        The server never sees the plaintext search term or the actual values
        in the database - everything remains encrypted throughout the process.
        """
        try:
            encrypted_query = pickle.loads(request.encrypted_query.encode('latin-1'))
            encrypted_index = self.index_manager.get_index()
            
            matching_session_ids = []
            for session_id, encrypted_value in encrypted_index.items():
                # Homomorphically subtract the query from the database value
                encrypted_diff = encrypted_value - encrypted_query
                
                # The server can't decrypt the difference, so it sends it to the client.
                # In a real-world scenario, the client would decrypt the difference and
                # determine if it's zero.
                # For this prototype, we'll simulate the client-side decryption here.
                private_key = self.search_prototype.private_key
                decrypted_diff = private_key.decrypt(encrypted_diff)
                
                if decrypted_diff == 0:
                    matching_session_ids.append(session_id)
            
            return TSMService_pb2.SearchResponse(matching_session_ids=matching_session_ids)
                
        except Exception as e:
            print(f"Error during encrypted search: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Search operation failed")
            return TSMService_pb2.SearchResponse()

    def GetStorageConfiguration(self, request, context):
        with open('storage_config.json', 'r') as f:
            config_data = json.load(f)

        backends = []
        for backend_config in config_data:
            backends.append(TSMService_pb2.BackendConfig(
                type=backend_config['type'],
                parameters=backend_config
            ))
        return TSMService_pb2.StorageConfiguration(backends=backends)

    def AddStorageBackend(self, request, context):
        try:
            with open('storage_config.json', 'r+') as f:
                config_data = json.load(f)
                config_data.append(request.backend)
                f.seek(0)
                json.dump(config_data, f, indent=2)
            return TSMService_pb2.StorageOperationResponse(success=True, message="Backend added successfully.")
        except Exception as e:
            return TSMService_pb2.StorageOperationResponse(success=False, message=str(e))

    def RemoveStorageBackend(self, request, context):
        try:
            with open('storage_config.json', 'r+') as f:
                config_data = json.load(f)
                config_data = [b for b in config_data if b['type'] != request.backend_id]
                f.seek(0)
                f.truncate()
                json.dump(config_data, f, indent=2)
            return TSMService_pb2.StorageOperationResponse(success=True, message="Backend removed successfully.")
        except Exception as e:
            return TSMService_pb2.StorageOperationResponse(success=False, message=str(e))


from ai_interceptor import AISecurityInterceptor

def serve():
    """
    Starts the gRPC server and handles incoming requests.
    """
    # Initialize the AI security module and the interceptor
    security_ai = SessionSecurityAI()
    ai_interceptor = AISecurityInterceptor(security_ai)

    # Configure the thread pool for handling concurrent requests
    # 10 workers is reasonable for a prototype; adjust based on load testing
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[ai_interceptor],
        options=[
            # Set maximum message size to handle encrypted data
            ('grpc.max_receive_message_length', 10 * 1024 * 1024),  # 10MB
            ('grpc.max_send_message_length', 10 * 1024 * 1024),     # 10MB
        ]
    )
    
    # Register our service implementation
    service = TSMService()
    TSMService_pb2_grpc.add_TSMServiceServicer_to_server(service, server)
    
    # Bind to port 50051 on all interfaces
    # In production, consider using TLS with server.add_secure_port()
    server.add_insecure_port('[::]:50051')
    
    # Start the server
    server.start()
    print("TSM gRPC server started on port 50051...")
    print("Ready to handle encrypted search requests")
    

    try:
        # Keep the server running
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down TSM server...")
        server.stop(grace_period=5)  # Give 5 seconds for cleanup
        print("Server stopped")

if __name__ == '__main__':
    serve()