import hashlib
from py_ecc.bn128 import G1, G2, multiply, pairing, is_on_curve, b, b2, curve_order

class ZKSessionProof:
    def generate_proof(self, session_secret: str):
        """
        Generates a ZK-proof that demonstrates knowledge of the original secret
        without revealing it.
        """
        # 1. Hash the secret to get a private input `s`
        s = int.from_bytes(hashlib.sha256(session_secret.encode()).digest(), 'big') % curve_order

        # 2. The public input will be `H`, where `H = s*G2`
        H = multiply(G2, s)

        # 3. The proof will be `s*G1`
        proof = multiply(G1, s)

        return H, proof

    def verify_proof(self, H, proof) -> bool:
        """
        Verifies the proof against the public input H.
        """
        # Check if the points are on the curve
        if not is_on_curve(proof, b):
            return False
        if not is_on_curve(H, b2):
            return False

        # e(proof, G2) == e(G1, H)
        return pairing(G2, proof) == pairing(H, G1)
