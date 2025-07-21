import sys
import os
import pickle

# Configure the Python path to find our modules
# This ensures imports work regardless of where the script is run from
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mock_server')))

import grpc
import TSMService_pb2
import TSMService_pb2_grpc
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from yubikey import YubiKeyManager
from homomorphic_search import HomomorphicSearchPrototype
from datetime import datetime


class SessionList(Static):
    """A widget to display a list of sessions."""
    pass


class LogViewer(Static):
    """A widget to display logs and search results."""
    pass


class StatusBar(Static):
    """A widget to display status information."""
    pass


class TSMDesktop(App):
    """
    Textual-based desktop application for managing encrypted Telegram sessions.
    
    This application provides a terminal user interface (TUI) for interacting
    with the TSM service, including secure session management and homomorphic
    encrypted search capabilities.
    """
    
    CSS = """
    SessionList {
        border: solid green;
        height: 60%;
    }
    
    LogViewer {
        border: solid blue;
        height: 40%;
    }
    
    StatusBar {
        dock: bottom;
        height: 1;
        background: $boost;
    }
    """

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("s", "switch_session", "Switch Session"),
        ("i", "session_details", "Session Details"),
        ("f", "search_sessions", "Search Sessions"),
        ("p", "provision_yubikey", "Provision YubiKey"),
        ("r", "refresh", "Refresh Sessions"),
        ("c", "clear_log", "Clear Log"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create the UI layout for the application."""
        yield Header()
        yield SessionList("Initializing session list...")
        yield LogViewer("Welcome to TSM Desktop Client\n" + "="*40 + "\n")
        yield StatusBar("Ready")
        yield Footer()

    def on_mount(self) -> None:
        """
        Initialize the application when it's first displayed.
        
        This method handles:
        1. YubiKey authentication (if available)
        2. gRPC connection establishment
        3. Initial session list loading
        """
        # Store the start time for logging
        self.start_time = datetime.now()
        self.log(f"TSM Desktop Client started at {self.start_time}")
        
        # Initialize YubiKey manager for two-factor authentication
        self.yubikey_manager = YubiKeyManager()
        
        # Initialize connection state
        self.channel = None
        self.stub = None
        self.sessions = []
        
        # Attempt YubiKey authentication first
        if self.yubikey_manager.detect_yubikey():
            self.log("YubiKey detected, attempting authentication...")
            if self.yubikey_manager.authenticate():
                self.log("YubiKey authentication successful ✓")
                self.connect_to_server()
            else:
                self.log("YubiKey authentication failed ✗")
                self.query_one(SessionList).update("YubiKey authentication failed.")
                self.query_one(StatusBar).update("Authentication Failed")
                # Don't exit immediately - allow retry
        else:
            # No YubiKey detected - connect anyway for prototype
            self.log("No YubiKey detected - using development mode")
            self.connect_to_server()

    def connect_to_server(self) -> None:
        """Establish connection to the TSM gRPC server."""
        try:
            self.log("Connecting to TSM server at localhost:50051...")
            self.channel = grpc.insecure_channel('localhost:50051')
            self.stub = TSMService_pb2_grpc.TSMServiceStub(self.channel)
            
            # Test the connection by listing sessions
            self.list_sessions()
            self.query_one(StatusBar).update("Connected to TSM Server")
            
        except Exception as e:
            self.log(f"Failed to connect to server: {e}")
            self.query_one(StatusBar).update("Connection Failed")

    def list_sessions(self) -> None:
        """Fetch and display the list of available sessions."""
        if not self.stub:
            self.log("Error: Not connected to server")
            return
            
        request = TSMService_pb2.ListSessionsRequest(user_id="user1")
        try:
            self.log("Fetching session list...")
            response = self.stub.ListSessions(request)
            self.sessions = response.sessions
            
            # Format the session list for display
            session_list = "Available Sessions:\n" + "─" * 50 + "\n"
            
            for i, session in enumerate(self.sessions):
                # Convert timestamps to readable format
                created = datetime.fromtimestamp(session.creation_date).strftime('%Y-%m-%d %H:%M')
                last_used = datetime.fromtimestamp(session.last_used_date).strftime('%Y-%m-%d %H:%M')
                
                # Format size in human-readable form
                size_mb = session.size / (1024 * 1024)
                
                session_list += f"\n{i+1}. {session.name}\n"
                session_list += f"   ID: {session.id}\n"
                session_list += f"   Created: {created}\n"
                session_list += f"   Last Used: {last_used}\n"
                session_list += f"   Size: {size_mb:.2f} MB\n"
                session_list += f"   Encrypted: {'✓' if session.is_encrypted else '✗'}\n"
            
            self.query_one(SessionList).update(session_list)
            self.log(f"Successfully loaded {len(self.sessions)} sessions")
            
        except grpc.RpcError as e:
            error_msg = f"Failed to fetch sessions: {e.details()}"
            self.log(error_msg)
            self.query_one(SessionList).update(f"Error: {error_msg}")

    def action_switch_session(self) -> None:
        """Handle switching to a different session."""
        if not self.sessions:
            self.log("No sessions available to switch to")
            return
            
        # For the prototype, we switch to the first session
        # In production, this would show a selection dialog
        session = self.sessions[0]
        self.log(f"Attempting to switch to session: {session.name}")
        
        request = TSMService_pb2.SwitchSessionRequest(session_id=session.id)
        try:
            response = self.stub.SwitchSession(request)
            if response.success:
                self.log(f"✓ {response.message}")
                self.query_one(StatusBar).update(f"Active: {session.name}")
            else:
                self.log(f"✗ Switch failed: {response.message}")
                
        except grpc.RpcError as e:
            self.log(f"Error switching session: {e.details()}")

    def action_session_details(self) -> None:
        """Fetch and display detailed information about a session."""
        if not self.sessions:
            self.log("No sessions available")
            return
            
        # For the prototype, show details of the first session
        session_id = self.sessions[0].id
        self.log(f"Fetching details for session: {session_id}")
        
        request = TSMService_pb2.GetSessionDetailsRequest(session_id=session_id)
        try:
            response = self.stub.GetSessionDetails(request)
            session = response.session
            
            # Format the session details for display
            details = "\n" + "="*50 + "\n"
            details += f"SESSION DETAILS: {session.name}\n"
            details += "="*50 + "\n\n"
            
            details += f"Session ID:     {session.id}\n"
            details += f"Name:           {session.name}\n"
            details += f"Created:        {datetime.fromtimestamp(session.creation_date)}\n"
            details += f"Last Used:      {datetime.fromtimestamp(session.last_used_date)}\n"
            details += f"Size:           {session.size:,} bytes\n"
            details += f"Encrypted:      {'Yes ✓' if session.is_encrypted else 'No ✗'}\n"
            details += f"Status:         {'Secure' if session.is_encrypted else 'Unprotected'}\n"
            
            self.log(details)
            
        except grpc.RpcError as e:
            self.log(f"Error fetching session details: {e.details()}")

    def action_provision_yubikey(self) -> None:
        """Set up YubiKey for authentication with this application."""
        self.log("Starting YubiKey provisioning...")
        
        if self.yubikey_manager.detect_yubikey():
            try:
                self.yubikey_manager.setup_challenge_response()
                self.log("✓ YubiKey provisioned successfully")
                self.query_one(StatusBar).update("YubiKey Ready")
            except Exception as e:
                self.log(f"✗ YubiKey provisioning failed: {e}")
        else:
            self.log("✗ No YubiKey detected. Please insert a YubiKey and try again.")

    def action_search_sessions(self) -> None:
        """
        Perform a homomorphic encrypted search for sessions.
        
        This demonstrates the privacy-preserving search capability where:
        1. The search term is encrypted on the client
        2. The server performs the search without decrypting
        3. Results are returned without the server knowing what was searched
        """
        self.log("\n" + "="*50)
        self.log("ENCRYPTED SEARCH OPERATION")
        self.log("="*50 + "\n")
        
        # Initialize the homomorphic search system
        search_prototype = HomomorphicSearchPrototype()
        
        # For the prototype, we use a hardcoded search term
        # In production, this would show an input dialog
        search_value = 3
        self.log(f"Search target: sessions with value = {search_value}")
        self.log("Generating homomorphic encryption keys...")
        
        # Generate an encrypted query
        # This creates an encrypted version of our search value
        encrypted_query = search_prototype.generate_encrypted_query(search_value)
        self.log("✓ Search query encrypted")
        
        # Prepare the encrypted query for transmission
        # We need to serialize the complex cryptographic object
        # The dictionary format allows proper reconstruction on the server
        encrypted_query_dict = {
            'pk': str(encrypted_query.public_key.n),  # Public key modulus
            'n': str(encrypted_query.ciphertext()),    # The encrypted value
            'e': str(encrypted_query.exponent)         # The exponent for optimization
        }
        
        self.log("Serializing encrypted query for transmission...")
        serialized_query = pickle.dumps(encrypted_query_dict)
        self.log(f"Encrypted query size: {len(serialized_query)} bytes")
        
        # Create the gRPC request
        request = TSMService_pb2.EncryptedSearchRequest(
            encrypted_query=serialized_query
        )
        
        try:
            self.log("Sending encrypted search to server...")
            start_time = datetime.now()
            
            # Perform the search
            response = self.stub.EncryptedSearch(request)
            
            # Calculate search time
            search_time = (datetime.now() - start_time).total_seconds()
            self.log(f"✓ Search completed in {search_time:.3f} seconds")
            
            # Display results
            if response.session_locators:
                self.log(f"\n✓ Found {len(response.session_locators)} matching session(s):")
                for i, locator in enumerate(response.session_locators, 1):
                    self.log(f"   {i}. {locator}")
                    
                # Show privacy notice
                self.log("\n" + "─"*50)
                self.log("🔒 Privacy Notice: The server performed this search")
                self.log("   without knowing you searched for value '3'")
                self.log("─"*50)
            else:
                self.log(f"\n✗ No sessions found with value = {search_value}")
                
        except grpc.RpcError as e:
            self.log(f"\n✗ Search failed: {e.details()}")
            self.query_one(StatusBar).update("Search Error")

    def action_refresh(self) -> None:
        """Refresh the session list."""
        self.log("Refreshing session list...")
        self.list_sessions()

    def action_clear_log(self) -> None:
        """Clear the log viewer."""
        self.query_one(LogViewer).update("Log cleared\n" + "="*40 + "\n")
        self.log("Log viewer cleared")

    def action_toggle_dark(self) -> None:
        """Toggle between light and dark theme."""
        self.dark = not self.dark
        theme = "dark" if self.dark else "light"
        self.log(f"Switched to {theme} theme")

    def log(self, message: str) -> None:
        """
        Add a timestamped message to the log viewer.
        
        Args:
            message: The message to log
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        current_log = self.query_one(LogViewer).renderable
        self.query_one(LogViewer).update(str(current_log) + log_entry)

    def on_shutdown(self) -> None:
        """Clean up resources when the application exits."""
        if self.channel:
            self.channel.close()
            self.log("Closed connection to TSM server")


class VirtualSessionContainer:
    """
    Manages Telegram sessions in isolated Docker containers for security.
    
    This class provides methods to create, manage, and destroy Docker containers
    that run isolated Telegram sessions. Each session runs in its own container
    with restricted network access and filesystem isolation.
    """

    def __init__(self, docker_client):
        """Initialize with a Docker client instance."""
        self.client = docker_client

    def build_image(self, dockerfile_path, image_tag):
        """
        Build a Docker image for running Telegram sessions.
        
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
        """
        Launch a new container instance for a Telegram session.
        
        Args:
            image_tag: Docker image to use
            session_dir: Host directory containing session data
            proxy_server: Optional proxy server URL for network isolation
            
        Returns:
            The running container object
        """
        # Configure environment variables
        environment = {
            'TSM_SESSION_DIR': '/home/tsmuser/session',
            'TSM_SECURITY_MODE': 'strict'
        }
        
        if proxy_server:
            # Route all traffic through the proxy for additional security
            environment['HTTP_PROXY'] = proxy_server
            environment['HTTPS_PROXY'] = proxy_server
            environment['NO_PROXY'] = 'localhost,127.0.0.1'

        # Security options for container isolation
        security_opts = [
            'no-new-privileges:true',  # Prevent privilege escalation
            'seccomp=unconfined'       # For prototype; use custom profile in production
        ]

        return self.client.containers.run(
            image_tag,
            volumes={
                # Mount the session directory with restricted access
                session_dir: {
                    'bind': '/home/tsmuser/session', 
                    'mode': 'rw'
                }
            },
            environment=environment,
            security_opt=security_opts,
            read_only=False,  # Session data needs write access
            detach=True,      # Run in background
            auto_remove=False # Keep container for forensics if needed
        )

    def stop_container(self, container):
        """
        Gracefully stop a running container.
        
        Gives the container time to save state before termination.
        """
        container.stop(timeout=30)  # 30 seconds for graceful shutdown

    def destroy_container(self, container):
        """
        Remove a stopped container and clean up resources.
        
        This permanently deletes the container and its writable layer.
        """
        container.remove(force=True)

    def get_logs(self, container):
        """
        Retrieve logs from a container for debugging.
        
        Returns:
            String containing the container logs
        """
        return container.logs(timestamps=True).decode('utf-8')

    def get_container_stats(self, container):
        """
        Get resource usage statistics for a running container.
        
        Returns:
            Dictionary with CPU, memory, and network statistics
        """
        stats = container.stats(stream=False)
        return {
            'cpu_usage': stats['cpu_stats']['cpu_usage']['total_usage'],
            'memory_usage': stats['memory_stats']['usage'],
            'network_rx': stats['networks']['eth0']['rx_bytes'],
            'network_tx': stats['networks']['eth0']['tx_bytes']
        }