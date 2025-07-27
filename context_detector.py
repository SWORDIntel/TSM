import os
from datetime import datetime

def detect_network_context(filepath="/tmp/tsm_context.txt"):
    """
    Reads the network context from a given file.

    Args:
        filepath (str): The path to the context file.

    Returns:
        str: The network context from the file or "Unknown" if the file doesn't exist.
    """
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read().strip()
    return "Unknown"

def detect_time_of_day():
    """
    Detects if the current time is within "Work_Hours" or "Off_Hours".

    Returns:
        str: "Work_Hours" or "Off_Hours".
    """
    now = datetime.now()
    if now.weekday() < 5 and 9 <= now.hour < 17:
        return "Work_Hours"
    return "Off_Hours"
