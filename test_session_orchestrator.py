import unittest
from unittest.mock import Mock
from session_orchestrator import SessionOrchestrator
import time

class TestSessionOrchestrator(unittest.TestCase):

    def test_recommend_session_switch(self):
        context_detector = Mock()
        context_detector.detect_network_context.return_value = "Public_WiFi"
        context_detector.detect_time_of_day.return_value = "Off_Hours"

        policy_engine = Mock()
        policy_engine.get_session_for_context.return_value = "session_gamma_stealth"

        orchestrator = SessionOrchestrator(context_detector, policy_engine)
        self.assertEqual(orchestrator.recommend_session(), "session_gamma_stealth")

    def test_recommend_session_no_switch(self):
        context_detector = Mock()
        context_detector.detect_network_context.return_value = "Unknown"
        context_detector.detect_time_of_day.return_value = "Off_Hours"

        policy_engine = Mock()
        policy_engine.get_session_for_context.return_value = "session_default_safe"

        orchestrator = SessionOrchestrator(context_detector, policy_engine)
        self.assertEqual(orchestrator.recommend_session(), "session_default_safe")

if __name__ == '__main__':
    unittest.main()
