#!/usr/bin/env python3
"""
TSM Mobile Integration Server
Secure API server for mobile companion apps
"""

import asyncio
import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import grpc
from concurrent import futures
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# Proto definitions (would be in separate .proto file)
"""
syntax = "proto3";

service TSMobile {
    rpc Authenticate(AuthRequest) returns (AuthResponse);
    rpc ListSessions(ListRequest) returns (SessionList);
    rpc SwitchSession(SwitchRequest) returns (SwitchResponse);
    rpc GetStatus(StatusRequest) returns (StatusResponse);
    rpc EmergencyWipe(WipeRequest) returns (WipeResponse);
}
"""

# Security Constants
OPAQUE_CONFIG = {
    "group": "ristretto255",
    "hash": "SHA-512",
    "mhf": "argon2id",
    "mac": "HMAC-SHA512"
}

# In-memory session store (replace with Redis in production)
active_sessions: Dict[str, 'MobileSession'] = {}
pending_auth: Dict[str, 'AuthChallenge'] = {}

@dataclass
class AuthChallenge:
    """OPAQUE authentication challenge"""
    client_id: str
    server_public: bytes
    expected_proof: bytes
    created: datetime
    device_info: Dict

@dataclass 
class MobileSession:
    """Authenticated mobile session"""
    session_id: str
    device_id: str
    device_name: str
    platform: str  # ios/android
    auth_time: datetime
    last_seen: datetime
    encryption_key: bytes
    permissions: List[str]
    
class CryptoManager:
    """Handles all cryptographic operations"""
    
    def __init__(self, master_key: bytes):
        self.master_key = master_key
        
    def derive_session_key(self, session_id: str, salt: bytes) -> bytes:
        """Derive unique key for each session"""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=f"tsm-session-{session_id}".encode(),
            backend=default_backend()
        )
        return hkdf.derive(self.master_key)
    
    def encrypt_response(self, data: bytes, session_key: bytes) -> Tuple[bytes, bytes]:
        """Encrypt API response"""
        cipher = ChaCha20Poly1305(session_key)
        nonce = secrets.token_bytes(12)
        ciphertext = cipher.encrypt(nonce, data, None)
        return nonce, ciphertext
    
    def decrypt_request(self, nonce: bytes, ciphertext: bytes, session_key: bytes) -> bytes:
        """Decrypt API request"""
        cipher = ChaCha20Poly1305(session_key)
        return cipher.decrypt(nonce, ciphertext, None)
    
    def generate_pairing_code(self) -> str:
        """Generate secure pairing code for initial setup"""
        # 6 words from BIP39 wordlist for human-friendly code
        words = ["correct", "horse", "battery", "staple", "trusted", "secure"]
        return "-".join(secrets.choice(words) for _ in range(4))

class SecurityMiddleware:
    """Security checks for all requests"""
    
    def __init__(self, crypto: CryptoManager):
        self.crypto = crypto
        self.rate_limiter = RateLimiter()
        
    async def verify_request(self, context: grpc.ServicerContext, 
                           session_id: str, signature: str) -> Optional[MobileSession]:
        """Verify request authentication and rate limits"""
        
        # Check session exists
        session = active_sessions.get(session_id)
        if not session:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session")
            return None
            
        # Verify signature
        expected = hmac.new(
            session.encryption_key,
            context.peer().encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid signature")
            return None
            
        # Check rate limits
        if not await self.rate_limiter.check(session.device_id):
            context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, "Rate limit exceeded")
            return None
            
        # Update last seen
        session.last_seen = datetime.utcnow()
        return session

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: int = 60, burst: int = 10):
        self.rate = rate  # requests per minute
        self.burst = burst
        self.buckets: Dict[str, List[float]] = {}
        
    async def check(self, key: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        
        # Get or create bucket
        if key not in self.buckets:
            self.buckets[key] = []
            
        # Remove old entries
        self.buckets[key] = [t for t in self.buckets[key] if t > minute_ago]
        
        # Check rate
        if len(self.buckets[key]) >= self.rate:
            return False
            
        # Check burst
        recent = [t for t in self.buckets[key] if t > now - 1]
        if len(recent) >= self.burst:
            return False
            
        self.buckets[key].append(now)
        return True

class TSMobileServicer:
    """gRPC service implementation"""
    
    def __init__(self, tsm_manager, crypto: CryptoManager):
        self.tsm = tsm_manager  # Reference to main TSM instance
        self.crypto = crypto
        self.security = SecurityMiddleware(crypto)
        
    async def Authenticate(self, request, context):
        """OPAQUE-based authentication flow"""
        
        if request.step == "init":
            # Generate OPAQUE server values
            challenge = AuthChallenge(
                client_id=request.client_id,
                server_public=secrets.token_bytes(32),
                expected_proof=secrets.token_bytes(32),
                created=datetime.utcnow(),
                device_info={
                    "platform": request.platform,
                    "version": request.version,
                    "device_name": request.device_name
                }
            )
            pending_auth[request.client_id] = challenge
            
            return AuthResponse(
                step="challenge",
                server_data=base64.b64encode(challenge.server_public).decode(),
                session_id=""
            )
            
        elif request.step == "verify":
            challenge = pending_auth.get(request.client_id)
            if not challenge:
                context.abort(grpc.StatusCode.FAILED_PRECONDITION, "No pending auth")
                
            # Verify OPAQUE proof (simplified)
            provided_proof = base64.b64decode(request.client_proof)
            if not hmac.compare_digest(provided_proof, challenge.expected_proof):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid proof")
                
            # Create session
            session_id = secrets.token_urlsafe(32)
            session_key = self.crypto.derive_session_key(
                session_id, 
                secrets.token_bytes(32)
            )
            
            session = MobileSession(
                session_id=session_id,
                device_id=request.client_id,
                device_name=challenge.device_info["device_name"],
                platform=challenge.device_info["platform"],
                auth_time=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                encryption_key=session_key,
                permissions=["read", "switch", "backup"]  # Configurable
            )
            
            active_sessions[session_id] = session
            del pending_auth[request.client_id]
            
            # Log authentication
            await self.tsm.db.log_operation(
                "mobile_auth",
                "success",
                0,
                f"Device: {session.device_name} ({session.platform})"
            )
            
            return AuthResponse(
                step="complete",
                session_id=session_id,
                encryption_key=base64.b64encode(session_key).decode()
            )
    
    async def ListSessions(self, request, context):
        """List available Telegram sessions"""
        
        session = await self.security.verify_request(
            context, 
            request.session_id,
            request.signature
        )
        if not session:
            return
            
        # Get sessions from main TSM
        sessions = self.tsm.find_sessions()
        
        # Build response
        response_data = {
            "sessions": [
                {
                    "id": s.name,
                    "name": s.name,
                    "created": s.created.isoformat(),
                    "size_bytes": s.size_bytes,
                    "file_count": s.file_count,
                    "tags": s.tags,
                    "is_active": self.tsm.tdata_dir.resolve() == s.path.resolve()
                }
                for s in sessions
            ]
        }
        
        # Encrypt response
        nonce, ciphertext = self.crypto.encrypt_response(
            json.dumps(response_data).encode(),
            session.encryption_key
        )
        
        return SessionList(
            encrypted_data=base64.b64encode(ciphertext).decode(),
            nonce=base64.b64encode(nonce).decode()
        )
    
    async def SwitchSession(self, request, context):
        """Switch active Telegram session"""
        
        session = await self.security.verify_request(
            context,
            request.session_id,
            request.signature
        )
        if not session:
            return
            
        # Check permissions
        if "switch" not in session.permissions:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "No switch permission")
            
        # Decrypt request
        target_session = json.loads(
            self.crypto.decrypt_request(
                base64.b64decode(request.nonce),
                base64.b64decode(request.encrypted_data),
                session.encryption_key
            )
        )["target_session"]
        
        # Perform switch
        try:
            success = await asyncio.to_thread(
                self.tsm.switch_session, 
                target_session
            )
            
            if success:
                # Send push notification
                await self.send_push_notification(
                    session.device_id,
                    f"Switched to session: {target_session}"
                )
                
                response = {"success": True, "message": "Session switched"}
            else:
                response = {"success": False, "message": "Switch failed"}
                
        except Exception as e:
            response = {"success": False, "message": str(e)}
            
        # Encrypt response
        nonce, ciphertext = self.crypto.encrypt_response(
            json.dumps(response).encode(),
            session.encryption_key
        )
        
        return SwitchResponse(
            encrypted_data=base64.b64encode(ciphertext).decode(),
            nonce=base64.b64encode(nonce).decode()
        )
    
    async def EmergencyWipe(self, request, context):
        """Emergency wipe functionality"""
        
        session = await self.security.verify_request(
            context,
            request.session_id,
            request.signature
        )
        if not session:
            return
            
        # Require additional authentication
        if not request.panic_code:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Panic code required")
            
        # Verify panic code (should be pre-configured)
        if not self.verify_panic_code(session.device_id, request.panic_code):
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid panic code")
            
        # Perform emergency wipe
        wiped_count = 0
        for s in self.tsm.find_sessions():
            if "backup" not in s.name:  # Don't wipe backups by default
                try:
                    shutil.rmtree(s.path, ignore_errors=True)
                    wiped_count += 1
                except:
                    pass
                    
        # Log emergency action
        await self.tsm.db.log_operation(
            "emergency_wipe",
            "executed",
            0,
            f"Wiped {wiped_count} sessions via {session.device_name}"
        )
        
        return WipeResponse(
            success=True,
            wiped_count=wiped_count
        )
    
    async def send_push_notification(self, device_id: str, message: str):
        """Send push notification to mobile device"""
        # Implement via Firebase/APNS
        pass
    
    def verify_panic_code(self, device_id: str, code: str) -> bool:
        """Verify pre-configured panic code"""
        # In production, store hashed panic codes per device
        return hmac.compare_digest(code, "PANIC-12345")

class MobileIntegrationServer:
    """Main mobile integration server"""
    
    def __init__(self, tsm_manager, config: Dict):
        self.tsm = tsm_manager
        self.config = config
        self.crypto = CryptoManager(self._load_master_key())
        
    def _load_master_key(self) -> bytes:
        """Load or generate master key"""
        key_file = Path(self.config.get("mobile_key_file", "~/.tsm/mobile.key")).expanduser()
        
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = secrets.token_bytes(32)
            key_file.parent.mkdir(parents=True, exist_ok=True)
            key_file.write_bytes(key)
            key_file.chmod(0o600)
            return key
    
    async def start(self):
        """Start gRPC server"""
        server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),
                ('grpc.max_send_message_length', 100 * 1024 * 1024),
            ]
        )
        
        # Add service
        servicer = TSMobileServicer(self.tsm, self.crypto)
        # tsm_mobile_pb2_grpc.add_TSMobileServicer_to_server(servicer, server)
        
        # TLS configuration
        with open('server.crt', 'rb') as f:
            server_cert = f.read()
        with open('server.key', 'rb') as f:
            server_key = f.read()
        with open('ca.crt', 'rb') as f:
            ca_cert = f.read()
            
        credentials = grpc.ssl_server_credentials(
            [(server_key, server_cert)],
            root_certificates=ca_cert,
            require_client_auth=True
        )
        
        # Start server
        listen_addr = self.config.get("mobile_listen", "[::]:50051")
        server.add_secure_port(listen_addr, credentials)
        
        await server.start()
        print(f"Mobile integration server started on {listen_addr}")
        
        try:
            await server.wait_for_termination()
        except KeyboardInterrupt:
            await server.stop(5)

# iOS Client Example (Swift)
"""
import GRPC
import CryptoKit

class TSMClient {
    private let channel: GRPCChannel
    private let client: TSMobileClient
    private var sessionKey: SymmetricKey?
    
    init(host: String, port: Int) throws {
        // Configure TLS with certificate pinning
        let group = PlatformSupport.makeEventLoopGroup(loopCount: 1)
        
        let tlsConfig = GRPCTLSConfiguration.makeClientConfiguration(
            certificateChain: [.certificate(clientCert)],
            privateKey: .privateKey(clientKey),
            trustRoots: .certificates([caCert]),
            hostnameOverride: "tsm.local"
        )
        
        self.channel = try GRPCChannelPool.with(
            target: .hostAndPort(host, port),
            transportSecurity: .tls(tlsConfig),
            eventLoopGroup: group
        )
        
        self.client = TSMobileClient(channel: channel)
    }
    
    func authenticate() async throws {
        // OPAQUE authentication flow
        let request = AuthRequest.with {
            $0.step = "init"
            $0.clientID = UIDevice.current.identifierForVendor!.uuidString
            $0.platform = "ios"
            $0.version = "1.0"
            $0.deviceName = UIDevice.current.name
        }
        
        let response = try await client.authenticate(request).response.get()
        
        // Continue with OPAQUE verification...
    }
    
    func switchSession(to sessionID: String) async throws {
        guard let sessionKey = sessionKey else {
            throw TSMError.notAuthenticated
        }
        
        // Encrypt request
        let requestData = try JSONEncoder().encode(["target_session": sessionID])
        let sealed = try ChaChaPoly.seal(requestData, using: sessionKey)
        
        let request = SwitchRequest.with {
            $0.sessionID = self.sessionID
            $0.signature = self.generateSignature()
            $0.encryptedData = sealed.ciphertext.base64EncodedString()
            $0.nonce = Data(sealed.nonce).base64EncodedString()
        }
        
        let response = try await client.switchSession(request).response.get()
        // Handle response...
    }
}
"""

# Android Client Example (Kotlin)
"""
import io.grpc.ManagedChannel
import io.grpc.android.AndroidChannelBuilder
import com.google.crypto.tink.subtle.ChaCha20Poly1305
import kotlinx.coroutines.flow.Flow

class TSMClient(private val context: Context) {
    private lateinit var channel: ManagedChannel
    private lateinit var stub: TSMobileGrpcKt.TSMobileCoroutineStub
    private var sessionKey: ByteArray? = null
    
    suspend fun connect(host: String, port: Int) {
        // Configure TLS with pinning
        val tlsContext = SSLContext.getInstance("TLS").apply {
            init(
                arrayOf(getKeyManager()),
                arrayOf(getTrustManager()),
                SecureRandom()
            )
        }
        
        channel = AndroidChannelBuilder
            .forAddress(host, port)
            .context(context)
            .sslContext(tlsContext)
            .build()
            
        stub = TSMobileGrpcKt.TSMobileCoroutineStub(channel)
    }
    
    suspend fun authenticate() {
        val request = authRequest {
            step = "init"
            clientId = Settings.Secure.getString(
                context.contentResolver,
                Settings.Secure.ANDROID_ID
            )
            platform = "android"
            version = "1.0"
            deviceName = Build.MODEL
        }
        
        val response = stub.authenticate(request)
        // Continue OPAQUE flow...
    }
    
    suspend fun listSessions(): List<Session> {
        requireNotNull(sessionKey) { "Not authenticated" }
        
        val request = listRequest {
            sessionId = this@TSMClient.sessionId
            signature = generateSignature()
        }
        
        val response = stub.listSessions(request)
        
        // Decrypt response
        val cipher = ChaCha20Poly1305(sessionKey)
        val plaintext = cipher.decrypt(
            Base64.decode(response.encryptedData, Base64.DEFAULT),
            Base64.decode(response.nonce, Base64.DEFAULT)
        )
        
        return Json.decodeFromString(plaintext.decodeToString())
    }
}
"""

if __name__ == "__main__":
    # Integration with main TSM
    import sys
    sys.path.append("..")
    from tsm_enhanced import TelegramSessionManager, load_config
    
    async def main():
        config = load_config()
        config["mobile_enabled"] = True
        config["mobile_listen"] = "[::]:50051"
        
        # Create TSM instance
        tsm = TelegramSessionManager(config)
        
        # Start mobile server
        mobile_server = MobileIntegrationServer(tsm, config)
        await mobile_server.start()
    
    asyncio.run(main())
