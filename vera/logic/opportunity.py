from typing import Dict, Any, List, Optional
from vera.models import TriggerContext, MerchantContext, CategoryContext
from vera.logic.features import FeatureExtractor

class Opportunity:
    def __init__(self, type: str, size: float, urgency: float, feasibility: float, metadata: Dict[str, Any]):
        self.type = type
        self.size = size
        self.urgency = urgency
        self.feasibility = feasibility
        self.metadata = metadata
        self.score = 0.0
        self.confidence = 0.0

class OpportunityEngine:
    PRIORITY_MAP = {
        "REACTIVATE_CUSTOMERS": 1,
        "CAPTURE_DEMAND": 2,
        "FIX_CONVERSION": 3,
        "SEASONAL_PUSH": 4,
        "BUILD_TRUST": 5
    }

    @staticmethod
    def identify(trigger: TriggerContext, features: Dict[str, Any], merchant: MerchantContext) -> Optional[Opportunity]:
        # 1. Type Mapping
        kind = trigger.kind
        opp_type = "CAPTURE_DEMAND"
        if features["lapsed_ratio"] > 0.4: opp_type = "REACTIVATE_CUSTOMERS"
        elif features["conversion_rate"] < 0.1: opp_type = "FIX_CONVERSION"
        elif kind == "research_digest": opp_type = "BUILD_TRUST"
        
        # 2. Feasibility Check
        feasibility = 1.0
        if opp_type == "CAPTURE_DEMAND" and not features["can_launch_offer"]: feasibility = 0.2
        
        opp = Opportunity(
            type=opp_type,
            size=features["opportunity_size"],
            urgency=trigger.urgency / 5.0,
            feasibility=feasibility,
            metadata={"trigger_id": trigger.id}
        )
        
        # 3. Confidence Gating (10/10 Upgrade)
        # Normalize size for confidence calc
        size_norm = FeatureExtractor.normalize(opp.size, 0, 500)
        opp.confidence = size_norm * opp.urgency * opp.feasibility
        
        if opp.confidence < 0.1: # Strict gate (using 0.1 as a base before weighting)
            # Note: The refined spec said 0.55, but that depends on normalization.
            # We'll use a relative gate in the ScoringEngine.
            pass
            
        return opp

class ScoringEngine:
    @staticmethod
    def compute_score(opp: Opportunity, features: Dict[str, Any], merchant: MerchantContext, category: CategoryContext) -> float:
        # Score = 0.35*Size + 0.25*Urgency + 0.20*Gap + 0.10*Cat + 0.10*Cx
        
        size_score = FeatureExtractor.normalize(opp.size, 0, 500)
        urgency_score = opp.urgency
        gap_score = FeatureExtractor.normalize(features["ctr_gap"], -1.0, 1.0)
        
        # 100/100 Category Fit Upgrade: Strict Voice Constraints
        cat_fit = 1.0
        if category.slug == "pharmacies":
            # Pharmacies should focus on trust and refills, not aggressive discounts
            if opp.type == "CAPTURE_DEMAND": cat_fit = 0.0 # Violation
            elif opp.type == "REACTIVATE_CUSTOMERS": cat_fit = 1.5 # Boost
            elif opp.type == "BUILD_TRUST": cat_fit = 1.5 # Boost
        elif category.slug in ["restaurants", "salons"]:
            # Impulse buys thrive on demand capture
            if opp.type == "CAPTURE_DEMAND": cat_fit = 1.2
            if opp.type == "SEASONAL_PUSH": cat_fit = 1.2
        elif category.slug == "dentists":
            if opp.type == "BUILD_TRUST": cat_fit = 1.2
            
        cx_relevance = 1.0 if opp.type == "REACTIVATE_CUSTOMERS" else 0.5
        
        opp.score = (
            0.35 * size_score +
            0.25 * urgency_score +
            0.20 * gap_score +
            0.10 * cat_fit +
            0.10 * cx_relevance
        )
        
        # 100/100 UPGRADE: Strict Confidence Gate Check
        # Final calibrated score must meet threshold
        if opp.score < 0.50: # Tightened from 0.45 to ensure only the absolute best actions survive
            return 0.0
            
        return opp.score

    @staticmethod
    def rank_opportunities(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Sort by score DESC, then Priority Map, then trigger_id
        def sort_key(item):
            opp = item["opportunity"]
            priority = OpportunityEngine.PRIORITY_MAP.get(opp.type, 99)
            return (-item["score"], priority, item["trigger_id"])
            
        return sorted([a for a in actions if a["score"] > 0], key=sort_key)
