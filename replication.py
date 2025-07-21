from storage.base import StorageBackend
from sharding import create_shards

class ReplicationManager:
    """
    Manages the replication of data across multiple storage backends.
    """

    def __init__(self, backends: list[StorageBackend]):
        self.backends = backends

    def replicate_upload(self, session_id: str, encrypted_data: bytes) -> list[str]:
        """
        Replicates the upload of data to all configured backends.

        Args:
            session_id: The ID of the session.
            encrypted_data: The encrypted session data.

        Returns:
            A list of locators from each backend.
        """
        locators = []
        for backend in self.backends:
            locator = backend.upload(session_id, encrypted_data)
            locators.append(locator)
        return locators

    def shard_upload(
        self, session_id: str, encrypted_data: bytes, threshold: int
    ) -> list[str]:
        """
        Splits data into shards and uploads each shard to a different backend.

        Args:
            session_id: The ID of the session.
            encrypted_data: The encrypted session data.
            threshold: The number of shards required to reconstruct the data.

        Returns:
            A list of locators for each shard.
        """
        num_backends = len(self.backends)
        shards = create_shards(encrypted_data, num_backends, threshold)
        locators = []
        for i, backend in enumerate(self.backends):
            shard_data = shards[i].encode("utf-8")
            locator = backend.upload(session_id, shard_data)
            locators.append(locator)
        return locators
