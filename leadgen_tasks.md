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

## Phase 9 — Optional Free/Trial API Upgrades (Swap‑in tasks)

### T25 — Integrate Yelp Fusion API (discovery)
**Goal:** Cleaner discovery.
- **Start:** API key available.
- **Actions:** New class `YelpAPI(DiscoverySource)`; call `/businesses/search` with term+location; map to lead dict shape.
- **End/Test:** 10 results returned with name/city/phone/website.

### T26 — Integrate Google Places (trial credit)
**Goal:** Reliable discovery.
- **Start:** API key available.
- **Actions:** Class `GooglePlacesAPI(DiscoverySource)` using Text Search + Details; compose fields; respect quotas.
- **End/Test:** 10–20 results with website/phone.

### T27 — Integrate Hunter.io (emails)
**Goal:** Better email coverage.
- **Start:** API key available.
- **Actions:** `hunter_api.py` adds `find_emails(domain)`; enrich leads missing emails; cache results.
- **End/Test:** For 5 domains, at least some emails returned and attached.

---

## Done Criteria
- `python main.py --vertical HVAC --region "Milton, Ontario" --max 50` produces a CSV + summary with A/B/C tiers.
- Logs are readable; failures don’t crash the run.
- Modules are swappable via imports without changing the orchestrator.