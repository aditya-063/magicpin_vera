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
        body_fmt="{proof}. Local interest in {service} is up. However, your conversion is {gap_pct}% below peers. Should I launch your {offer} to capture this?",
        cta_fmt="Launch {offer}?",
        template_name="vera_capture_demand_v2"
    ),
    "FIX_CONVERSION": MessageTemplate(
        body_fmt="Your listing has {proof} views this month. However, calls are {gap_pct}% lower than similar {category} in {locality}. Add {offer} to your profile to fix this conversion gap?",
        cta_fmt="Add {offer} to profile?",
        template_name="vera_fix_conversion_v2"
    ),
    "REACTIVATE_CUSTOMERS": MessageTemplate(
        body_fmt="Hi {cx_name}, {mx_name} here. It's been {months} months since your last visit. We have {slots} ready for your recall checkup. {offer} included. Reply 1 for {slot1}, 2 for {slot2}.",
        cta_fmt="Reply 1 or 2",
        template_name="merchant_recall_reminder_v2"
    ),
    "BUILD_TRUST": MessageTemplate(
        body_fmt="{source} {metric}: {proof} {metric} required for your {cohort}. This is a critical {source_ref} update. Want me to draft the necessary {action} for your profile?",
        cta_fmt="Draft {action}?",
        template_name="vera_build_trust_v2"
    ),
    "SEASONAL_PUSH": MessageTemplate(
        body_fmt="{event} is today! Local {category} see a {proof}% spike in {service} during matches. Should I launch your {offer} special now?",
        cta_fmt="Launch {offer}?",
        template_name="vera_seasonal_v2"
    )
}
