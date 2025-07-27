import unittest
import json
from policy_engine import PolicyEngine

class TestPolicyEngine(unittest.TestCase):

    def setUp(self):
        with open("policy.json", "w") as f:
            json.dump({
                "priority": ["network", "time"],
                "default": "session_default_safe",
                "contexts": {
                    "network": {
                        "Secure_LAN": "session_alpha_trusted",
                        "Public_WiFi": "session_gamma_stealth"
                    },
                    "time": {
                        "Work_Hours": "session_beta_corp"
                    }
                }
            }, f)
        self.engine = PolicyEngine()

    def test_get_session_for_context_network_priority(self):
        context = {"network": "Secure_LAN", "time": "Work_Hours"}
        self.assertEqual(self.engine.get_session_for_context(context), "session_alpha_trusted")

    def test_get_session_for_context_time_priority(self):
        context = {"network": "Unknown", "time": "Work_Hours"}
        self.assertEqual(self.engine.get_session_for_context(context), "session_beta_corp")

    def test_get_session_for_context_default(self):
        context = {"network": "Unknown", "time": "Off_Hours"}
        self.assertEqual(self.engine.get_session_for_context(context), "session_default_safe")

if __name__ == '__main__':
    unittest.main()
