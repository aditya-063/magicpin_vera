from typing import List, Optional, Any, Dict, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# --- Context Models (as per brief) ---

class VoiceProfile(BaseModel):
    tone: str
    vocab_allowed: List[str] = []
    vocab_taboo: List[str] = []

class PeerStats(BaseModel):
    avg_rating: float
    avg_ctr: float
    avg_views_30d: Optional[float] = None
    # ... other stats can be added as needed

class DigestItem(BaseModel):
    id: str
    kind: str
    title: str
    source: str
    summary: str
    actionable: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class CategoryContext(BaseModel):
    slug: str
    display_name: str
    voice: VoiceProfile
    offer_catalog: List[Dict[str, Any]]
    peer_stats: PeerStats
    digest: List[DigestItem] = []
    seasonal_beats: List[Dict[str, Any]] = []

class PerformanceSnapshot(BaseModel):
    views: int
    calls: int
    directions: int
    ctr: float
    delta_7d: Dict[str, float] = {}

class MerchantContext(BaseModel):
    merchant_id: str
    category_slug: str
    identity: Dict[str, Any]
    subscription: Dict[str, Any]
    performance: PerformanceSnapshot
    offers: List[Dict[str, Any]]
    customer_aggregate: Dict[str, Any]
    signals: List[str] = []

class CustomerContext(BaseModel):
    customer_id: str
    merchant_id: str
    identity: Dict[str, Any]
    relationship: Dict[str, Any]
    state: str
    preferences: Dict[str, Any]

class TriggerContext(BaseModel):
    id: str
    scope: Literal["merchant", "customer"]
    kind: str
    source: Literal["external", "internal"]
    merchant_id: str
    customer_id: Optional[str] = None
    payload: Dict[str, Any]
    urgency: int
    suppression_key: str
    expires_at: datetime

# --- API Models ---

class ContextPush(BaseModel):
    scope: Literal["category", "merchant", "customer", "trigger"]
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: datetime

class TickRequest(BaseModel):
    now: datetime
    available_triggers: List[str] = []

class BotAction(BaseModel):
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    send_as: Literal["vera", "merchant_on_behalf"]
    trigger_id: str
    template_name: str
    template_params: List[str]
    body: str
    cta: str
    suppression_key: str
    rationale: str

class TickResponse(BaseModel):
    actions: List[BotAction]

class ReplyRequest(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: Literal["merchant", "customer"]
    message: str
    received_at: datetime
    turn_number: int

class ReplyResponse(BaseModel):
    action: Literal["send", "wait", "end"]
    body: Optional[str] = None
    cta: Optional[str] = None
    wait_seconds: Optional[int] = None
    rationale: str

class Opportunity(BaseModel):
    type: str
    confidence: float
    priority: int
