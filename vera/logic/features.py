from vera.models import MerchantContext, CategoryContext, TriggerContext, CustomerContext
from typing import Optional, Dict, Any

class FeatureExtractor:
    @staticmethod
    def extract(
        merchant: MerchantContext, 
        category: CategoryContext, 
        trigger: TriggerContext, 
        customer: Optional[CustomerContext] = None
    ) -> Dict[str, Any]:
        features = {}

        # 1. Calibrated Performance Gaps (Ratio-based)
        category_avg_ctr = category.peer_stats.avg_ctr if category.peer_stats.avg_ctr > 0 else 0.030
        features["normalized_ctr"] = merchant.performance.ctr / category_avg_ctr
        features["ctr_gap"] = 1.0 - features["normalized_ctr"] # e.g., 0.42x below average
        
        # 2. Demand Signals
        features["demand_signal"] = trigger.payload.get("search_volume", 100)
        
        # 3. Conversion Rate
        total_leads = merchant.performance.calls + merchant.performance.directions
        features["conversion_rate"] = total_leads / merchant.performance.views if merchant.performance.views > 0 else 0
        
        # 4. Opportunity Size (The "Top 1%" Feature)
        base_opp = features["demand_signal"] * (1 - features["conversion_rate"])
        # 10/10 Reliability Upgrade: Never return zero size for a valid trigger
        features["opportunity_size"] = max(10.0, base_opp)
        
        # 5. Customer Health
        cx_agg = merchant.customer_aggregate
        total_cx = cx_agg.get("total_unique_ytd", 1)
        lapsed_cx = cx_agg.get("lapsed_180d_plus", 0)
        features["lapsed_ratio"] = lapsed_cx / total_cx
        
        # 6. Feasibility Flags
        features["has_active_offer"] = len([o for o in merchant.offers if o.get("status") == "active"]) > 0
        features["can_launch_offer"] = len(merchant.offers) < 5
        
        return features

    @staticmethod
    def normalize(value: float, min_val: float, max_val: float) -> float:
        if max_val == min_val:
            return 0.0
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
