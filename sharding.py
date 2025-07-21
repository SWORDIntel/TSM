from secretsharing import PlaintextToHexSecretSharer

def create_shards(data: bytes, num_backends: int, threshold: int) -> list[str]:
    """
    Splits data into a number of shards using Shamir's Secret Sharing.

    Args:
        data: The data to be split.
        num_backends: The number of shards to create.
        threshold: The number of shards required to reconstruct the data.

    Returns:
        A list of shards.
    """
    shards = PlaintextToHexSecretSharer.split_secret(data.hex(), threshold, num_backends)
    return shards

def reconstruct_from_shards(shards: list[str]) -> bytes:
    """
    Reconstructs the original data from a list of shards.

    Args:
        shards: A list of shards.

    Returns:
        The reconstructed data.
    """
    secret_hex = PlaintextToHexSecretSharer.recover_secret(shards)
    return bytes.fromhex(secret_hex)
