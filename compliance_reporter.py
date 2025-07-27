import json

class ComplianceReporter:
    def __init__(self, log_file_path="audit_log.json"):
        self.log_file_path = log_file_path

    def generate_user_activity_report(self, user_id):
        report = f"# User Activity Report for {user_id}\n\n"
        try:
            with open(self.log_file_path, "r") as f:
                for line in f:
                    log_entry = json.loads(line)
                    if log_entry.get("actorId") == user_id or log_entry.get("targetId") == user_id:
                        report += f"## Event: {log_entry['eventId']}\n"
                        report += f"- **Timestamp:** {log_entry['timestamp']}\n"
                        report += f"- **Action:** {log_entry['actionType']}\n"
                        report += f"- **Actor ID:** {log_entry['actorId']}\n"
                        report += f"- **Target ID:** {log_entry['targetId']}\n"
                        report += f"- **Outcome:** {log_entry['outcome']}\n"
                        report += f"- **Source IP:** {log_entry['sourceIp']}\n"
                        report += "\n"
        except FileNotFoundError:
            report += "No audit log file found.\n"
        return report
