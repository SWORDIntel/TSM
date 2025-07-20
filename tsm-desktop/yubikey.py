import os
from yubikit.core.smartcard import SmartCardConnection
from yubikit.management import ManagementSession
from yubikit.oath import OathSession
from yubikit.support import get_name, read_info
from ykman.descriptor import get_descriptors
from ykman.device import connect_to_device
from yubikit.core import NotSupportedError
from yubikit.core.otp import OtpConnection
from yubikit.core.smartcard import SmartCardConnection
from yubikit.yubiotp import YubiOtpSession
from yubikit.management import ManagementSession
from yubikit.oath import OathSession
from yubikit.support import get_name, read_info
from ykman.descriptor import get_descriptors
from ykman.device import connect_to_device
from yubikit.core import NotSupportedError
from yubikit.core.otp import OtpConnection
from yubikit.core.smartcard import SmartCardConnection
from yubikit.yubiotp import YubiOtpSession


class YubiKeyManager:
    def __init__(self, secret: bytes = b"mysecretkey"):
        self.secret = secret

    def detect_yubikey(self) -> bool:
        """Detects if a YubiKey is connected."""
        descriptors = list(get_descriptors())
        return len(descriptors) > 0

    def setup_challenge_response(self, slot: int = 2):
        """Provisions the YubiKey with a challenge-response secret."""
        descriptor = list(get_descriptors())[0]
        with descriptor.open_device(OtpConnection) as connection:
            session = YubiOtpSession(connection)
            if slot == 1:
                session.configure_slot(slot).program_chal_resp_hmac(self.secret)
            elif slot == 2:
                session.configure_slot(slot).program_chal_resp_hmac(self.secret)

    def authenticate(self, slot: int = 2) -> bool:
        """Performs the challenge-response authentication."""
        descriptor = list(get_descriptors())[0]
        with descriptor.open_device(OtpConnection) as connection:
            session = YubiOtpSession(connection)
            challenge = os.urandom(16)
            try:
                response = session.calculate_hmac_sha1(slot, challenge)
                import hmac, hashlib
                expected_response = hmac.new(self.secret, challenge, hashlib.sha1).digest()
                return response == expected_response
            except Exception:
                return False
