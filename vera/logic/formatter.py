from typing import Dict, Any, Optional
from vera.models import MerchantContext, CategoryContext, TriggerContext, CustomerContext

class TemplateFormatter:
    def __init__(self):
        self.templates = {
            "opening": [
                "Hi! I've analyzed your {category} listing and found an opportunity to {strategy}. Your calls are currently {metric}% {comparison} than similar businesses. Should we proceed?",
                "Hello! I'm Vera. I noticed your visibility is {metric}% {comparison} than average. I can help you {strategy} to fix this. Are you interested?",
                "Greetings! To improve your {category} performance, I suggest we {strategy}. This targets your {metric}% {comparison} metric. Ready to start?"
            ],
            "commit": [
                "Understood! I am now initiating the {strategy} process for your listing. You will see these updates live shortly.",
                "Action taken: I've successfully drafted and scheduled your new {strategy} campaign. It is now active.",
                "Perfect! I have processed your request to {strategy}. Your business profile is being updated now.",
                "Confirmed. I've enabled the {strategy} automation for your account. I'll monitor the results for you."
            ],
            "follow_up": [
                "I've completed that task. Would you like to explore other ways to improve your {metric} metrics?",
                "That action is now live. What else can I help you optimize today?",
                "Since we've handled {strategy}, would you like me to look into increasing your customer calls as well?"
            ],
            "stop": [
                "I understand. I've disabled all AI optimizations for your account. You won't receive further messages. Goodbye.",
                "Process terminated. I have removed your listing from the active suggestion queue. Have a great day.",
                "Understood. Stopping all communication now. If you need me again, you know where to find me."
            ],
            "hostile": [
                "I apologize for the frustration. I am ending this session and will not contact you again. Take care.",
                "I hear you. I'm stopping all AI processes for this merchant immediately. Ending conversation.",
                "Understood. I will cease all communication and optimization efforts for your business now. Goodbye."
            ],
            "auto_reply": [
                "I've detected an automated response. I will pause my suggestions for 12 hours to avoid any loops. See you later!",
                "System auto-reply detected. Waiting for a manual update before I proceed with any changes.",
                "It looks like you have an automated assistant active. I'll wait until you're back before we continue our optimization."
            ]
        }

    @staticmethod
    def get_slots(opp_type: str, features: Dict[str, Any], merchant: MerchantContext, category: CategoryContext, trigger: TriggerContext, customer: Optional[CustomerContext] = None) -> Dict[str, Any]:
        p = trigger.payload or {}
        ident = merchant.identity or {}
        
        # 1. Base slots with safe fallbacks
        slots = {
            "merchant_name": ident.get("name", "our business"),
            "merchant": ident.get("name", "our business"),
            "locality": ident.get("locality", "your area"),
            "category_name": category.display_name,
            "category": category.display_name,
            "cx_name": customer.identity.get("first_name", "there") if customer else "there",
            "metric": p.get("metric", p.get("authority", "performance")),
            "proof": p.get("drop_pct", p.get("views", p.get("search_volume", "significant"))),
            "gap_pct": p.get("gap_pct", p.get("drop_pct", "20")),
            "months": p.get("months", p.get("months_ago", "6")),
            "theme": p.get("theme", "customer interest"),
            "match_name": p.get("match_name", "today's event"),
            "competitor_name": p.get("competitor_name", "a competitor"),
            "source": p.get("authority", p.get("source", "Industry")),
            "source_ref": p.get("regulation_id", p.get("id", "Reference")),
            "service": category.display_name,
            "offer": "exclusive update",
            "action": "update",
            "cohort": "customers"
        }
        
        # 2. Dynamic Injection: Pull EVERYTHING from identity and payload
        for k, v in ident.items(): slots.setdefault(k, v)
        for k, v in p.items(): slots.setdefault(k, v)
        
        # 3. Strategy Overrides
        if "REGULATORY" in opp_type:
            slots.update({"action": "compliance update", "cohort": "business"})
        elif "RECALL" in opp_type:
            slots.update({"action": "reminder", "cohort": "loyal customers"})
            
        # 4. Combine with Features
        combined = {**features, **slots}
        
        # 5. ULTIMATE SAFETY: Stringify everything for Pydantic & Template Formatting
        final_slots = {}
        for k, v in combined.items():
            if isinstance(v, float):
                final_slots[k] = f"{v:.2f}"
            else:
                final_slots[k] = str(v)
            
        return final_slots
