import json

class PolicyEngine:
    """
    A class to determine the appropriate session based on the current context.
    """
    def __init__(self, policy_path="policy.json"):
        """
        Initializes the PolicyEngine.

        Args:
            policy_path (str): The path to the policy JSON file.
        """
        with open(policy_path, 'r') as f:
            self.policy = json.load(f)
        self.priority = self.policy.get("priority", [])
        self.contexts = self.policy.get("contexts", {})
        self.default_session = self.policy.get("default", "session_default_safe")

    def get_session_for_context(self, context):
        """
        Gets the session ID for the given context.

        Args:
            context (dict): A dictionary containing the current context.

        Returns:
            str: The determined session ID.
        """
        for context_type in self.priority:
            if context_type in context and context[context_type] in self.contexts.get(context_type, {}):
                return self.contexts[context_type][context[context_type]]
        return self.default_session
