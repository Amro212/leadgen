# 🧱 Lead Generation System – Project Architecture

This document describes the **full architecture** of the Lead Generation Tool built in Python. It defines the file/folder structure, purpose of each component, and how state and services connect. The structure is designed to be free or low-cost for MVP but easily extensible for paid APIs later.

---

## 📁 Folder & File Structure

```
leadgen/
│
├── main.py                      # Entry point: orchestrates the workflow end-to-end
│
├── config/
│   ├── settings.py              # Loads environment variables, constants, API keys
│   └── weights.py               # Scoring weights and tier thresholds
│
├── discovery/                   # Business discovery modules
│   ├── base_discovery.py        # Abstract base interface for all discovery sources
│   ├── google_scraper.py        # Free web scraper for Google search results
│   ├── yelp_scraper.py          # Free Yelp scraper or Yelp Fusion API
│   └── google_places_api.py     # Future upgrade: official Google Places API integration
│
├── enrichment/                  # Collects additional details from websites/APIs
│   ├── base_enrichment.py       # Interface for enrichment sources
│   ├── website_scraper.py       # Free BeautifulSoup-based enrichment
│   ├── hunter_api.py            # Paid Hunter.io API (optional)
│   └── clearbit_api.py          # Paid Clearbit enrichment (optional)
│
├── scoring/
│   └── scoring_engine.py        # Deterministic rule-based scoring system
│
├── outreach/                    # Outreach message generation (AI)
│   ├── generator.py             # Uses OpenAI (free tier) for outreach copy
│   └── templates/               # JSON prompt or email style templates
│
├── storage/
│   ├── exporter.py              # pandas → CSV or Google Sheets export
│   ├── database.py              # SQLite / Supabase connector (for persistence)
│   └── reports.py               # Generates summary stats and markdown reports
│
├── automation/
│   └── scheduler.py             # Runs periodic jobs (cron/schedule)
│
├── utils/
│   ├── logging_utils.py         # Logging configuration using Loguru
│   ├── http_utils.py            # HTTP request wrapper with retry/backoff
│   └── text_utils.py            # Regex finders, sanitizers, keyword extractors
│
├── .env                         # Local secrets (API keys, DB URLs)
├── requirements.txt             # Dependencies
└── README.md                    # Developer instructions
```

---

## 🧩 Module Responsibilities

### `main.py`
**Role:** Central orchestrator.
- Loads environment variables from `config/settings.py`
- Initializes discovery source (e.g., `GoogleScraper` or `YelpScraper`)
- Runs enrichment → scoring → outreach → export sequentially
- Handles basic logging and timing for performance

```python
# Pseudocode view
leads = discovery.fetch_leads(vertical, region)
enriched = enrichment.enrich(leads)
scored = scoring.score_all(enriched)
with_outreach = outreach.generate_emails(scored)
exporter.export_csv(with_outreach)
```

---

### `config/`
**Purpose:** Configuration & environment management.
- `settings.py`: loads `.env` vars (e.g., API keys, rate limits)
- `weights.py`: defines scoring rubric and tier thresholds

**Future upgrade:** Can be extended to load settings from Supabase or cloud secret managers.

---

### `discovery/`
**Purpose:** Locate businesses based on category and geography.

- **`base_discovery.py`**: defines abstract class `DiscoverySource` with method:
  ```python
  def fetch_leads(self, query: str, location: str, max_results: int) -> list[dict]:
  ```
- **`google_scraper.py`**: free scraper parsing Google results via `requests` + `BeautifulSoup`.
- **`yelp_scraper.py`**: calls Yelp Fusion API (free tier).
- **`google_places_api.py`**: paid upgrade for official Google Places API.

**Output:** raw leads list of dicts → `[ {"business_name": ..., "website": ..., "phone": ...}, ... ]`

---

### `enrichment/`
**Purpose:** Add context by visiting websites or using APIs.

- **`base_enrichment.py`**: defines `enrich_lead(lead: dict) -> dict`
- **`website_scraper.py`**: requests and parses website HTML for:
  - Emails (`mailto:`)
  - Booking/contact forms
  - Keywords ("Emergency", "Financing", "24/7", etc.)
  - HTTPS presence
- **`hunter_api.py` / `clearbit_api.py`**: optional paid modules (plug-in ready)

**Output:** enriched leads list → adds fields like `email`, `contact_form_present`, `supports_emergency`, etc.

---

### `scoring/`
**Purpose:** Score and tier leads.

- **`scoring_engine.py`**: simple rule-based model
  - Adds numeric `score` (0–100)
  - Assigns `tier` (A/B/C)

Scores are computed from presence/absence of signals and weighted via `config/weights.py`.

---

### `outreach/`
**Purpose:** Generate personalized outreach snippets and emails.

- **`generator.py`**:
  - Uses OpenAI free credit (gpt-4o-mini)
  - Generates short personalization, subject lines, and email drafts
  - Can skip this step in free MVP to save tokens
- **`templates/`**: stores text/email formats for different tones (short, warm, etc.)

**Output:** adds outreach fields to each lead.

---

### `storage/`
**Purpose:** Persist and export results.

- **`exporter.py`**: saves pandas DataFrame → CSV; can also write to Google Sheets API (free)
- **`database.py`**: placeholder for SQLite (local) → upgrade to Supabase (Postgres)
- **`reports.py`**: summary generation (counts by tier, averages, issues)

---

### `automation/`
**Purpose:** Handle recurring runs.

- **`scheduler.py`**: uses `schedule` or system cron to run jobs weekly.
- Future: replace with FastAPI endpoint + Celery queue for concurrent jobs.

---

### `utils/`
**Purpose:** Shared helper functions.

- `logging_utils.py`: configures `loguru` logs (console + file)
- `http_utils.py`: standardized `requests` session with retry & rate-limit decorator
- `text_utils.py`: regex for emails, normalization, keyword scanning

---

## 🧠 State Management

### Local State
During MVP phase:
- All transient state (lead lists, enriched leads, scores) is stored as **in-memory Python lists/dicts**.
- Persistent state (history, logs, outputs) stored as:
  - `/output/*.csv` files
  - `/logs/*.log` (if configured)
  - `.env` for runtime secrets

### Later (scalable version)
- Replace in-memory with SQLite or Postgres (Supabase)
- Store intermediate JSON between stages for debugging
- Add job metadata table (job_id, status, timestamp)

---

## 🔗 Service Connectivity

**1️⃣ Discovery → Enrichment**
- Discovery returns minimal business info (name, website, phone)
- Enrichment reads that data and fetches each website asynchronously (in future via aiohttp)

**2️⃣ Enrichment → Scoring**
- Enrichment adds feature flags; scoring uses those booleans to compute `score` and `tier`.

**3️⃣ Scoring → Outreach**
- Scoring outputs structured JSON → fed into GPT prompt for personalized text generation.

**4️⃣ Outreach → Storage**
- Outreach adds final fields → written to CSV or DB.

**5️⃣ Automation → Main**
- Scheduler simply calls `main.run_job()` at intervals.

---

## ☁️ Integration Flow Diagram (Conceptual)

```
+------------------+
| Discovery Source |  ← Yelp / Google Scraper / Google API
+------------------+
          |
          v
+-------------------+
| Enrichment Module |  ← Website scrape / Hunter / Clearbit
+-------------------+
          |
          v
+----------------+
| Scoring Engine |  ← Rule-based weight system
+----------------+
          |
          v
+------------------+
| Outreach (LLM)  |  ← Optional: OpenAI API
+------------------+
          |
          v
+----------------+
| Storage/Export |  ← CSV / Sheets / DB
+----------------+
          |
          v
+----------------+
| Automation     |  ← Cron / Scheduler / Cloud Run
+----------------+
```

---

## 🔐 Environment Variables (.env)
```
GOOGLE_API_KEY=
YELP_API_KEY=
HUNTER_API_KEY=
CLEARBIT_API_KEY=
OPENAI_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
OUTPUT_DIR=./output
LOG_LEVEL=INFO
```

---

## 🪶 Summary
- **Loose coupling**: each module communicates via JSON/dicts → easy to replace.
- **Plug-in architecture**: base interfaces let you add new discovery/enrichment APIs seamlessly.
- **Local-first**: runs 100 % free on your machine.
- **Upgradeable**: plug in paid APIs, DB, or cron hosts later without refactoring core logic.
- **State control**: all leads processed in memory or local CSV; upgrade to DB later.

---

✅ **Next Step**: Implement the scaffolding (`main.py`, `base_discovery.py`, etc.) so that the pipeline runs with dummy data, then gradually fill in each stage (scraper → enrichment → scoring).