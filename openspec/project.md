# Project Context

## Purpose

The **Lead Generation System** is a Python-based tool designed to automate the discovery, enrichment, scoring, and export of local business leads for B2B sales teams. The system targets small-to-medium businesses (SMBs) in specific verticals (e.g., HVAC, plumbing, landscaping) and geographic regions, identifying high-quality prospects based on their digital presence and readiness signals.

### Key Goals
- **Automate lead discovery** using free/low-cost web scraping and APIs
- **Enrich leads** with contact information, website signals, and technology indicators
- **Score and tier leads** using a deterministic rule-based system (A/B/C tiers)
- **Export actionable data** to CSV/Google Sheets for sales teams
- **Support optional AI-powered outreach** generation using OpenAI
- **Enable scalability** through modular, plug-in architecture for easy API upgrades

### Target Users
- Sales teams and agencies targeting local SMBs
- Business development professionals needing qualified leads
- Marketing teams building outbound campaigns

---

## Tech Stack

### Core Technologies
- **Python 3.10+** – Primary language
- **Pydantic 2.x** – Data validation and settings management
- **pandas** – Data manipulation and CSV export
- **Requests** – HTTP client for API calls and web scraping
- **BeautifulSoup4** – HTML parsing for website enrichment
- **Loguru** – Structured logging with rotation
- **python-dotenv** – Environment variable management
- **schedule** – Task scheduling for automated runs

### Optional/Paid Integrations
- **OpenAI API** – AI-powered outreach message generation (gpt-4o-mini)
- **Yelp Fusion API** – Business discovery (free tier)
- **Google Places API** – Enhanced discovery (trial credits)
- **Hunter.io API** – Email finding (free tier)
- **Clearbit API** – Company enrichment (future)
- **Supabase** – PostgreSQL cloud database (future upgrade from SQLite)

### Development Tools
- **pytest** – Unit testing framework
- **Git** – Version control
- **VS Code** – Recommended IDE
- **PowerShell/Bash** – Script execution

---

## Project Conventions

### Code Style

#### General Principles
- **PEP 8 compliance** – Follow Python style guide
- **Type hints** – Use for all function signatures and class attributes
- **Docstrings** – Google-style docstrings for all public functions/classes
- **Line length** – 88 characters (Black formatter default)
- **Imports** – Group into stdlib, third-party, local (separated by blank lines)

#### Naming Conventions
- **Modules/Packages**: `snake_case` (e.g., `google_scraper.py`, `base_discovery.py`)
- **Classes**: `PascalCase` (e.g., `DiscoverySource`, `Lead`)
- **Functions/Methods**: `snake_case` (e.g., `fetch_leads()`, `score_lead()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `SETTINGS`, `OUTPUT_DIR`)
- **Private members**: prefix with `_` (e.g., `_parse_html()`)

#### File Organization
- One main class per file (except utilities)
- Keep files under 300 lines when possible
- Place related functionality in module folders (e.g., `discovery/`, `enrichment/`)

### Architecture Patterns

#### 1. **Plug-in Architecture**
- All discovery and enrichment sources inherit from abstract base classes
- `DiscoverySource` defines `fetch_leads()` contract
- `EnrichmentSource` defines `enrich()` contract
- New sources can be added without modifying orchestration logic

#### 2. **Pipeline Pattern**
- `main.py` orchestrates a linear pipeline:
  - Discovery → Enrichment → Scoring → Outreach → Export
- Each stage receives data, transforms it, and passes to next stage
- Stages are loosely coupled via standard data dictionaries/models

#### 3. **Configuration Injection**
- All settings centralized in `config/settings.py`
- Uses Pydantic BaseSettings for type-safe environment loading
- Scoring weights separated into `config/weights.py` for easy tuning

#### 4. **Local-First Design**
- MVP runs entirely on local machine with in-memory state
- No database required initially (CSV-based persistence)
- Designed for easy upgrade to Supabase/PostgreSQL later

#### 5. **Error Handling Strategy**
- Fail gracefully: continue pipeline even if individual leads fail
- Collect errors in `Lead.notes` list for debugging
- Log all errors with context using Loguru
- Use retries with exponential backoff for HTTP requests

### Testing Strategy

#### Testing Approach
- **Unit tests** for isolated logic (scoring, text utils, parsers)
- **Integration tests** for pipeline stages (discovery → enrichment)
- **Fixture-based testing** using sample HTML/JSON for scrapers
- **Test coverage target**: >70% for core logic

#### Testing Guidelines
- Place tests in `tests/` directory mirroring source structure
- Use `pytest` fixtures for reusable test data
- Mock external HTTP calls using `responses` library
- Test edge cases (missing data, malformed HTML, API errors)
- Run tests before committing: `pytest -v`

#### Test File Naming
- `test_<module_name>.py` (e.g., `test_scoring_engine.py`)
- Test functions: `test_<function>_<scenario>` (e.g., `test_score_lead_high_quality`)

### Git Workflow

#### Branching Strategy
- **`main`** – Production-ready code
- **`develop`** – Integration branch (optional for larger teams)
- **Feature branches** – `feature/<task-id>-<short-description>` (e.g., `feature/T08-google-scraper`)
- **Bugfix branches** – `bugfix/<issue-description>`

#### Commit Conventions
- Use **imperative mood** (e.g., "Add Google scraper", not "Added Google scraper")
- Prefix with task ID when applicable: `[T08] Implement Google results scraper`
- Keep commits atomic (one logical change per commit)
- Write meaningful commit messages explaining **why**, not just **what**

#### Commit Message Format
```
[T##] Brief summary (50 chars or less)

- Detailed bullet points if needed
- Explain context and reasoning
- Reference related tasks or issues
```

---

## Domain Context

### Lead Generation Fundamentals

#### Target Verticals
Common industries for lead generation:
- **HVAC** – Heating, ventilation, air conditioning
- **Plumbing** – Residential and commercial plumbers
- **Landscaping** – Lawn care, tree service, hardscaping
- **Electrical** – Licensed electricians
- **Roofing** – Residential and commercial roofers
- **Home Cleaning** – Maid services, deep cleaning

#### Geographic Scope
- Primary focus: **Ontario, Canada** (initial MVP)
- City-level targeting (e.g., "Milton, Ontario", "Oakville, Ontario")
- Expandable to other Canadian provinces and US states

#### Lead Quality Signals
Indicators of a high-quality lead:
- **Weak digital presence** – Outdated website, no online booking
- **Missing contact forms** – Harder to reach = less saturated with competitors
- **No 24/7 service** – Opportunity to offer enhanced service packages
- **No financing options** – Upsell opportunity
- **HTTP instead of HTTPS** – Security gap to address
- **Outdated tech stack** – Website redesign opportunity

#### Business Model Context
- This tool serves **B2B sales teams** selling web design, digital marketing, or SaaS tools to SMBs
- Output format optimized for cold email outreach and phone sales
- Tier A leads = highest priority for immediate outreach
- Tier B leads = nurture campaigns
- Tier C leads = low priority or future follow-up

---

## Important Constraints

### Technical Constraints
1. **Rate Limiting**
   - Respect website `robots.txt` and rate limits
   - Default delay: 1.5 seconds between requests
   - Use exponential backoff for retries
   - Risk: IP blocking if too aggressive

2. **Free/Low-Cost Requirement**
   - MVP must run with zero or minimal API costs
   - Use free tiers and trial credits strategically
   - Web scraping as fallback for expensive APIs

3. **Legal/Ethical Web Scraping**
   - Only scrape publicly available data
   - Do not bypass authentication or paywalls
   - Store only business contact info (not personal data)
   - Comply with CASL (Canadian Anti-Spam Law) for outreach

4. **Performance**
   - Target: Process 25-50 leads in under 5 minutes
   - Sequential HTTP requests (no async in MVP)
   - Memory-efficient: stream large datasets, avoid loading all in RAM

5. **Local Execution**
   - Must run on developer's local machine (Windows/Mac/Linux)
   - No cloud dependencies for MVP
   - PowerShell-compatible commands for Windows users

### Business Constraints
- **Data Freshness**: Leads should be <7 days old when exported
- **Export Format**: CSV with specific columns for CRM import compatibility
- **Compliance**: GDPR/CASL-aware (only business data, opt-out support)

### Privacy & Security
- API keys stored in `.env` (never committed to Git)
- `.gitignore` configured for secrets and local data
- No storage of personal consumer data (B2B focus only)

---

## External Dependencies

### Core APIs (Optional)

#### 1. **Yelp Fusion API**
- **Purpose**: Business discovery (name, location, website, phone)
- **Free Tier**: 500 calls/day
- **Docs**: https://www.yelp.com/fusion
- **Integration**: `discovery/yelp_scraper.py`

#### 2. **Google Places API**
- **Purpose**: Enhanced business discovery with rich metadata
- **Free Tier**: $200 credit/month (~20,000 requests)
- **Docs**: https://developers.google.com/maps/documentation/places
- **Integration**: `discovery/google_places_api.py`

#### 3. **Hunter.io API**
- **Purpose**: Email discovery by domain
- **Free Tier**: 50 searches/month
- **Docs**: https://hunter.io/api-documentation
- **Integration**: `enrichment/hunter_api.py`

#### 4. **OpenAI API**
- **Purpose**: Personalized outreach email generation
- **Free Tier**: $5 trial credit (supports ~250 lead personalizations with gpt-4o-mini)
- **Docs**: https://platform.openai.com/docs
- **Integration**: `outreach/generator.py`

#### 5. **Clearbit API** (Future)
- **Purpose**: Company enrichment (employee count, tech stack, funding)
- **Free Tier**: Limited trial
- **Docs**: https://clearbit.com/docs
- **Integration**: `enrichment/clearbit_api.py`

### Infrastructure (Future Upgrades)

#### **Supabase**
- **Purpose**: PostgreSQL database + auth + storage
- **Free Tier**: 500 MB database, 2 GB bandwidth/month
- **Use Case**: Replace local CSV storage with cloud DB
- **Docs**: https://supabase.com/docs

#### **Google Sheets API**
- **Purpose**: Export leads directly to shared spreadsheets
- **Free Tier**: Unlimited (with rate limits)
- **Use Case**: Real-time collaboration for sales teams
- **Docs**: https://developers.google.com/sheets/api

### Third-Party Libraries

All dependencies are specified in `requirements.txt`:
- `requests` – HTTP client
- `beautifulsoup4` + `lxml` + `html5lib` – HTML parsing
- `pandas` – Data manipulation
- `pydantic` + `pydantic-settings` – Data validation
- `loguru` – Logging
- `schedule` – Task scheduling
- `pytest` – Testing

---

## Development Workflow

### Initial Setup
```bash
# Clone repository
git clone <repo-url>
cd leadgen

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env  # Edit with your API keys
```

### Running the Pipeline
```bash
# Basic run
python main.py --vertical HVAC --region "Milton, Ontario" --max 25

# Check output
ls ./output/  # CSV and summary files
```

### Testing
```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Task-Driven Development
- Follow `leadgen_tasks.md` for granular, testable tasks
- Execute **one task at a time**
- Commit after each completed task
- Test before moving to next task

---

## Future Roadmap

### Phase 1 (Current MVP)
- ✅ Free web scraping for discovery
- ✅ Website enrichment via BeautifulSoup
- ✅ Rule-based scoring system
- ✅ CSV export

### Phase 2 (API Upgrades)
- Integrate Yelp Fusion API
- Add Google Places API support
- Implement Hunter.io email finding

### Phase 3 (Scalability)
- Migrate to Supabase for persistence
- Add async HTTP requests (aiohttp)
- Implement job queue (Celery)
- Deploy scheduler to cloud (Railway, Render)

### Phase 4 (Advanced Features)
- Machine learning-based scoring
- Automated outreach sending (email integration)
- Multi-region campaigns
- Sales team dashboard (FastAPI + React)
