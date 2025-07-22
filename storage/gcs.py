from storage.base import StorageBackend
from google.cloud import storage

class GCSStorage(StorageBackend):
    """
    Google Cloud Storage backend for session data.
    """

    def __init__(self, storage_client: storage.Client, bucket_name: str):
        self.storage_client = storage_client
        self.bucket_name = bucket_name
        self.bucket = self.storage_client.bucket(self.bucket_name)

    def upload(self, session_id: str, encrypted_data: bytes) -> str:
        """
        Uploads session data to GCS.
        """
        blob = self.bucket.blob(session_id)
        blob.upload_from_string(encrypted_data)
        return f"gcs://{self.bucket_name}/{session_id}"

    def download(self, locator: str) -> bytes:
        """
        Downloads data from GCS.
        """
        blob_name = locator.replace(f"gcs://{self.bucket_name}/", "")
        blob = self.bucket.blob(blob_name)
        return blob.download_as_bytes()

    def delete(self, locator: str) -> bool:
        """
        Deletes data from GCS.
        """
        try:
            blob_name = locator.replace(f"gcs://{self.bucket_name}/", "")
            blob = self.bucket.blob(blob_name)
            blob.delete()
            return True
        except Exception:
            return False

    def list_all(self) -> list[str]:
        """
        Lists all locators in the GCS bucket.
        """
        blobs = self.storage_client.list_blobs(self.bucket_name)
        return [f"gcs://{self.bucket_name}/{blob.name}" for blob in blobs]
