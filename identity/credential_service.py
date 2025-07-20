from did_sdk import VerifiableCredential
from identity.manager import DecentralizedIdentityManager
import json

class CredentialService:
    """
    Provides services for issuing and verifying Verifiable Credentials (VCs).
    """

    def issue_tsm_access_credential(self, subject_did: str, issuer_manager: DecentralizedIdentityManager) -> str:
        """
        Issues a Verifiable Credential for TSM access.

        This method creates a VC that asserts the subject DID is authorized for
        TSM access. The VC is signed by the issuer's DID.

        Args:
            subject_did: The DID of the subject receiving the credential.
            issuer_manager: An instance of DecentralizedIdentityManager for the issuer.

        Returns:
            The Verifiable Credential in JSON format (str).
        """
        issuer_did, issuer_private_key = issuer_manager.create_did_key()

        credential_attributes = {
            "grant": "tsm_access",
            "usage": "unlimited",
        }

        vc = VerifiableCredential(
            issuer=issuer_did,
            subject=subject_did,
            credential_type="TSMAccessCredential",
            claims=credential_attributes,
        )

        signed_vc = vc.sign(issuer_private_key)
        return json.dumps(signed_vc)

    def verify_access_credential(self, vc_json: str) -> bool:
        """
        Verifies a TSM access credential.

        This method checks the cryptographic signature of the VC and returns
        True if it is valid.

        Args:
            vc_json: The Verifiable Credential in JSON format.

        Returns:
            True if the credential is valid, False otherwise.
        """
        vc_data = json.loads(vc_json)
        return VerifiableCredential.verify(vc_data)
