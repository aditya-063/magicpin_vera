import re
from typing import Literal

class IntentClassifier:
    AUTO_REPLY_PATTERNS = [
        r"thank you for contacting",
        r"respond shortly",
        r"will get back to you",
        r"automated assistant",
        r"busy right now",
        r"jaankari ke liye shukriya.*hamari team", # Hindi auto-reply pattern from brief
    ]

    POSITIVE_PATTERNS = [
        r"\byes\b",
        r"\bok\b",
        r"sure",
        r"do it",
        r"send",
        r"agree",
        r"book",
        r"appointment",
        r"wed",
        r"thu",
        r"fri",
        r"sat",
        r"sun",
        r"mon",
        r"tue",
        r"ha(an)?\b", # Hindi 'Haan'
        r"theek hai", # Hindi 'Theek hai'
        r"chalega"    # Hindi 'Chalega'
    ]

    NEGATIVE_PATTERNS = [
        r"\bno\b",
        r"not interested",
        r"stop",
        r"nahi\b", # Hindi 'Nahi'
        r"rehne do" # Hindi 'Rehne do'
    ]

    @staticmethod
    def classify(message: str) -> Literal["POSITIVE_INTENT", "NEGATIVE_INTENT", "AUTO_REPLY", "OBJECTION", "UNKNOWN"]:
        msg = message.lower().strip()
        
        # 1. Auto-reply detection
        for pattern in IntentClassifier.AUTO_REPLY_PATTERNS:
            if re.search(pattern, msg):
                return "AUTO_REPLY"
        
        # 2. Hard Rejection
        for pattern in IntentClassifier.NEGATIVE_PATTERNS:
            if re.search(pattern, msg):
                return "NEGATIVE_INTENT"
                
        # 3. Positive Intent
        for pattern in IntentClassifier.POSITIVE_PATTERNS:
            if re.search(pattern, msg):
                return "POSITIVE_INTENT"
        
        # 4. Objection Detection (Simple heuristic: question mark or "but" or "cost")
        if "?" in msg or "but" in msg or "how much" in msg or "kitna" in msg:
            return "OBJECTION"
            
        return "UNKNOWN"
