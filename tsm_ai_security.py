"""
CLASSIFICATION: TOP SECRET
OPERATION: AEGIS
AUTHOR: JULES
DESCRIPTION: AI-powered security analysis for TSM sessions.
"""

from dataclasses import dataclass
from typing import List, Dict, Any

import numpy as np
from sklearn.ensemble import IsolationForest

@dataclass
class SecurityReport:
    """A structured report of a session's security analysis."""
    risk_score: float
    threats: List[str]
    recommendations: List[str]

class SessionSecurityAI:
    """
    Analyzes session data using a pre-trained Isolation Forest model
    to detect anomalies and assess risk.
    """

    def __init__(self, model_path: str = None):
        """
        Initializes the security AI.

        Args:
            model_path: Path to a pre-trained model file. If None,
                        a mock model is created.
        """
        if model_path:
            # In a real scenario, we would load the model from a file.
            # self.model = joblib.load(model_path)
            pass
        else:
            # For this task, we create a mock pre-trained model.
            # This model is "trained" on normal-looking data.
            rng = np.random.RandomState(42)
            X_train = 0.2 * rng.randn(100, 3)
            self.model = IsolationForest(random_state=rng).fit(X_train)

    def _extract_features(self, session_data: Dict[str, Any]) -> np.ndarray:
        """
        Extracts and preprocesses features from session data for the model.
        """
        # Example features. In a real implementation, these would be more
        # sophisticated and based on the actual session data structure.
        login_hour = session_data.get("last_login_time", "00:00").split(":")[0]
        message_frequency = session_data.get("message_frequency_per_hour", 0)
        api_calls = session_data.get("api_calls_last_24h", 0)

        # Normalize or scale features as needed
        features = np.array([
            int(login_hour) / 24.0,
            message_frequency / 1000.0,  # Assuming max 1000 messages/hr
            api_calls / 100.0          # Assuming max 100 API calls/24h
        ]).reshape(1, -1)

        return features

    def analyze_session(self, session_data: Dict[str, Any]) -> SecurityReport:
        """
        Analyzes mock session data to produce a security report.

        Args:
            session_data: A dictionary containing mock session data.

        Returns:
            A SecurityReport with the analysis results.
        """
        features = self._extract_features(session_data)

        # The `decision_function` gives a score where negative values are
        # more anomalous. We'll invert and scale it to be a risk score
        # from 0.0 to 1.0.
        anomaly_score = self.model.decision_function(features)[0]
        risk_score = 1 / (1 + np.exp(anomaly_score * 5)) # Sigmoid scaling

        threats = []
        recommendations = []

        if risk_score > 0.7:
            threats.append("Anomalous Activity Detected")
            recommendations.append("Review recent session activity for suspicious behavior.")
            if features[0, 0] > 0.9 or features[0, 0] < 0.2: # Late night or early morning
                 threats.append("Unusual Login Time")
                 recommendations.append("Verify the login was legitimate.")

        if risk_score > 0.9:
             threats.append("High Risk of Compromise")
             recommendations.append("Consider isolating the session and rotating credentials immediately.")


        if not threats:
            threats.append("No Immediate Threats Detected")
            recommendations.append("Session appears normal. Continue monitoring.")

        return SecurityReport(
            risk_score=risk_score,
            threats=threats,
            recommendations=recommendations,
        )
