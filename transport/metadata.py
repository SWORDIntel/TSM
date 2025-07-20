import os
import time
import threading
import secrets

class MetadataProtection:
    """
    Protects metadata by padding messages and sending dummy traffic.
    """
    SIZE_BUCKETS = [64, 128, 256, 512, 1024, 2048, 4096]

    def __init__(self, send_callback):
        self._send = send_callback
        self._dummy_traffic_thread = threading.Thread(
            target=self._generate_dummy_traffic, daemon=True
        )
        self._stop_dummy_traffic = threading.Event()

    def start(self):
        """
        Starts the dummy traffic generation thread.
        """
        self._dummy_traffic_thread.start()

    def stop(self):
        """
        Stops the dummy traffic generation thread.
        """
        self._stop_dummy_traffic.set()
        self._dummy_traffic_thread.join()

    def _get_padded_size(self, data_size):
        """
        Finds the smallest bucket that can fit the data.
        """
        for size in self.SIZE_BUCKETS:
            if data_size <= size:
                return size
        raise ValueError("Data size exceeds the largest bucket")

    def prepare_message(self, data):
        """
        Pads the message to the next bucket size.
        """
        padded_size = self._get_padded_size(len(data))
        padding_length = padded_size - len(data)
        padding = os.urandom(padding_length)
        return data + padding

    def _constant_time_process(self, data):
        """
        Placeholder for a constant-time operation.
        """
        # In a real implementation, this would be a constant-time
        # operation to avoid leaking timing information.
        time.sleep(0.001)

    def _generate_dummy_traffic(self):
        """
        Sends dummy messages at random intervals.
        """
        while not self._stop_dummy_traffic.is_set():
            time.sleep(secrets.randbelow(5) + 1)
            bucket_index = secrets.randbelow(len(self.SIZE_BUCKETS))
            dummy_message_size = self.SIZE_BUCKETS[bucket_index]
            dummy_message = os.urandom(dummy_message_size)
            self._send(dummy_message)
            self._constant_time_process(dummy_message)
