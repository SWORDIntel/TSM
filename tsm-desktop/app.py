import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mock_server')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import grpc
import TSMService_pb2
import TSMService_pb2_grpc
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from yubikey import YubiKeyManager
from homomorphic_search import HomomorphicSearchPrototype
import pickle

class SessionList(Static):
    """A widget to display a list of sessions."""
    pass

class LogViewer(Static):
    """A widget to display logs."""
    pass

class StatusBar(Static):
    """A widget to display status information."""
    pass

class TSMDesktop(App):
    """A Textual app to manage Telegram sessions."""

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("s", "switch_session", "Switch Session"),
        ("i", "session_details", "Session Details"),
        ("f", "search_sessions", "Search Sessions"),
        ("p", "provision_yubikey", "Provision YubiKey"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield SessionList("Session List Placeholder")
        yield LogViewer("Log Viewer Placeholder")
        yield StatusBar("Status Bar Placeholder")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Initialize YubiKey manager for authentication
        self.yubikey_manager = YubiKeyManager()
        
        # Check if YubiKey is present and authenticate
        if self.yubikey_manager.detect_yubikey():
            if self.yubikey_manager.authenticate():
                # YubiKey authentication successful
                self.channel = grpc.insecure_channel('localhost:50051')
                self.stub = TSMService_pb2_grpc.TSMServiceStub(self.channel)
                self.list_sessions()
            else:
                # YubiKey detected but authentication failed
                self.query_one(SessionList).update("YubiKey authentication failed.")
                self.exit()
        else:
            # No YubiKey detected - fallback to password authentication
            # For prototype, we'll just connect without authentication
            self.channel = grpc.insecure_channel('localhost:50051')
            self.stub = TSMService_pb2_grpc.TSMServiceStub(self.channel)
            self.list_sessions()

    def list_sessions(self) -> None:
        """Fetch and display the list of available sessions."""
        request = TSMService_pb2.ListSessionsRequest(user_id="user1")
        try:
            response = self.stub.ListSessions(request)
            self.sessions = response.sessions
            
            # Format the session list for display
            session_list = "Sessions:\n"
            for i, session in enumerate(self.sessions):
                session_list += f"{i+1}. {session.name} ({session.id})\n"
            
            self.query_one(SessionList).update(session_list)
        except grpc.RpcError as e:
            self.query_one(SessionList).update(f"Error: {e.details()}")

    def action_switch_session(self) -> None:
        """Handle switching to a different session."""
        if self.sessions:
            # For the prototype, we switch to the first session
            # In production, this would show a selection dialog
            session_id = self.sessions[0].id
            request = TSMService_pb2.SwitchSessionRequest(session_id=session_id)
            try:
                response = self.stub.SwitchSession(request)
                self.query_one(StatusBar).update(response.message)
            except grpc.RpcError as e:
                self.query_one(StatusBar).update(f"Error: {e.details()}")

    def action_session_details(self) -> None:
        """Fetch and display detailed information about a session."""
        if self.sessions:
            # For the prototype, we show details of the first session
            # In production, this would use the currently selected session
            session_id = self.sessions[0].id
            request = TSMService_pb2.GetSessionDetailsRequest(session_id=session_id)
            try:
                response = self.stub.GetSessionDetails(request)
                
                # Format the session details for display
                details = f"Session Details:\n"
                details += f"ID: {response.session.id}\n"
                details += f"Name: {response.session.name}\n"
                details += f"Creation Date: {response.session.creation_date}\n"
                details += f"Last Used Date: {response.session.last_used_date}\n"
                details += f"Size: {response.session.size} bytes\n"
                details += f"Encrypted: {response.session.is_encrypted}\n"
                
                self.query_one(LogViewer).update(details)
            except grpc.RpcError as e:
                self.query_one(LogViewer).update(f"Error: {e.details()}")

    def action_provision_yubikey(self) -> None:
        """Set up YubiKey for authentication with this application."""
        if self.yubikey_manager.detect_yubikey():
            self.yubikey_manager.setup_challenge_response()
            self.query_one(StatusBar).update("YubiKey provisioned successfully.")
        else:
            self.query_one(StatusBar).update("No YubiKey detected.")

    def action_search_sessions(self) -> None:
        """Perform a homomorphic search for sessions matching a criteria."""
        # Initialize the search prototype
        search_prototype = HomomorphicSearchPrototype()
        
        # For the prototype, we use a hardcoded search term
        # In production, this would prompt the user for input
        search_term = 3
        
        # Generate an encrypted query using the search prototype
        # This uses the public key from the prototype instance
        encrypted_query = search_prototype.generate_encrypted_query(search_term)

        # Serialize the encrypted query for transmission
        # We need to include the public key, ciphertext, and exponent
        encrypted_query_p = {
            'pk': str(encrypted_query.public_key.n),  # Public key modulus
            'n': str(encrypted_query.ciphertext()),    # The encrypted value
            'e': str(encrypted_query.exponent)         # The exponent (for proper reconstruction)
        }

        # Create the gRPC request with the pickled encrypted query
        request = TSMService_pb2.EncryptedSearchRequest(
            encrypted_query=pickle.dumps(encrypted_query_p)
        )
        
        try:
            # Send the encrypted search request to the server
            response = self.stub.EncryptedSearch(request)
            
            # Display the results
            if response.session_locators:
                result_text = f"Search results (value={search_term}):\n"
                for locator in response.session_locators:
                    result_text += f"  - {locator}\n"
                self.query_one(LogViewer).update(result_text)
            else:
                self.query_one(LogViewer).update(
                    f"No sessions found matching value {search_term}."
                )
        except grpc.RpcError as e:
            self.query_one(LogViewer).update(f"Search error: {e.details()}")

    def action_toggle_dark(self) -> None:
        """Toggle between light and dark theme."""
        self.dark = not self.dark


class VirtualSessionContainer:
    """Manages Telegram sessions in isolated Docker containers for security."""

    def __init__(self, docker_client):
        """Initialize with a Docker client instance."""
        self.client = docker_client

    def build_image(self, dockerfile_path, image_tag):
        """Build a Docker image from a Dockerfile.
        
        Args:
            dockerfile_path: Path to the Dockerfile
            image_tag: Tag to assign to the built image
            
        Returns:
            The built Docker image object
        """
        with open(dockerfile_path, 'rb') as dockerfile:
            return self.client.images.build(
                fileobj=dockerfile, 
                tag=image_tag, 
                rm=True  # Remove intermediate containers
            )

    def run_container(self, image_tag, session_dir, proxy_server=None):
        """Launch a new container instance for a Telegram session.
        
        Args:
            image_tag: Docker image to use
            session_dir: Host directory containing session data
            proxy_server: Optional proxy server URL
            
        Returns:
            The running container object
        """
        environment = {}
        if proxy_server:
            # Configure proxy settings if provided
            environment['HTTP_PROXY'] = proxy_server
            environment['HTTPS_PROXY'] = proxy_server

        return self.client.containers.run(
            image_tag,
            volumes={
                # Mount the session directory with read/write access
                session_dir: {
                    'bind': '/home/tsmuser/session', 
                    'mode': 'rw'
                }
            },
            environment=environment,
            detach=True  # Run in background
        )

    def stop_container(self, container):
        """Gracefully stop a running container."""
        container.stop()

    def destroy_container(self, container):
        """Remove a stopped container and clean up resources."""
        container.remove()

    def get_logs(self, container):
        """Retrieve logs from a container for debugging.
        
        Returns:
            String containing the container logs
        """
        return container.logs().decode('utf-8')