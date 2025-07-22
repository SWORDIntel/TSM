import unittest
import boto3
from storage.s3 import S3Storage
import os

class TestCephS3Compatibility(unittest.TestCase):
    def setUp(self):
        # --- User Configuration ---
        # Replace the following placeholders with your Ceph RADOS Gateway credentials
        self.ceph_endpoint_url = "http://your-ceph-rados-gateway-url.com"
        self.ceph_access_key = "YOUR_CEPH_ACCESS_KEY"
        self.ceph_secret_key = "YOUR_CEPH_SECRET_KEY"
        self.ceph_bucket_name = "your-bucket-name"
        # --- End User Configuration ---

        # Skip tests if placeholder values are still present
        if self.ceph_endpoint_url == "http://your-ceph-rados-gateway-url.com" or \
           self.ceph_access_key == "YOUR_CEPH_ACCESS_KEY" or \
           self.ceph_secret_key == "YOUR_CEPH_SECRET_KEY" or \
           self.ceph_bucket_name == "your-bucket-name":
            self.skipTest("Ceph credentials not configured. Please edit test_ceph_s3_compatibility.py.")

        s3_client = boto3.client(
            "s3",
            endpoint_url=self.ceph_endpoint_url,
            aws_access_key_id=self.ceph_access_key,
            aws_secret_access_key=self.ceph_secret_key,
        )
        self.storage = S3Storage(s3_client, self.ceph_bucket_name)
        self.test_session_id = "test_session_123"
        self.test_data = b"This is some test data."

    def test_upload_download_delete(self):
        """
        Tests the upload, download, and delete functionality.
        """
        # Upload data
        locator = self.storage.upload(self.test_session_id, self.test_data)
        self.assertIsNotNone(locator)

        # Download data
        downloaded_data = self.storage.download(locator)
        self.assertEqual(self.test_data, downloaded_data)

        # Delete data
        success = self.storage.delete(locator)
        self.assertTrue(success)

        # Verify deletion
        with self.assertRaises(Exception):
            self.storage.download(locator)

    def test_list_all(self):
        """
        Tests the list_all functionality.
        """
        # Upload a few files
        locators = []
        for i in range(3):
            locator = self.storage.upload(f"test_session_{i}", f"test_data_{i}".encode())
            locators.append(locator)

        # List all
        all_locators = self.storage.list_all()
        for locator in locators:
            self.assertIn(locator, all_locators)

        # Clean up
        for locator in locators:
            self.storage.delete(locator)

if __name__ == "__main__":
    unittest.main()
