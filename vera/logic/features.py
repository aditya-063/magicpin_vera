from typing import Dict, Any, Optional
from vera.models import MerchantContext, CategoryContext, TriggerContext, CustomerContext

class FeatureExtractor:
    @staticmethod
    def extract(merchant: MerchantContext, category: CategoryContext, trigger: TriggerContext, customer: Optional[CustomerContext] = None) -> Dict[str, Any]:
        f = {}
        p = trigger.payload or {}
        
        # Safe Metric Calculation
        perf = merchant.performance
        # Universal Slug Normalization (Handles Singular & Plural)
        raw_slug = getattr(category, "slug", "unknown").lower()
        slug_map = {
            "dentist": "dentist", "dentists": "dentist",
            "gym": "gym", "gyms": "gym",
            "pharmacy": "pharmacy", "pharmacies": "pharmacy",
            "restaurant": "restaurant", "restaurants": "restaurant",
            "salon": "salon", "salons": "salon"
        }
        category = slug_map.get(raw_slug, raw_slug.rstrip('s'))
        views = getattr(perf, "views", 0) or 1
        calls = getattr(perf, "calls", 0) or 0
        dirs = getattr(perf, "directions", 0) or 0
        
        f["conversion_rate"] = (calls + dirs) / views
        f["demand_signal"] = p.get("search_volume", p.get("views", 100))
        f["opportunity_size"] = max(10.0, float(f["demand_signal"]) * (1 - f["conversion_rate"]))
        
        # Expanded Context
        f["months_ago"] = p.get("months") or p.get("months_ago") or 6
        f["gap_pct"] = p.get("gap_pct") or p.get("drop_pct") or 20
        f["urgency_score"] = trigger.urgency / 5.0
        
        return f
