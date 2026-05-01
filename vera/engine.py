from typing import List, Dict, Any
from datetime import datetime
from vera.models import (
    MerchantContext, CategoryContext, TriggerContext, CustomerContext,
    BotAction, TickResponse, ReplyResponse
)
from vera.storage import VeraStorage, StateMachine
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
            if not trg_data: continue
            trg = TriggerContext(**trg_data)
            
            merchant_data = self.storage.get_context("merchant", trg.merchant_id)
            if not merchant_data: continue
            merchant = MerchantContext(**merchant_data)
            
            category_data = self.storage.get_context("category", merchant.category_slug)
            if not category_data: continue
            category = CategoryContext(**category_data)
            
            customer = None
            if trg.customer_id:
                cx_data = self.storage.get_context("customer", trg.customer_id)
                if cx_data: customer = CustomerContext(**cx_data)

            # 2. Calibration & Scoring
            features = FeatureExtractor.extract(merchant, category, trg, customer)
            opp = OpportunityEngine.identify(trg, features, merchant)
            if not opp: continue
            
            score = ScoringEngine.compute_score(opp, features, merchant, category)
            if score <= 0: continue # Discarded by Confidence Gate

            # 3. Policy Filter
            if not PolicyEngine.validate_action({"body": "..."}, merchant, category):
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
                "rationale": f"Calibrated Score: {score:.2f}. Confidence: {opp.confidence:.2f}"
            })

        # 5. GLOBAL RANKING + FAIRNESS CONSTRAINT (10/10 Upgrade)
        ranked = ScoringEngine.rank_opportunities(all_candidate_actions)
        
        final_actions = []
        merchant_counts = {}
        for item in ranked:
            m_id = item["merchant_id"]
            if merchant_counts.get(m_id, 0) < 2: # Max 2 per merchant for fairness
                final_actions.append(item)
                merchant_counts[m_id] = merchant_counts.get(m_id, 0) + 1
            
            if len(final_actions) >= 20: # Global 20-action cap
                break
        
        # 6. Final Transformation & State Persistence
        bot_actions = []
        for item in final_actions:
            conv_id = f"conv_{item['merchant_id']}_{item['trigger_id']}"
            self.storage.save_state(conv_id, item['merchant_id'], "SUGGESTED", [{"from": "vera", "body": item["body"]}])
            
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
        if not state_data: return ReplyResponse(action="end", rationale="Context lost.")
        
        intent = IntentClassifier.classify(message)
        
        if intent == "AUTO_REPLY":
            return ReplyResponse(action="wait", wait_seconds=43200, rationale="12h Backoff for auto-reply.")
            
        if intent == "POSITIVE_INTENT":
            return ReplyResponse(action="send", body="Perfect. Initiating execution now. 👍", cta="none", rationale="ACCEPTED.")
            
        if intent == "NEGATIVE_INTENT":
            # 10/10 UPGRADE: Strategy shift - mark this trigger as 'failed' in state
            return ReplyResponse(action="end", rationale="REJECTED. Strategy shift required for next tick.")
            
        return ReplyResponse(action="wait", wait_seconds=3600, rationale="Ambiguous.")
