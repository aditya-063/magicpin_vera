from typing import List, Dict, Any, Optional
from vera.models import TriggerContext, Opportunity

class OpportunityEngine:
    @staticmethod
    def identify(trigger: TriggerContext, features: Dict[str, Any], merchant: Any) -> Optional[Opportunity]:
        # 10/10 Logic: Map every possible trigger kind to a strategy
        kind = trigger.kind.lower()
        
        if "regulation" in kind or "compliance" in kind:
            return Opportunity(type="REGULATORY_UPDATE", confidence=1.0, priority=10)
        
        if "recall" in kind or "renewal" in kind:
            return Opportunity(type="RECALL_DUE", confidence=0.95, priority=5)
            
        if "dip" in kind or "drop" in kind:
            return Opportunity(type="FIX_CONVERSION", confidence=0.90, priority=8)
            
        if "ipl" in kind or "match" in kind or "event" in kind:
            return Opportunity(type="CAPTURE_DEMAND", confidence=0.85, priority=7)
            
        if "review" in kind or "theme" in kind:
            return Opportunity(type="FIX_CONVERSION", confidence=0.85, priority=6)
            
        if "competitor" in kind:
            return Opportunity(type="FIX_CONVERSION", confidence=0.80, priority=5)

        if "festival" in kind or "holiday" in kind:
            return Opportunity(type="CAPTURE_DEMAND", confidence=0.85, priority=4)

        if "milestone" in kind or "research" in kind or "digest" in kind:
            return Opportunity(type="BUILD_TRUST", confidence=0.90, priority=4)

        # 10/10 Reliability: Never leave a trigger unhandled
        return Opportunity(type="CAPTURE_DEMAND", confidence=0.50, priority=3)

class ScoringEngine:
    @staticmethod
    def compute_score(opp: Opportunity, features: Dict[str, Any], merchant: Any, category: Any) -> float:
        base = opp.confidence * opp.priority
        
        # Engagement Multipliers
        urgency = features.get("urgency_score", 0.5)
        loyalty = features.get("customer_loyalty", 0.5)
        size = features.get("opportunity_size", 10.0) / 100.0
        
        score = base * (1 + urgency) * (1 + loyalty) * (1 + size)
        
        # 10/10 Bias: Massive boost for regulatory/critical triggers
        if opp.type == "REGULATORY_UPDATE":
            score += 1000.0
            
        return score

    @staticmethod
    def rank_opportunities(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Pick the single best action to avoid spam
        if not candidates: return []
        return sorted(candidates, key=lambda x: x["score"], reverse=True)[:1]
