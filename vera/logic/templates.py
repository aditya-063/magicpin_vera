from typing import Dict, Any, List

class MessageTemplate:
    def __init__(self, body_fmt: str, cta_fmt: str, template_name: str):
        self.body_fmt = body_fmt
        self.cta_fmt = cta_fmt
        self.template_name = template_name

    def render(self, slots: Dict[str, str]) -> Dict[str, str]:
        return {
            "body": self.body_fmt.format(**slots),
            "cta": self.cta_fmt.format(**slots)
        }

# Mandatory structure: PROOF + CONTEXT + GAP + ACTION
TEMPLATES = {
    "CAPTURE_DEMAND": MessageTemplate(
        body_fmt="{proof} people nearby searched '{service}' today. Your profile views are active but your conversion is {gap_pct}% below peers. Start a {offer} campaign to capture this demand?",
        cta_fmt="Start {offer} campaign?",
        template_name="vera_capture_demand_v1"
    ),
    "FIX_CONVERSION": MessageTemplate(
        body_fmt="Your listing has {proof} views this month. However, calls are {gap_pct}% lower than similar {category} in {locality}. Add {offer} to your profile to fix this conversion gap?",
        cta_fmt="Add {offer} to profile?",
        template_name="vera_fix_conversion_v1"
    ),
    "REACTIVATE_CUSTOMERS": MessageTemplate(
        body_fmt="Hi {cx_name}, {mx_name} here. It's been {months} months since your last visit. We have {slots} slots ready for your recall checkup. {offer} included. Reply 1 for {slot1}, 2 for {slot2}.",
        cta_fmt="Reply 1 or 2",
        template_name="merchant_recall_reminder_v1"
    ),
    "BUILD_TRUST": MessageTemplate(
        body_fmt="{source} update: {proof} reduction in {metric} found for {cohort}. Highly relevant for your practice. Want me to draft a {action} for your patients? — {source_ref}",
        cta_fmt="Draft {action}?",
        template_name="vera_build_trust_v1"
    ),
    "SEASONAL_PUSH": MessageTemplate(
        body_fmt="{event} is coming up in {days} days. {proof}% of local {category} usually see a spike in {service}. Should I launch your {offer} special today?",
        cta_fmt="Launch {offer} special?",
        template_name="vera_seasonal_v1"
    )
}
