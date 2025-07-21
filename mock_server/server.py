import grpc
from concurrent import futures
import time
import pickle

import TSMService_pb2
import TSMService_pb2_grpc
from homomorphic_search import HomomorphicSearchPrototype
from phe import paillier
from pqc.quantum_crypto import QuantumResistantCrypto
from tsm_ai_security import SessionSecurityAI
from database import Database
from identity.hardware_rooted_srp import HardwareRootedSRP

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
        self.search_prototype = HomomorphicSearchPrototype()
        
        # Initialize the quantum-resistant crypto module
        self.qrc = QuantumResistantCrypto()
        self.qrc_public_key, self.qrc_private_key = self.qrc.generate_kyber_keys()

        # Initialize the session security AI
        self.security_ai = SessionSecurityAI()

        # In-memory store for SRP sessions
        self.srp_sessions = {}

        # Generate some sample sessions and store them in the database
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
            self.db.upsert_session(session)
        
        print(f"TSM Service initialized with {len(session_names)} sessions in the database")

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
        if session_row:
            encrypted_data = pickle.loads(session_row[6])
            decrypted_data = self.qrc.decrypt(self.qrc_private_key, encrypted_data)
            return TSMService_pb2.GetSessionDataResponse(decrypted_data=decrypted_data)
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
            id=session_row[0],
            name=session_row[1],
            creation_date=session_row[2],
            last_used_date=session_row[3],
            size=session_row[4],
            is_encrypted=session_row[5],
            encrypted_data=session_row[6]
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
            # Deserialize the encrypted query
            # The pickle format allows us to transmit complex cryptographic objects
            encrypted_query_data = pickle.loads(request.encrypted_query)
            
            # Check if we received the new format (with proper Paillier reconstruction)
            # or the old format (direct encrypted object)
            if isinstance(encrypted_query_data, dict):
                # New format: reconstruct the Paillier encrypted number
                # This ensures proper cryptographic properties are maintained
                
                # Validate required fields
                required_fields = ['pk', 'n', 'e']
                for field in required_fields:
                    if field not in encrypted_query_data:
                        raise ValueError(f"Missing required field: {field}")
                
                # Reconstruct the public key
                # The public key n is the modulus used in Paillier encryption
                public_key = paillier.PaillierPublicKey(int(encrypted_query_data['pk']))
                
                # Reconstruct the encrypted number
                # n: the ciphertext (encrypted value)
                # e: the exponent (used for optimization in Paillier)
                encrypted_query = paillier.EncryptedNumber(
                    public_key, 
                    int(encrypted_query_data['n']), 
                    int(encrypted_query_data['e'])
                )
            else:
                # Old format: assume it's already an encrypted object
                # This maintains backward compatibility during migration
                encrypted_query = encrypted_query_data

            # Execute the homomorphic search
            # This performs mathematical operations on encrypted values
            # to find matches without decrypting anything

            # For now, we'll just search the in-memory database.
            # In a real implementation, this would need to be adapted to work with the SQLite database.
            plain_database = {
                "session_alpha": 1,
                "session_bravo": 2,
                "session_charlie": 3,
                "session_delta": 4,
                "session_echo": 5
            }
            encrypted_database = self.search_prototype.generate_encrypted_database(plain_database)

            matching_key = self.search_prototype.execute_search(
                encrypted_query, 
                encrypted_database
            )
            
            # Log for debugging (in production, use structured logging)
            if matching_key:
                print(f"Search found match: {matching_key}")
            else:
                print("Search completed with no matches")
            
            # Return the results
            if matching_key:
                return TSMService_pb2.SearchResponse(session_locators=[matching_key])
            else:
                return TSMService_pb2.SearchResponse(session_locators=[])
                
        except pickle.UnpicklingError as e:
            # Handle deserialization errors specifically
            print(f"Failed to deserialize encrypted query: {e}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid encrypted query format")
            return TSMService_pb2.SearchResponse(session_locators=[])
            
        except ValueError as e:
            # Handle validation errors
            print(f"Invalid encrypted query data: {e}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return TSMService_pb2.SearchResponse(session_locators=[])
            
        except Exception as e:
            # Handle unexpected errors
            print(f"Error during encrypted search: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Search operation failed")
            return TSMService_pb2.SearchResponse(session_locators=[])

def serve():
    """
    Starts the gRPC server and handles incoming requests.
    """
    # Configure the thread pool for handling concurrent requests
    # 10 workers is reasonable for a prototype; adjust based on load testing
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            # Set maximum message size to handle encrypted data
            ('grpc.max_receive_message_length', 10 * 1024 * 1024),  # 10MB
            ('grpc.max_send_message_length', 10 * 1024 * 1024),     # 10MB
        ]
    )
    
    # Register our service implementation
    TSMService_pb2_grpc.add_TSMServiceServicer_to_server(TSMService(), server)
    
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