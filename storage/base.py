from abc import ABC, abstractmethod

class StorageBackend(ABC):
    """
    Abstract base class for a storage backend.
    """

    @abstractmethod
    def upload(self, session_id: str, encrypted_data: bytes) -> str:
        """
        Uploads session data to the storage backend.

        Args:
            session_id: The ID of the session.
            encrypted_data: The encrypted session data.

        Returns:
            A unique string locator for the uploaded data.
        """
        pass

    @abstractmethod
    def download(self, locator: str) -> bytes:
        """
        Downloads data from the storage backend.

        Args:
            locator: The unique locator for the data.

        Returns:
            The downloaded data.
        """
        pass

    @abstractmethod
    def delete(self, locator: str) -> bool:
        """
        Deletes data from the storage backend.

        Args:
            locator: The unique locator for the data.

        Returns:
            True if the deletion was successful, False otherwise.
        """
        pass

    @abstractmethod
    def list_all(self) -> list[str]:
        """
        Lists all locators managed by the backend.

        Returns:
            A list of all locators.
        """
        pass

    async def store_with_failover(self, session_data):
        """
        Stores session data with failover to another backend.
        """
        for backend in self.backends:
            try:
                return await backend.store(session_data)
            except Exception:
                continue
