import json
import hashlib
import uuid
from datetime import datetime, timezone

class SecureAuditLogger:
    def __init__(self, log_file_path="audit_log.json"):
        self.log_file_path = log_file_path

    def get_last_entry_hash(self):
        try:
            with open(self.log_file_path, "rb") as f:
                lines = f.readlines()
                if not lines:
                    return hashlib.sha256(b"").hexdigest()
                last_line = lines[-1]
                return hashlib.sha256(last_line).hexdigest()
        except FileNotFoundError:
            return hashlib.sha256(b"").hexdigest()

    def log(self, actorId, actionType, targetId, outcome, sourceIp):
        log_entry = {
            "eventId": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actorId": actorId,
            "actionType": actionType,
            "targetId": targetId,
            "outcome": outcome,
            "sourceIp": sourceIp,
            "previousEntryHash": self.get_last_entry_hash(),
        }

        with open(self.log_file_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
