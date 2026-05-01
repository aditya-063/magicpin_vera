from typing import Dict, Any, List
from vera.models import MerchantContext, CategoryContext, BotAction

class PolicyEngine:
    @staticmethod
    def validate_action(action: Dict[str, Any], merchant: MerchantContext, category: CategoryContext) -> bool:
        """
        Returns True if the action is valid according to business rules.
        """
        # 1. Category Specific Rules
        if category.slug == "pharmacies" and "discount" in action.get("body", "").lower():
            # Pharmacies should avoid aggressive discount framing (Regulation/Trust)
            if "aggressive" in action.get("rationale", "").lower():
                return False

        if category.slug == "dentists" and any(word in action.get("body", "").lower() for word in ["guaranteed", "cure"]):
            # Dentists have strict clinical taboos
            return False

        # 2. Merchant Specific Rules
        if action.get("type") == "launch_offer" and len([o for o in merchant.offers if o.get("status") == "active"]) > 2:
            # Don't suggest a new offer if they already have 3+ active ones (Choice Paralysis)
            return False

        # 3. Global Hard Constraints
        body = action.get("body", "")
        # WhatsApp session rules: no URLs in first touch
        if "http://" in body or "https://" in body:
            # Allow short domains or internal handles if needed, but strict on protocols
            return False
        
        # Too many questions (Confusing) - Relaxed from 2 to 3
        if body.count("?") > 3:
            return False

        return True

    @staticmethod
    def adjust_score(score: float, action_type: str, merchant: MerchantContext) -> float:
        """
        Nudges the score based on policy preferences.
        """
        # Penalize launch_discount if conversion is already high (Why lose margin?)
        leads = merchant.performance.calls + merchant.performance.directions
        conv = leads / merchant.performance.views if merchant.performance.views > 0 else 0
        
        if action_type == "LAUNCH_DISCOUNT" and conv > 0.15:
            return score * 0.7
            
        # Bonus for trust-building in regulated categories
        if action_type == "IMPROVE_TRUST" and merchant.performance.ctr < 0.02:
            return score * 1.2

        return score
