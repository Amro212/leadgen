# Leadgen MVP — Step‑by‑Step Build Plan (Granular, Testable Tasks)

> Each task is tiny, focused, and ends with a concrete test. Execute **one task at a time**, commit, and verify before moving on.

---

## Phase 0 — Repo & Environment

### T00 — Initialize repo
**Goal:** Version control ready.
- **Start:** Empty folder.
- **Actions:** `git init`; create `.gitignore` for Python (`__pycache__/`, `.env`, `.venv/`).
- **End/Test:** `git status` clean; first commit present.

### T01 — Create project skeleton
**Goal:** Folder/file tree exists per architecture (empty files OK).
- **Start:** Repo initialized.
- **Actions:** Create directories & empty files exactly as defined in architecture.
- **End/Test:** `tree` (or file explorer) matches structure.

### T02 — Python env & deps
**Goal:** Reproducible environment.
- **Start:** Skeleton exists.
- **Actions:** Create `.venv`; add `requirements.txt` (requests, beautifulsoup4, pandas, python-dotenv, loguru, pydantic, schedule). Optional: openai.
- **End/Test:** `pip install -r requirements.txt` succeeds.

### T03 — Settings loader
**Goal:** Centralized config.
- **Start:** `config/settings.py` empty.
- **Actions:** Implement `.env` loading (dotenv), constants (OUTPUT_DIR), and optional API keys (read but not required).
- **End/Test:** `python -c "from config.settings import SETTINGS; print(SETTINGS.OUTPUT_DIR)"` prints default path.

### T04 — Logging baseline
**Goal:** Unified logging.
- **Start:** `utils/logging_utils.py` empty.
- **Actions:** Configure loguru logger factory (`get_logger(name)`), add console + rotating file handler under `./logs/`.
- **End/Test:** Simple script logs to console and `logs/app.log`.

---

## Phase 1 — Data Contracts & Stubs

### T05 — Lead model & types
**Goal:** Shared data shape.
- **Start:** No models.
- **Actions:** Create `Lead` pydantic model with core fields (business_name, city, website, phone, signals dict, score, tier, notes).
- **End/Test:** Import in REPL, instantiate with sample dict; validation passes.

### T06 — Base interfaces
**Goal:** Pluggable components.
- **Start:** Empty bases.
- **Actions:** `discovery/base_discovery.py` defines `DiscoverySource.fetch_leads(query, location, max_results)->list[dict]`; `enrichment/base_enrichment.py` defines `EnrichmentSource.enrich(leads)->list[dict]`.
- **End/Test:** Import interfaces; mypy/pyright type check passes (optional).

### T07 — Orchestrator skeleton
**Goal:** Runnable pipeline stub.
- **Start:** `main.py` empty.
- **Actions:** Wire empty calls: discovery → enrichment → scoring → export; each returns the input for now.
- **End/Test:** `python main.py` runs without exceptions and prints staged counts (0 OK).

---

## Phase 2 — Discovery (Free)

### T08 — Google results scraper (basic)
**Goal:** Minimal free discovery.
- **Start:** `discovery/google_scraper.py` empty.
- **Actions:** Implement simple `requests` GET to Google with query `site:yelp.com <vertical> <location>` (use `hl=en&num=10`), parse anchors with BeautifulSoup, extract business names & profile URLs (from result titles/snippets). Add polite delay.
- **End/Test:** `fetch_leads("HVAC","Milton, Ontario",10)` returns ≥5 dicts with `business_name` & `source_url`.

### T09 — Yelp profile scraper (augment)
**Goal:** Enrich discovery using public Yelp pages.
- **Start:** `discovery/yelp_scraper.py` empty.
- **Actions:** Given a Yelp biz URL, scrape name, city, phone (if visible), website link (if present). Fallbacks if elements missing.
- **End/Test:** For 3 known Yelp URLs, function returns expected fields.

### T10 — Discovery aggregator
**Goal:** Merge & dedupe discovery outputs.
- **Start:** None.
- **Actions:** In `discovery/google_scraper.py` (or new `discovery/aggregate.py`), follow top N Yelp URLs from T08 and run T09; normalize website (lowercase, strip scheme), dedupe by domain or (name+phone).
- **End/Test:** Aggregator returns a list of unique leads with name, city, phone?, website?.

---

## Phase 3 — Enrichment (Free)

### T11 — HTTP utils
**Goal:** Reliable requests.
- **Start:** `utils/http_utils.py` empty.
- **Actions:** Build `get(url, timeout=8)` with retry/backoff (tenacity optional; else manual); random UA; 1–2s sleep between domains.
- **End/Test:** Fetch 3 sites; responses 200; retry works on 500/timeout.

### T12 — Website scraper
**Goal:** Extract core signals.
- **Start:** `enrichment/website_scraper.py` empty.
- **Actions:** For each lead with website: fetch homepage + `/contact`; parse for: `mailto:` emails, presence of `<form>`, words: "Booking|Appointment", "Emergency|24/7", "Financing"; detect HTTPS via URL scheme; collect `tech_signals` (basic heuristics: meta generator contains WordPress/Wix/Squarespace).
- **End/Test:** Run on 3 real sites; returns booleans and lists as expected.

### T13 — Enrichment pipeline
**Goal:** Apply to all leads.
- **Start:** None.
- **Actions:** Implement `EnrichmentSource.enrich(leads)` that maps T12 over inputs; preserves unknowns with `None`; adds `notes` for errors.
- **End/Test:** 10 input leads → ≥8 enriched; errors logged; structure consistent.

---

## Phase 4 — Scoring

### T14 — Scoring engine
**Goal:** Deterministic ranking.
- **Start:** `scoring/scoring_engine.py` empty.
- **Actions:** Implement `score_lead(lead)` using weights from `config/weights.py`; add `tier` mapping (A≥65, B≥45).
- **End/Test:** Unit test on crafted leads yields expected scores/tiers.

### T15 — Score all
**Goal:** Batch scoring.
- **Start:** None.
- **Actions:** `score_all(leads)` loops through, mutates/returns list; logs distribution counts.
- **End/Test:** Run on sample; prints A/B/C counts.

---

## Phase 5 — Export & Reports

### T16 — Export to CSV
**Goal:** Client deliverable.
- **Start:** `storage/exporter.py` empty.
- **Actions:** Convert list→DataFrame; write `./output/<vertical>_<region>_<date>.csv`; include columns: name, city, phone, website, emails, booking/contact flags, tech_signals, score, tier, notes.
- **End/Test:** File exists; openable; correct columns; row count matches inputs.

### T17 — Summary report
**Goal:** Human-friendly overview.
- **Start:** `storage/reports.py` empty.
- **Actions:** Compute counts by tier, % without booking, avg rating (if available), top 3 keywords; write `summary_<same-stem>.md`.
- **End/Test:** Markdown generated with non-empty stats.

---

## Phase 6 — Outreach (Optional Free Tier)

### T18 — OpenAI connector (guarded)
**Goal:** Pluggable LLM usage.
- **Start:** `outreach/generator.py` empty.
- **Actions:** If `OPENAI_API_KEY` present: for each lead produce `personalization_snippet` (<=220 chars) + two subject lines + short/warm emails using minimal prompt. If key absent: return placeholders.
- **End/Test:** With API key: 3 leads → 3 texts each. Without key: placeholders returned, no crash.

---

## Phase 7 — Orchestration & CLI

### T19 — Wire up `main.py`
**Goal:** End-to-end run.
- **Start:** Stubs exist.
- **Actions:** Parse CLI args (`--vertical`, `--region`, `--max`); log start/end; call discovery→enrichment→scoring→(outreach?)→export→summary.
- **End/Test:** `python main.py --vertical HVAC --region "Milton, Ontario" --max 25` completes; artifacts in `/output`.

### T20 — Minimal scheduler
**Goal:** Automated runs.
- **Start:** `automation/scheduler.py` empty.
- **Actions:** Use `schedule` to run `main.run_job()` daily/weekly; `if __name__ == "__main__"` loop with `run_pending()`.
- **End/Test:** Start script; it triggers dry-run every minute (for test), logs execution.

---

## Phase 8 — Quality & Resilience

### T21 — Input validation
**Goal:** Predictable behavior.
- **Start:** None.
- **Actions:** Validate CLI args; sanitize location string; clamp `max` to sensible limit.
- **End/Test:** Invalid args produce helpful error and non-zero exit.

### T22 — Rate-limit & politeness
**Goal:** Be a good citizen.
- **Start:** `utils/http_utils.py` present.
- **Actions:** Add per-domain sleep; exponential backoff; cap concurrent fetches (sequential for MVP).
- **End/Test:** Logs show delayed pacing; no rapid-fire bursts.

### T23 — Error handling & retries
**Goal:** Robustness.
- **Start:** None.
- **Actions:** Wrap discovery/enrichment steps with try/except; collect `notes` on failures; continue processing.
- **End/Test:** Introduce a bad URL; pipeline completes and notes the failure.

### T24 — Sample data & unit tests
**Goal:** Guardrails.
- **Start:** No tests.
- **Actions:** Add a `tests/` folder with unit tests for scoring, text utils, and a tiny HTML fixture for parser.
- **End/Test:** `pytest -q` green.

---

## Phase 9 — API Integration Sprint (7 Days, Real Data)

> **Available APIs:** Yelp (500/day), Google Places (2,000/mo), Hunter.io (25/mo), Tavily (4,000/mo), Gemini (1,500/day)

### Phase 9A — Discovery APIs (Days 1–3)

#### T25 — Integrate Yelp Fusion API (Primary Discovery)
**Goal:** Replace sample data with real businesses.
- **Start:** YELP_API_KEY in `.env`.
- **Actions:**
  - Create `discovery/yelp_fusion_api.py` implementing `DiscoverySource` interface
  - Call `/businesses/search` endpoint with term + location + radius
  - Map response to lead dict: name, city, region, phone, website, address, rating
  - Implement rate limiter: max 500/day, track in `storage/api_usage.json`
  - Add logging: show daily quota remaining after each call
  - Fallback: if quota exceeded, switch to Google Places or sample data
- **End/Test:** 
  - `python main.py --vertical HVAC --region "Milton, Ontario" --max 50`
  - Returns 50 real Yelp businesses (not sample data)
  - CSV contains actual phone numbers, websites, ratings
  - `storage/api_usage.json` shows: `{"yelp": {"daily": 50, "last_reset": "2025-10-27"}}`

#### T26 — Integrate Google Places API (Secondary Discovery)
**Goal:** Fallback discovery + enhanced attributes.
- **Start:** GOOGLE_API_KEY in `.env`.
- **Actions:**
  - Create `discovery/google_places_api.py` implementing `DiscoverySource` interface
  - Call Text Search API to find businesses, then Details API for full data
  - Extract: name, address, phone, website, opening_hours, rating, reviews_url
  - Implement quota tracker: max 2,000/month (~67/day), warn when approaching limit
  - Use only if: (a) Yelp quota exceeded OR (b) `--use-google-places` flag
  - Cache results to avoid duplicate calls
- **End/Test:**
  - Run when Yelp exhausted: `python main.py --vertical Plumbing --region "Toronto, ON" --max 50`
  - Google Places fills remaining leads
  - CSV shows Google-sourced leads with different attributes than Yelp
  - `storage/api_usage.json` shows: `{"google_places": {"monthly": 50, "last_reset": "2025-10"}}`

#### T26.5 — Discovery Aggregator Enhancement (Fallback Chain)
**Goal:** Intelligent API selection.
- **Start:** Both Yelp and Google implementations complete.
- **Actions:**
  - Modify `discovery/aggregator.py` to check quotas before calling each API
  - Priority order: Yelp → Google Places → SerpAPI → Sample Data
  - Log which API provided each lead (add `discovery_source` field)
  - Skip to next API if current exceeds quota
- **End/Test:**
  - Run large batch: `python main.py --vertical HVAC --region "Toronto, ON" --max 150`
  - First 100 from Yelp, next 50 from Google, no sample data
  - CSV column shows: "yelp_api", "google_places_api", "google_places_api", ...

---

### Phase 9B — Enrichment APIs (Days 4–5)

#### T27 — Integrate Hunter.io Email Finder (High-Value Leads Only)
**Goal:** Verify emails on Tier A leads.
- **Start:** HUNTER_API_KEY in `.env`.
- **Actions:**
  - Create `enrichment/hunter_email_finder.py`
  - Call `hunter.io/v2/domain-search` with domain from lead website
  - Extract primary email, all emails, confidence score
  - **Only run for:** Tier A leads (score ≥ 65)
  - Implement quota tracker: max 25/month, warn at 20/25
  - Add to enrichment pipeline as optional enhancement step
  - Store: `lead['emails_verified']` and `lead['email_confidence']`
- **End/Test:**
  - Run enrichment on 10 leads, 5 Tier A + 5 Tier B/C
  - Only Tier A leads get Hunter queries
  - CSV shows verified emails for A-tier, empty for others
  - `storage/api_usage.json` shows: `{"hunter": {"monthly": 5, "last_reset": "2025-10"}}`

#### T28 — Integrate Tavily Deep Research (A-Tier Intelligence)
**Goal:** Add verification + market insights for top leads.
- **Start:** TAVILY_API_KEY in `.env`.
- **Actions:**
  - Create `enrichment/tavily_researcher.py`
  - Call `/search` endpoint with query: `"{business_name}" {city} reviews reputation`
  - Extract: recent mentions, verified status, customer sentiment, market trends
  - **Only run for:** Tier A leads (score ≥ 75)
  - Implement quota tracker: max 4,000/month, budget ~130/day
  - Add to enrichment pipeline; runs after Hunter
  - Store: `lead['tavily_research']` dict with sources, snippets, sentiment
- **End/Test:**
  - Run enrichment; Tier A leads show Tavily data
  - CSV includes new column: `ai_research_summary` (truncated to 200 chars)
  - Example: "✓ Verified active. Recent positive reviews. Uses modern booking tech."
  - `storage/api_usage.json` shows: `{"tavily": {"monthly": 10, "last_reset": "2025-10"}}`

---

### Phase 6 (Moved) — AI Outreach (Day 6)

#### T18 — Gemini Outreach Generator (Personalized Emails)
**Goal:** AI-generated personalized outreach.
- **Start:** GEMINI_API_KEY in `.env`.
- **Actions:**
  - Create `outreach/gemini_generator.py`
  - Call Gemini API with prompt: business context + missing features + Tavily insights
  - Generate: personalized email subject + body (≤150 words, warm tone)
  - **Only run for:** Tier A/B leads (score ≥ 45)
  - Implement quota tracker: max 1,500/day, use ~50/day for MVP
  - Add to export stage; append to CSV as new columns
  - Store: `lead['outreach_subject']` and `lead['outreach_body']`
- **End/Test:**
  - Export run includes outreach columns
  - CSV shows personalized emails for A/B leads
  - Example: "Subject: Help ABC Plumbing add online booking. Body: We noticed..."
  - `storage/api_usage.json` shows: `{"gemini": {"daily": 20, "last_reset": "2025-10-27"}}`

---

### Phase 8 (Enhanced) — Rate Limit Management & Monitoring

#### T29 — API Usage Tracker & Dashboard
**Goal:** Real-time quota visibility.
- **Start:** None.
- **Actions:**
  - Create `storage/api_usage.py` with `APIUsageTracker` class
  - Tracks daily/monthly quotas; auto-resets on period boundaries
  - Saves state to `output/api_usage.json` after each call
  - Implement `get_status()` method returning quota summary
  - Integrate into main.py logging: print before/after pipeline
- **End/Test:**
  - Run pipeline; logs show: "📊 API Usage: Yelp 50/500 | Google 10/2000 | Hunter 5/25 | Tavily 10/4000 | Gemini 20/1500"
  - `output/api_usage.json` persists across runs
  - Next run shows updated counts

#### T30 — Alert System for Quota Warnings
**Goal:** Prevent unexpected API exhaustion.
- **Start:** API usage tracker exists.
- **Actions:**
  - Add threshold alerts: warn at 80% of monthly quota, 90% of daily
  - Log warnings to console + `logs/app.log`
  - Example: "⚠️ Hunter.io: 20/25 used (80%). Only 5 searches remaining this month."
  - Optional: send email alert if configured (for future)
- **End/Test:**
  - Simulate high usage; alerts appear
  - No silent failures due to quota exhaustion

---

## Done Criteria (MVP Complete)

### Phase 1–5 (Completed ✅)
- Discovery, enrichment, scoring, export all functional
- CSV + markdown summary generated
- A/B/C tiers assigned
- Logs readable; error handling in place

### Phase 9A–9B (7-Day API Sprint)
- **Day 1 (T25):** `python main.py --vertical HVAC --region "Milton, Ontario" --max 50` returns 50 real Yelp businesses
- **Day 2 (T26):** Google Places fallback working; handles quota switching
- **Day 3 (T26.5):** Aggregator logs discovery source for each lead
- **Day 4 (T27):** Tier A leads have verified emails from Hunter.io
- **Day 5 (T28):** Tier A leads have Tavily research + sentiment
- **Day 6 (T18):** CSV includes AI-generated outreach emails for A/B leads
- **Day 7 (T29–T30):** API usage tracked + quota warnings logged

### Final Output
```csv
lead_id,business_name,phone,website,email,score,tier,discovery_source,emails_verified,ai_research_summary,outreach_subject,outreach_body
...
```

- All data real (Yelp/Google, not sample)
- All top-tier leads enriched (Hunter.io + Tavily)
- All outreach personalized (Gemini)
- All API quotas tracked + visible