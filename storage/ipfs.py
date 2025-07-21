from storage.base import StorageBackend

class IPFSStorage(StorageBackend):
    """
    A storage backend that saves data to IPFS.
    """

    def __init__(self, ipfs_client):
        self.ipfs_client = ipfs_client

    def upload(self, session_id: str, encrypted_data: bytes) -> str:
        """
        Uploads session data to IPFS.
        """
        cid = self.ipfs_client.add_bytes(encrypted_data)
        return cid

    def download(self, locator: str) -> bytes:
        """
        Downloads data from IPFS.
        """
        return self.ipfs_client.cat(locator)

    def delete(self, locator: str) -> bool:
        """
        Deletes data from IPFS.
        Note: This is not a standard IPFS operation.
        Pinning is used to keep data, and unpinning allows it to be garbage collected.
        """
        try:
            self.ipfs_client.pin.rm(locator)
            return True
        except Exception:
            return False


    def list_all(self) -> list[str]:
        """
        Lists all pinned locators.
        """
        pins = self.ipfs_client.pin.ls(type="recursive")
        return [pin["cid"] for pin in pins]
