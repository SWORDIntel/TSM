import os
import uuid
from storage.base import StorageBackend

class LocalNetworkStorage(StorageBackend):
    """
    A storage backend that saves data to a local network share.
    """

    def __init__(self, base_path: str):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def upload(self, session_id: str, encrypted_data: bytes) -> str:
        """
        Uploads session data to the local network share.
        """
        locator = str(uuid.uuid4())
        file_path = os.path.join(self.base_path, f"{locator}.session")
        with open(file_path, "wb") as f:
            f.write(encrypted_data)
        return locator

    def download(self, locator: str) -> bytes:
        """
        Downloads data from the local network share.
        """
        file_path = os.path.join(self.base_path, f"{locator}.session")
        with open(file_path, "rb") as f:
            return f.read()

    def delete(self, locator: str) -> bool:
        """
        Deletes data from the local network share.
        """
        try:
            file_path = os.path.join(self.base_path, f"{locator}.session")
            os.remove(file_path)
            return True
        except FileNotFoundError:
            return False

    def list_all(self) -> list[str]:
        """
        Lists all locators in the local network share.
        """
        locators = []
        for filename in os.listdir(self.base_path):
            if filename.endswith(".session"):
                locators.append(filename.replace(".session", ""))
        return locators
