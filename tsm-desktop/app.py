import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mock_server')))

import grpc
import TSMService_pb2
import TSMService_pb2_grpc
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from yubikey import YubiKeyManager

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
        self.yubikey_manager = YubiKeyManager()
        if self.yubikey_manager.detect_yubikey():
            if self.yubikey_manager.authenticate():
                self.channel = grpc.insecure_channel('localhost:50051')
                self.stub = TSMService_pb2_grpc.TSMServiceStub(self.channel)
                self.list_sessions()
            else:
                self.query_one(SessionList).update("YubiKey authentication failed.")
                self.exit()
        else:
            # Fallback to existing password-based mechanism (not implemented yet)
            self.channel = grpc.insecure_channel('localhost:50051')
            self.stub = TSMService_pb2_grpc.TSMServiceStub(self.channel)
            self.list_sessions()

    def list_sessions(self) -> None:
        """List the sessions."""
        request = TSMService_pb2.ListSessionsRequest(user_id="user1")
        try:
            response = self.stub.ListSessions(request)
            self.sessions = response.sessions
            session_list = "Sessions:\n"
            for i, session in enumerate(self.sessions):
                session_list += f"{i+1}. {session.name} ({session.id})\n"
            self.query_one(SessionList).update(session_list)
        except grpc.RpcError as e:
            self.query_one(SessionList).update(f"Error: {e.details()}")

    def action_switch_session(self) -> None:
        """Switches to a session."""
        if self.sessions:
            # For simplicity, we'll switch to the first session.
            # In a real app, you'd let the user select a session.
            session_id = self.sessions[0].id
            request = TSMService_pb2.SwitchSessionRequest(session_id=session_id)
            try:
                response = self.stub.SwitchSession(request)
                self.query_one(StatusBar).update(response.message)
            except grpc.RpcError as e:
                self.query_one(StatusBar).update(f"Error: {e.details()}")

    def action_session_details(self) -> None:
        """Gets and displays session details."""
        if self.sessions:
            # For simplicity, we'll get details for the first session.
            # In a real app, you'd let the user select a session.
            session_id = self.sessions[0].id
            request = TSMService_pb2.GetSessionDetailsRequest(session_id=session_id)
            try:
                response = self.stub.GetSessionDetails(request)
                details = f"Session Details:\n"
                details += f"ID: {response.session.id}\n"
                details += f"Name: {response.session.name}\n"
                details += f"Creation Date: {response.session.creation_date}\n"
                details += f"Last Used Date: {response.session.last_used_date}\n"
                details += f"Size: {response.session.size}\n"
                details += f"Encrypted: {response.session.is_encrypted}\n"
                self.query_one(LogViewer).update(details)
            except grpc.RpcError as e:
                self.query_one(LogViewer).update(f"Error: {e.details()}")

    def action_provision_yubikey(self) -> None:
        """Provisions the YubiKey."""
        if self.yubikey_manager.detect_yubikey():
            self.yubikey_manager.setup_challenge_response()
            self.query_one(StatusBar).update("YubiKey provisioned.")
        else:
            self.query_one(StatusBar).update("No YubiKey detected.")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark
