import hashlib

class AnonymizationService:
    def anonymize_log(self, log_json):
        anonymized_log = log_json.copy()
        if "actorId" in anonymized_log:
            anonymized_log["actorId"] = "ANON_" + hashlib.sha256(anonymized_log["actorId"].encode()).hexdigest()
        if "sourceIp" in anonymized_log:
            anonymized_log["sourceIp"] = "ANON_" + hashlib.sha256(anonymized_log["sourceIp"].encode()).hexdigest()
        return anonymized_log
