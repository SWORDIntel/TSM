import uuid
from storage.base import StorageBackend

class S3Storage(StorageBackend):
    """
    A storage backend that saves data to AWS S3.
    """

    def __init__(self, s3_client, bucket_name: str):
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    def upload(self, session_id: str, encrypted_data: bytes) -> str:
        """
        Uploads session data to S3.
        """
        locator = f"tsm_sessions/{uuid.uuid4()}.session"
        self.s3_client.put_object(
            Bucket=self.bucket_name, Key=locator, Body=encrypted_data
        )
        return locator

    def download(self, locator: str) -> bytes:
        """
        Downloads data from S3.
        """
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=locator)
        return response["Body"].read()

    def delete(self, locator: str) -> bool:
        """
        Deletes data from S3.
        """
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=locator)
        return True

    def list_all(self) -> list[str]:
        """
        Lists all locators in the S3 bucket.
        """
        locators = []
        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix="tsm_sessions/")
        for page in pages:
            for obj in page.get("Contents", []):
                locators.append(obj["Key"])
        return locators
