from py_ecc.bn128 import FQ, FQ2

def serialize_point(point):
    """
    Serializes a py_ecc point to a hex string.
    """
    if isinstance(point, tuple):
        if isinstance(point[0], FQ2):
            return {
                "x": [point[0].coeffs[0].n, point[0].coeffs[1].n],
                "y": [point[1].coeffs[0].n, point[1].coeffs[1].n],
            }
        else:
            return {"x": point[0].n, "y": point[1].n}
    return None


def deserialize_point(data):
    """
    Deserializes a hex string to a py_ecc point.
    """
    if isinstance(data["x"], list):
        return (
            FQ2([data["x"][0], data["x"][1]]),
            FQ2([data["y"][0], data["y"][1]]),
        )
    else:
        return (FQ(data["x"]), FQ(data["y"]))


def serialize_proof(proof):
    """
    Serializes a py_ecc proof to a dictionary of hex strings.
    """
    return {
        "H": serialize_point(proof[0]),
        "proof": serialize_point(proof[1]),
    }


def deserialize_proof(serialized_proof):
    """
    Deserializes a dictionary of hex strings to a py_ecc proof.
    """
    return (
        deserialize_point(serialized_proof["H"]),
        deserialize_point(serialized_proof["proof"]),
    )
