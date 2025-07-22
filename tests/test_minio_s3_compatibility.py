import unittest
import os
import boto3
from storage.s3 import S3Storage

class TestMinioS3Compatibility(unittest.TestCase):
    def setUp(self):
        self.minio_endpoint = os.environ.get("MINIO_ENDPOINT")
        self.minio_access_key = os.environ.get("MINIO_ACCESS_KEY")
        self.minio_secret_key = os.environ.get("MINIO_SECRET_KEY")
        self.bucket_name = "test-bucket"

        self.assertIsNotNone(self.minio_endpoint, "MINIO_ENDPOINT not set")
        self.assertIsNotNone(self.minio_access_key, "MINIO_ACCESS_KEY not set")
        self.assertIsNotNone(self.minio_secret_key, "MINIO_SECRET_KEY not set")

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.minio_endpoint,
            aws_access_key_id=self.minio_access_key,
            aws_secret_access_key=self.minio_secret_key,
        )

        try:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
        except self.s3_client.exceptions.BucketAlreadyOwnedByYou:
            pass

        self.storage = S3Storage(self.s3_client, self.bucket_name)

    def tearDown(self):
        # Clean up created objects
        for key in self.storage.list_all():
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
        self.s3_client.delete_bucket(Bucket=self.bucket_name)

    def test_upload_download_delete(self):
        session_id = "test_session"
        data = b"test data"

        # Upload
        locator = self.storage.upload(session_id, data)
        self.assertIsNotNone(locator)

        # Download
        downloaded_data = self.storage.download(locator)
        self.assertEqual(data, downloaded_data)

        # Delete
        self.assertTrue(self.storage.delete(locator))

        # Verify deletion
        with self.assertRaises(self.s3_client.exceptions.NoSuchKey):
            self.storage.download(locator)

if __name__ == "__main__":
    unittest.main()
