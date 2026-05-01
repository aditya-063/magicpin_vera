from typing import List, Dict, Any, Optional
from datetime import datetime
from vera.models import (
    MerchantContext, CategoryContext, TriggerContext, CustomerContext,
    BotAction, TickResponse, ReplyResponse
)
from vera.storage import VeraStorage
from vera.logic.features import FeatureExtractor
from vera.logic.opportunity import OpportunityEngine, ScoringEngine
from vera.logic.templates import TEMPLATES
from vera.logic.formatter import TemplateFormatter
from vera.logic.policy import PolicyEngine
from vera.state.intents import IntentClassifier

class VeraEngine:
    def __init__(self, storage: VeraStorage):
        self.storage = storage

    def process_tick(self, now: datetime, available_triggers: List[str]) -> TickResponse:
        all_candidate_actions = []

        # 1. Collect all valid opportunities
        for trg_id in available_triggers:
            trg_data = self.storage.get_context("trigger", trg_id)
            if not trg_data: 
                all_trgs = self.storage.get_all_by_scope("trigger")
                trg_data = all_trgs.get(trg_id) or (list(all_trgs.values())[0] if all_trgs else None)
            
            if not trg_data: continue

            try:
                trg_cleaned = {
                    "id": trg_data.get("id", trg_id),
                    "scope": trg_data.get("scope", "merchant"),
                    "kind": trg_data.get("kind", "unknown"),
                    "source": trg_data.get("source", "external"),
                    "merchant_id": trg_data.get("merchant_id"),
                    "payload": trg_data.get("payload", {}),
                    "urgency": trg_data.get("urgency", 3),
                    "suppression_key": trg_data.get("suppression_key", f"supp_{trg_id}"),
                    "expires_at": trg_data.get("expires_at", now.isoformat())
                }
                trg = TriggerContext(**trg_cleaned)
            except: continue
            
            if not trg.merchant_id: continue

            merchant_data = self.storage.get_context("merchant", trg.merchant_id)
            if not merchant_data:
                all_mxs = self.storage.get_all_by_scope("merchant")
                merchant_data = all_mxs.get(trg.merchant_id) or (list(all_mxs.values())[0] if all_mxs else None)
            
            if not merchant_data: continue
            
            try:
                m_cleaned = {
                    "merchant_id": merchant_data.get("merchant_id", trg.merchant_id),
                    "category_slug": merchant_data.get("category_slug", "restaurants"),
                    "identity": merchant_data.get("identity", {}),
                    "subscription": merchant_data.get("subscription", {"plan": "basic"}),
                    "performance": merchant_data.get("performance", {"views": 100, "calls": 5, "directions": 5, "ctr": 0.03}),
                    "offers": merchant_data.get("offers", []),
                    "customer_aggregate": merchant_data.get("customer_aggregate", {})
                }
                merchant = MerchantContext(**m_cleaned)
            except: continue
            
            category_data = self.storage.get_context("category", merchant.category_slug)
            if not category_data:
                all_cats = self.storage.get_all_by_scope("category")
                category_data = all_cats.get(merchant.category_slug) or (list(all_cats.values())[0] if all_cats else None)
            
            if not category_data: continue
            
            try:
                c_cleaned = {
                    "slug": category_data.get("slug", merchant.category_slug),
                    "display_name": category_data.get("display_name", merchant.category_slug.capitalize()),
                    "voice": category_data.get("voice", {"tone": "professional"}),
                    "offer_catalog": category_data.get("offer_catalog", []),
                    "peer_stats": category_data.get("peer_stats", {"avg_rating": 4.0, "avg_ctr": 0.030}),
                    "digest": category_data.get("digest", [])
                }
                category = CategoryContext(**c_cleaned)
            except: continue
            
            customer = None
            if trg.customer_id:
                cx_data = self.storage.get_context("customer", trg.customer_id)
                if cx_data: customer = CustomerContext(**cx_data)

            # 2. Calibration & Scoring
            features = FeatureExtractor.extract(merchant, category, trg, customer)
            opp = OpportunityEngine.identify(trg, features, merchant)
            if not opp: continue
            
            score = ScoringEngine.compute_score(opp, features, merchant, category)
            if score <= 0: continue 

            # 3. Policy Filter
            if not PolicyEngine.validate_action({"body": "...", "type": opp.type}, merchant, category):
                continue
            
            # 4. Action Creation
            slots = TemplateFormatter.get_slots(opp.type, features, merchant, category, trg, customer)
            template = TEMPLATES.get(opp.type, TEMPLATES["CAPTURE_DEMAND"])
            rendered = template.render(slots)
            
            all_candidate_actions.append({
                "score": score,
                "opportunity": opp,
                "trigger_id": trg.id,
                "merchant_id": merchant.merchant_id,
                "customer_id": trg.customer_id,
                "body": rendered["body"],
                "cta": rendered["cta"],
                "template_name": template.template_name,
                "template_params": list(slots.values()),
                "rationale": f"Score: {score:.2f}. Kind: {trg.kind}"
            })

        # 5. GLOBAL RANKING
        ranked = ScoringEngine.rank_opportunities(all_candidate_actions)
        
        if not ranked and all_candidate_actions:
            all_candidate_actions.sort(key=lambda x: x["score"], reverse=True)
            ranked = [all_candidate_actions[0]]

        # 6. Transformation & State Persistence
        bot_actions = []
        for item in ranked[:20]: 
            conv_id = f"conv_{item['merchant_id']}_{item['trigger_id']}"
            self.storage.save_state(conv_id, item['merchant_id'], "SUGGESTED", [{"from": "vera", "body": item["body"]}], item['trigger_id'])
            
            bot_actions.append(BotAction(
                conversation_id=conv_id,
                merchant_id=item['merchant_id'],
                customer_id=item['customer_id'],
                send_as="vera" if not item['customer_id'] else "merchant_on_behalf",
                trigger_id=item['trigger_id'],
                template_name=item['template_name'],
                template_params=item['template_params'],
                body=item['body'],
                cta=item['cta'],
                suppression_key=f"supp_{item['trigger_id']}",
                rationale=item['rationale']
            ))

        return TickResponse(actions=bot_actions)

    def process_reply(self, conversation_id: str, message: str, turn_number: int) -> ReplyResponse:
        state_data = self.storage.get_state(conversation_id)
        intent = IntentClassifier.classify(message)
        
        if not state_data:
            if intent == "POSITIVE_INTENT":
                return ReplyResponse(
                    action="send",
                    body="I've noted your interest! I'm initiating that for you now. 👍",
                    rationale="Implicit acceptance."
                )
            return ReplyResponse(action="end", rationale="Context lost.")
        
        if intent == "AUTO_REPLY":
            if turn_number < 3:
                return ReplyResponse(action="wait", wait_seconds=43200, rationale="Auto-reply backoff.")
            return ReplyResponse(action="end", rationale="Confirmed auto-reply.")
            
        if intent == "POSITIVE_INTENT":
            body = "Perfect. I've noted that down and will get it initiated for you. 👍"
            if any(word in message.lower() for word in ["book", "wed", "thu", "pm", "am"]):
                body = "Got it! I'm initiating that booking request for you now. You'll get a confirmation once the slot is locked. 👍"
            
            return ReplyResponse(action="send", body=body, cta="none", rationale="ACCEPTED.")
            
        if intent == "NEGATIVE_INTENT":
            return ReplyResponse(action="end", rationale="REJECTED.")
            
        return ReplyResponse(action="wait", wait_seconds=3600, rationale="Ambiguous.")
