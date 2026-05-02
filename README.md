# Vera Decision Engine - magicpin AI Challenge

This is the official submission for the magicpin AI Challenge. It implements a production-grade, deterministic decision engine (VERA) designed to help merchants grow through intelligent, context-aware messaging.

## 🚀 Key Features

### 1. Deterministic Decision Pipeline
Unlike generic LLM wrappers, this engine uses a structured pipeline to ensure 100% reliability and schema compliance:
*   **Feature Extraction**: Analyzes merchant performance, category voice, and customer intent.
*   **Opportunity Identification**: Maps triggers to specific business strategies (e.g., Compliance, Trust Building, Demand Capture).
*   **Prioritized Scoring**: A global ranking system that ensures high-impact opportunities (like regulation changes) are always delivered first.

### 2. Comprehensive Trigger Coverage
Fully implements logic for all 6 official trigger kinds:
*   `regulation_change`: Accurate compliance framing (e.g., DCI/FSSAI alerts).
*   `recall_due`: Customer retention through personalized reminders.
*   `perf_dip`: Recovery strategies for dipping views/calls.
*   `ipl_match_today`: Contextual engagement using local events.
*   `review_theme_emerged`: Addressing customer feedback trends.
*   `competitor_opened`: Defensive positioning strategies.

### 3. Intelligent Reply Branching
The engine manages multi-turn conversations with specific intent detection:
*   **Positive Intents**: Auto-detects booking requests and initiates fulfillment.
*   **Auto-Reply Detection**: Implements a 12-hour backoff window to handle bot-to-bot interaction gracefully.
*   **Hostile/Stop Detection**: Immediate termination to ensure merchant safety.

### 4. Bulletproof Context Recovery
Designed to handle real-world API data variability:
*   Supports deeply nested JSON payloads.
*   Implements multi-layer fallbacks for missing merchant or category metadata.
*   Ensures a "Never-Empty" response strategy through default candidate seeding.

## 🛠️ Tech Stack
*   **Core**: Python 3.11+
*   **Framework**: FastAPI (High-performance API)
*   **Storage**: SQLite with a versioned context-state model.
*   **Deployment**: Optimized for Railway/Render (Procfile & Environment-aware).

## 🏁 How to Run

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Start the server**:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8080
    ```

---
**Team**: Aditya Chaudhary
**Model**: Vera-Deterministic-Logic-v1
