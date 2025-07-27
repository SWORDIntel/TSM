import logging
import threading
import time
from datetime import datetime
import random
import json

class SessionOrchestrator:
    """
    The main orchestrator for managing sessions.
    """
    def __init__(self, context_detector, policy_engine):
        """
        Initializes the SessionOrchestrator.

        Args:
            context_detector: An instance of ContextDetector.
            policy_engine: An instance of PolicyEngine.
        """
        self.context_detector = context_detector
        self.policy_engine = policy_engine
        self.current_active_session = "session_default_safe"
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

    def recommend_session(self):
        """
        Recommends a session based on the current context.
        """
        network_context = self.context_detector.detect_network_context()
        time_of_day = self.context_detector.detect_time_of_day()
        context = {"network": network_context, "time": time_of_day}

        recommended_session = self.policy_engine.get_session_for_context(context)

        if recommended_session != self.current_active_session:
            logging.info(f"Session switch recommended: From {self.current_active_session} to {recommended_session}")
            self.current_active_session = recommended_session
        else:
            logging.info(f"No session switch advised. Current session remains: {self.current_active_session}")

        return recommended_session

    def run_scheduler(self, schedule_path="schedule.json"):
        """
        Runs the session scheduler in a background thread.
        """
        scheduler_thread = threading.Thread(target=self._scheduler_loop, args=(schedule_path,), daemon=True)
        scheduler_thread.start()

    def _scheduler_loop(self, schedule_path):
        """
        The main loop for the scheduler.
        """
        with open(schedule_path, 'r') as f:
            schedule = json.load(f)

        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            current_day = now.strftime("%A").lower()

            for event in schedule:
                if event["time"] == current_time:
                    if event["day"] == "all" or (event["day"] == "weekday" and now.weekday() < 5) or (event["day"] == "weekend" and now.weekday() >= 5):
                        delay = random.uniform(-0.15, 0.15) * 60
                        time.sleep(60 + delay)
                        logging.info(f"Scheduler: Switching to session {event['session_id']}")
                        self.current_active_session = event['session_id']
            time.sleep(60)
