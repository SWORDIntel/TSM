import unittest
import os
from context_detector import detect_network_context, detect_time_of_day
from freezegun import freeze_time

class TestContextDetector(unittest.TestCase):

    def test_detect_network_context_file_exists(self):
        with open("/tmp/tsm_context.txt", "w") as f:
            f.write("Secure_LAN")
        self.assertEqual(detect_network_context(), "Secure_LAN")
        os.remove("/tmp/tsm_context.txt")

    def test_detect_network_context_file_not_exists(self):
        if os.path.exists("/tmp/tsm_context.txt"):
            os.remove("/tmp/tsm_context.txt")
        self.assertEqual(detect_network_context(), "Unknown")

    @freeze_time("2023-10-27 10:00:00") # Friday
    def test_detect_time_of_day_work_hours(self):
        self.assertEqual(detect_time_of_day(), "Work_Hours")

    @freeze_time("2023-10-27 20:00:00") # Friday
    def test_detect_time_of_day_off_hours(self):
        self.assertEqual(detect_time_of_day(), "Off_Hours")

    @freeze_time("2023-10-28 10:00:00") # Saturday
    def test_detect_time_of_day_weekend(self):
        self.assertEqual(detect_time_of_day(), "Off_Hours")

if __name__ == '__main__':
    unittest.main()
