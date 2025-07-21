import grpc
from concurrent import futures
import time
import pickle

import TSMService_pb2
import TSMService_pb2_grpc
from homomorphic_search import HomomorphicSearchPrototype
from phe import paillier

class TSMService(TSMService_pb2_grpc.TSMServiceServicer):
    """
    TSM gRPC Service Implementation
    
    This service handles encrypted session management using homomorphic encryption,
    allowing the server to perform searches on encrypted data without ever seeing
    the plaintext values. This is crucial for maintaining user privacy while still
    providing functionality.
    """
    
    def __init__(self):
        # Initialize the homomorphic search prototype
        # This creates the encryption keys and sets up the cryptographic framework
        self.search_prototype = HomomorphicSearchPrototype()
        
        # Create the sample database with meaningful session names
        # Using phonetic alphabet names makes debugging easier and reduces confusion
        # In production, these would be actual session identifiers from the database
        self.plain_database = {
            "session_alpha": 1,    # Value 1 encrypted
            "session_bravo": 2,    # Value 2 encrypted
            "session_charlie": 3,  # Value 3 encrypted
            "session_delta": 4,    # Value 4 encrypted
            "session_echo": 5      # Value 5 encrypted
        }
        
        # Generate the encrypted version of the database
        # Each value is encrypted using Paillier homomorphic encryption
        # This allows mathematical operations on encrypted data
        self.encrypted_database = self.search_prototype.generate_encrypted_database(
            self.plain_database
        )
        
        print(f"TSM Service initialized with {len(self.plain_database)} encrypted sessions")

    def ListSessions(self, request, context):
        """
        Lists all available sessions for a user.
        
        In a production system, this would query the actual database
        filtered by the user_id from the request.
        """
        sessions = []
        
        # Generate session metadata
        # In production, this would come from the database
        session_names = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"]
        
        for i in range(5):
            session = TSMService_pb2.Session(
                id=f"session_{session_names[i].lower()}",
                name=f"Session {session_names[i]}",
                creation_date=int(time.time()) - (86400 * (5 - i)),  # Stagger creation dates
                last_used_date=int(time.time()) - (3600 * (5 - i)),  # Stagger last used times
                size=1024 * 1024 * (i + 1),  # Varying sizes
                is_encrypted=True  # All sessions are encrypted in our system
            )
            sessions.append(session)
            
        return TSMService_pb2.ListSessionsResponse(sessions=sessions)

    def SwitchSession(self, request, context):
        """
        Switches the active session to the requested one.
        
        This would typically involve:
        1. Validating the user has access to the session
        2. Closing the current session
        3. Loading the new session
        4. Updating the last_used timestamp
        """
        # Validate that the session exists
        if not any(request.session_id in key for key in self.plain_database.keys()):
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
        # Extract the session identifier (e.g., "alpha" from "session_alpha")
        session_key = None
        for key in self.plain_database.keys():
            if request.session_id in key:
                session_key = key
                break
                
        if not session_key:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Session {request.session_id} not found")
            # Return an empty session with error indicators
            return TSMService_pb2.GetSessionDetailsResponse()
        
        # Create detailed session information
        session_suffix = session_key.split('_')[1].capitalize()
        
        session = TSMService_pb2.Session(
            id=request.session_id,
            name=f"Session {session_suffix}",
            creation_date=int(time.time()) - 86400,  # Created 24 hours ago
            last_used_date=int(time.time()) - 3600,  # Used 1 hour ago
            size=2 * 1024 * 1024,  # 2MB
            is_encrypted=True
        )
        
        return TSMService_pb2.GetSessionDetailsResponse(session=session)

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
            matching_key = self.search_prototype.execute_search(
                encrypted_query, 
                self.encrypted_database
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