import sqlite3
import json
from typing import Optional, Dict, Any, List
from vera.models import MerchantContext, CategoryContext, TriggerContext, CustomerContext

class VeraStorage:
    def __init__(self, db_path: str = "vera.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contexts (
                    scope TEXT,
                    context_id TEXT,
                    version INTEGER,
                    payload TEXT,
                    PRIMARY KEY (scope, context_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS states (
                    conversation_id TEXT PRIMARY KEY,
                    merchant_id TEXT,
                    customer_id TEXT,
                    current_state TEXT,
                    last_trigger_id TEXT,
                    history TEXT
                )
            """)

    def save_context(self, scope: str, context_id: str, version: int, payload: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            # Check version
            cur = conn.execute("SELECT version FROM contexts WHERE scope = ? AND context_id = ?", (scope, context_id)).fetchone()
            if cur and cur[0] >= version:
                return False
            
            conn.execute("""
                INSERT OR REPLACE INTO contexts (scope, context_id, version, payload)
                VALUES (?, ?, ?, ?)
            """, (scope, context_id, version, json.dumps(payload)))
            return True

    def get_context(self, scope: str, context_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT payload FROM contexts WHERE scope = ? AND context_id = ?", (scope, context_id)).fetchone()
            return json.loads(row[0]) if row else None

    def get_all_by_scope(self, scope: str) -> Dict[str, Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT context_id, payload FROM contexts WHERE scope = ?", (scope,)).fetchall()
            return {row[0]: json.loads(row[1]) for row in rows}

    def save_state(self, conversation_id: str, merchant_id: str, state: str, history: List[Dict[str, Any]], trigger_id: str = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO states (conversation_id, merchant_id, current_state, last_trigger_id, history)
                VALUES (?, ?, ?, ?, ?)
            """, (conversation_id, merchant_id, state, trigger_id, json.dumps(history)))

    def get_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM states WHERE conversation_id = ?", (conversation_id,)).fetchone()
            if row:
                return {
                    "conversation_id": row[0],
                    "merchant_id": row[1],
                    "customer_id": row[2],
                    "current_state": row[3],
                    "last_trigger_id": row[4],
                    "history": json.loads(row[5])
                }
            return None

class StateMachine:
    # IDLE -> SUGGESTED -> ACCEPTED -> EXECUTED -> FOLLOW_UP
    STATES = ["IDLE", "SUGGESTED", "ACCEPTED", "EXECUTED", "FOLLOW_UP"]

    @staticmethod
    def transition(current_state: str, intent: str) -> str:
        if current_state == "IDLE" and intent == "TICK_PROACTIVE":
            return "SUGGESTED"
        if current_state == "SUGGESTED" and intent == "POSITIVE_INTENT":
            return "ACCEPTED"
        if current_state == "ACCEPTED" and intent == "SYSTEM_EXECUTE":
            return "EXECUTED"
        if intent == "REJECTION_INTENT" or intent == "AUTO_REPLY":
            return "IDLE" # Reset or park
        return current_state
