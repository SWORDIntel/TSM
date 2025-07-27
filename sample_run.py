from secure_audit_logger import SecureAuditLogger
from compliance_reporter import ComplianceReporter
from anonymization_service import AnonymizationService
import json

# Initialize the logger
logger = SecureAuditLogger()

# Log some sample events
logger.log("user1", "SESSION_LOGIN", "session1", "SUCCESS", "192.168.1.1")
logger.log("user2", "SESSION_LOGIN", "session2", "SUCCESS", "192.168.1.2")
logger.log("user1", "REMOTE_WIPE_SENT", "device1", "SUCCESS", "192.168.1.1")

# Initialize the reporter
reporter = ComplianceReporter()

# Generate a report for user1
user1_report = reporter.generate_user_activity_report("user1")
print("--- User 1 Activity Report ---")
print(user1_report)

# Initialize the anonymization service
anonymizer = AnonymizationService()

# Anonymize a log entry
with open("audit_log.json", "r") as f:
    log_entry = json.loads(f.readline())
    anonymized_log = anonymizer.anonymize_log(log_entry)
    print("--- Anonymized Log Entry ---")
    print(json.dumps(anonymized_log, indent=2))
