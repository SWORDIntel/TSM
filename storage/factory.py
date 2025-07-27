import json
from storage.base import StorageBackend
from storage.local import LocalNetworkStorage
from storage.s3 import S3Storage
from storage.gcs import GCSStorage
from storage.ipfs import IPFSStorage
# Import other storage backends here
# from storage.minio import MinIOStorage
# from storage.ceph import CephStorage

class StorageFactory:
    """
    Factory for creating storage backend instances.
    """

    @staticmethod
    def load_from_config(path: str) -> list[StorageBackend]:
        """
        Loads storage backends from a JSON configuration file.

        Args:
            path: The path to the configuration file.

        Returns:
            A list of initialized storage backend instances.
        """
        with open(path, 'r') as f:
            config = json.load(f)

        backends = []
        for backend_config in config:
            backend_type = backend_config.get("type")
            if backend_type == "local":
                instance = LocalNetworkStorage(backend_config["base_path"])
                backends.append(instance)
            elif backend_type == "s3":
                # Note: This requires a pre-configured s3_client
                # In a real application, you would initialize the client here
                # based on the config (e.g., access key, secret key, region)
                # For this example, we assume a client is passed in.
                pass
            elif backend_type == "gcs":
                # Note: This requires a pre-configured storage_client
                # In a real application, you would initialize the client here
                # based on the config (e.g., credentials JSON)
                pass
            elif backend_type == "ipfs":
                # Note: This requires a pre-configured ipfs_client
                pass
            # Add other backends here
            # elif backend_type == "minio":
            #     ...
            # elif backend_type == "ceph":
            #     ...

        return backends
