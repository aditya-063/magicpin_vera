import requests
import time
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any

BASE_URL = "http://localhost:8080"

def log_test(name, result, detail=""):
    status = "[PASS]" if result else "[FAIL]"
    print(f"{status} {name}")
    if detail:
        print(f"      {detail}")

def run_layer_1_determinism():
    print("\n--- Layer 1: Determinism Test ---")
    # Prepare a mock tick request
    payload = {
        "now": datetime.utcnow().isoformat() + "Z",
        "available_triggers": ["trg_001"] # Assuming trg_001 exists in store
    }
    
    # We need to push context first
    requests.post(f"{BASE_URL}/v1/context", json={
        "scope": "category", "context_id": "dentists", "version": 1, "payload": {"slug": "dentists", "display_name": "Dentists", "voice": {"tone": "clinical"}, "peer_stats": {"avg_ctr": 0.03, "avg_rating": 4.5}, "offer_catalog": []}, "delivered_at": "2026-04-30T10:00:00Z"
    })
    requests.post(f"{BASE_URL}/v1/context", json={
        "scope": "merchant", "context_id": "m_001", "version": 1, "payload": {"merchant_id": "m_001", "category_slug": "dentists", "identity": {"name": "Test Clinic"}, "performance": {"views": 1000, "calls": 10, "directions": 5, "ctr": 0.015}, "offers": [], "customer_aggregate": {}, "subscription": {}}, "delivered_at": "2026-04-30T10:00:00Z"
    })
    requests.post(f"{BASE_URL}/v1/context", json={
        "scope": "trigger", "context_id": "trg_001", "version": 1, "payload": {"id": "trg_001", "scope": "merchant", "kind": "perf_dip", "source": "external", "merchant_id": "m_001", "urgency": 5, "payload": {"search_volume": 200}, "suppression_key": "s1", "expires_at": "2026-05-30T10:00:00Z"}, "delivered_at": "2026-04-30T10:00:00Z"
    })

    outputs = []
    for i in range(10):
        resp = requests.post(f"{BASE_URL}/v1/tick", json=payload)
        outputs.append(resp.text)
        time.sleep(0.1)
    
    is_stable = all(o == outputs[0] for o in outputs)
    log_test("Deterministic Output", is_stable, f"Hashes match across 10 runs: {hashlib.sha256(outputs[0].encode()).hexdigest()[:10]}")
    return is_stable

def run_layer_3_scenario_tests():
    print("\n--- Layer 3: Scenario Tests ---")
    # Scenario: High Demand + Low Conv
    requests.post(f"{BASE_URL}/v1/context", json={
        "scope": "trigger", "context_id": "trg_high_demand", "version": 1, "payload": {"id": "trg_high_demand", "scope": "merchant", "kind": "perf_dip", "source": "external", "merchant_id": "m_001", "urgency": 5, "payload": {"search_volume": 500}, "suppression_key": "s2", "expires_at": "2026-05-30T10:00:00Z"}, "delivered_at": "2026-04-30T10:00:00Z"
    })
    resp = requests.post(f"{BASE_URL}/v1/tick", json={"now": "2026-04-30T10:00:00Z", "available_triggers": ["trg_high_demand"]})
    data = resp.json()
    has_action = len(data["actions"]) > 0
    if has_action:
        body = data["actions"][0]["body"]
        log_test("High Demand Logic", "searched" in body.lower() and "~" in body, f"Body: {body[:60]}...")
    else:
        log_test("High Demand Logic", False, "No action returned for high demand")

def run_layer_5_tick_fairness():
    print("\n--- Layer 5: Tick Engine Fairness ---")
    # Setup 3 merchants, each with 3 triggers
    for m_idx in range(3):
        m_id = f"m_fair_{m_idx}"
        requests.post(f"{BASE_URL}/v1/context", json={
            "scope": "merchant", "context_id": m_id, "version": 1, "payload": {"merchant_id": m_id, "category_slug": "dentists", "identity": {"name": f"Clinic {m_idx}"}, "performance": {"views": 1000, "calls": 10, "directions": 5, "ctr": 0.015}, "offers": [], "customer_aggregate": {}, "subscription": {}}, "delivered_at": "2026-04-30T10:00:00Z"
        })
        for t_idx in range(3):
            t_id = f"trg_{m_idx}_{t_idx}"
            requests.post(f"{BASE_URL}/v1/context", json={
                "scope": "trigger", "context_id": t_id, "version": 1, "payload": {"id": t_id, "scope": "merchant", "kind": "perf_dip", "source": "external", "merchant_id": m_id, "urgency": 5, "payload": {"search_volume": 200}, "suppression_key": t_id, "expires_at": "2026-05-30T10:00:00Z"}, "delivered_at": "2026-04-30T10:00:00Z"
            })
    
    all_trgs = [f"trg_{m}_{t}" for m in range(3) for t in range(3)]
    resp = requests.post(f"{BASE_URL}/v1/tick", json={"now": "2026-04-30T10:00:00Z", "available_triggers": all_trgs})
    actions = resp.json()["actions"]
    
    m_counts = {}
    for a in actions:
        m_id = a["merchant_id"]
        m_counts[m_id] = m_counts.get(m_id, 0) + 1
    
    is_fair = all(count <= 2 for count in m_counts.values())
    log_test("Fairness Constraint (Max 2/merchant)", is_fair, f"Merchant distribution: {m_counts}")

def run_layer_7_message_validation():
    print("\n--- Layer 7: Message Validation ---")
    resp = requests.post(f"{BASE_URL}/v1/tick", json={"now": "2026-04-30T10:00:00Z", "available_triggers": ["trg_0_0"]})
    action = resp.json()["actions"][0]
    body = action["body"]
    
    # Must contain proof, gap, action
    has_proof = "~" in body or any(char.isdigit() for char in body)
    has_gap = "conversion" in body.lower() or "below" in body.lower()
    has_cta = "?" in body or "?" in action["cta"]
    
    log_test("Message Framework (PROOF+GAP+ACTION)", has_proof and has_gap and has_cta, f"Body: {body[:60]}...")

def run_layer_9_chaos_resistance():
    print("\n--- Layer 9: Chaos Resistance ---")
    # Empty merchant
    requests.post(f"{BASE_URL}/v1/context", json={
        "scope": "merchant", "context_id": "m_empty", "version": 1, "payload": {"merchant_id": "m_empty", "category_slug": "dentists"}, "delivered_at": "2026-04-30T10:00:00Z"
    })
    requests.post(f"{BASE_URL}/v1/context", json={
        "scope": "trigger", "context_id": "trg_empty", "version": 1, "payload": {"id": "trg_empty", "scope": "merchant", "kind": "perf_dip", "source": "external", "merchant_id": "m_empty", "urgency": 1, "payload": {}, "suppression_key": "empty_key", "expires_at": "2026-05-30T10:00:00Z"}, "delivered_at": "2026-04-30T10:00:00Z"
    })
    
    try:
        resp = requests.post(f"{BASE_URL}/v1/tick", json={"now": "2026-04-30T10:00:00Z", "available_triggers": ["trg_empty"]})
        log_test("Empty Data Resilience", resp.status_code == 200)
    except:
        log_test("Empty Data Resilience", False, "System crashed on empty merchant data")

if __name__ == "__main__":
    print("=== Vera AI Decision Engine Test Suite ===")
    try:
        requests.get(BASE_URL + "/v1/healthz")
        run_layer_1_determinism()
        run_layer_3_scenario_tests()
        run_layer_5_tick_fairness()
        run_layer_7_message_validation()
        run_layer_9_chaos_resistance()
        print("\n=== All Tests Completed ===")
    except Exception as e:
        print(f"Error connecting to server: {e}")
