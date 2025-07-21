import grpc
from tsm_ai_security import SessionSecurityAI

class AISecurityInterceptor(grpc.ServerInterceptor):
    def __init__(self, security_ai: SessionSecurityAI, threshold: float = 0.9):
        self.security_ai = security_ai
        self.threshold = threshold

class AISecurityInterceptor(grpc.ServerInterceptor):
    def __init__(self, security_ai: SessionSecurityAI, threshold: float = 0.9):
        self.security_ai = security_ai
        self.threshold = threshold

    def intercept_service(self, continuation, handler_call_details):
        method_name = handler_call_details.method.split('/')[-1]

        # We only want to analyze methods that involve session data
        if method_name not in ["GetSessionData", "SwitchSession", "GetSessionDetails", "EncryptedSearch"]:
            return continuation(handler_call_details)

        # In a real implementation, we would extract meaningful data from the request.
        # For now, we'll use dummy data.
        session_data = {
            "last_login_time": "23:50",
            "message_frequency_per_hour": 150,
            "api_calls_last_24h": 80
        }

        report = self.security_ai.analyze_session(session_data)
        print(f"AI Security Analysis for {method_name}: Risk Score = {report.risk_score:.2f}")

        if report.risk_score > self.threshold:
            raise grpc.RpcError(grpc.StatusCode.PERMISSION_DENIED, "High risk")
        else:
            return continuation(handler_call_details)
