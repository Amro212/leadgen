"""
AI-Powered Query Generator - Comprehensive Multi-API Lead Generation Strategy
Uses Gemini 2.0 Flash to generate optimized queries for ALL available APIs.
Follows best practices for API orchestration and data enrichment.
"""
import json
import google.generativeai as genai
from typing import Dict, List, Optional
from config.settings import SETTINGS
from utils.logging_utils import get_logger

log = get_logger(__name__)


class QueryGenerator:
    """
    Comprehensive AI-powered query generator that orchestrates ALL available APIs.
    
    Generates optimized search strategies for:
    - Yelp Fusion API (primary discovery)
    - Google Places API (secondary discovery + enrichment)
    - SerpAPI (web search + SERP data)
    - Tavily Research (deep business intelligence)
    - Hunter.io (email discovery strategy)
    
    Input: "Acme Software is a Toronto B2B SaaS company selling project management tools..."
    Output: Comprehensive multi-API search strategy with structured parameters
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini query generator.
        
        Args:
            api_key: Gemini API key (defaults to SETTINGS.GEMINI_API_KEY)
        """
        self.api_key = api_key or SETTINGS.GEMINI_API_KEY
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Check which APIs are available
        self.available_apis = self._check_available_apis()
        
        log.info("✅ AI Query Generator initialized (Gemini 2.0 Flash)")
        log.info(f"   Available APIs: {', '.join(self.available_apis)}")
    
    def _check_available_apis(self) -> List[str]:
        """Check which APIs have keys configured."""
        available = []
        if SETTINGS.YELP_API_KEY:
            available.append("Yelp")
        if SETTINGS.GOOGLE_API_KEY:
            available.append("Google Places")
        if SETTINGS.SERPAPI_API_KEY:
            available.append("SerpAPI")
        if SETTINGS.TAVILY_API_KEY:
            available.append("Tavily")
        if SETTINGS.HUNTER_API_KEY:
            available.append("Hunter.io")
        return available
    
    def generate_search_strategy(self, company_brief: str) -> Dict:
        """
        Generate comprehensive multi-API search strategy.
        
        Uses API orchestration best practices:
        1. Primary discovery (Yelp, Google Places)
        2. Web search enrichment (SerpAPI)
        3. Deep research (Tavily)
        4. Contact discovery (Hunter.io strategy)
        
        Args:
            company_brief: 2-3 sentence description of the company and lead requirements
        
        Returns:
            Dict with strategies for all available APIs:
                - yelp_search: Structured Yelp API parameters
                - google_places_search: Natural language query
                - serpapi_search: Web search query with filters
                - tavily_research: Deep research query with domains
                - hunter_strategy: Email discovery parameters
                - lead_criteria: Qualification criteria
        """
        log.info("🤖 Generating COMPREHENSIVE multi-API search strategy...")
        log.info(f"   Company Brief: {company_brief[:100]}{'...' if len(company_brief) > 100 else ''}")
        
        prompt = f"""You are an expert B2B lead generation strategist specializing in multi-API orchestration.
You understand how to leverage different APIs' strengths to create comprehensive lead discovery strategies.

Company Brief:
{company_brief}

Generate a COMPREHENSIVE search strategy that leverages ALL available APIs for maximum coverage and data enrichment.

=== YELP FUSION API (Primary Discovery) ===
CRITICAL RULES:
1. Price parameter MUST be NUMERIC: "1,2" (not "$,$$"). Yelp uses: 1=$, 2=$$, 3=$$$, 4=$$$$
   - Use "1,2" for budget/mid-market (small businesses)
   - Use "2,3" for mid-market/enterprise (established companies)
   - Use "3" for enterprise only (avoid "4" - too expensive)
2. Categories: Use EXACT Yelp category aliases (comma-separated, no spaces)
   Examples: "softwaredev", "itservices", "marketingagencies", "contractors", "hvac"
   Reference: https://www.yelp.com/developers/documentation/v3/all_category_list
3. Term: 5-8 specific keywords (not generic like "companies")
4. Attributes: "has_website" for verified businesses
5. Sort: "best_match" (default), "rating", "review_count", or "distance"

=== GOOGLE PLACES API (Secondary Discovery + Enrichment) ===
CRITICAL RULES:
1. Query: DETAILED 10-15 word natural language query
2. Include: Industry + Location + Size signals + Tech indicators + Timeframe
3. Example: "established construction firms using project management software Toronto GTA 10+ employees commercial focus founded 2018 or earlier"
4. Google excels at understanding context and business relationships

=== SERPAPI (Web Search + SERP Data) ===
CRITICAL RULES:
1. Query: Optimized Google search query (8-12 words)
2. Location: City, State/Province (for local results)
3. Engine: "google" (default)
4. Use for: Finding company websites, news mentions, directory listings
5. Example: "construction project management software companies Toronto Ontario"

=== TAVILY RESEARCH (Deep Business Intelligence) ===
CRITICAL RULES:
1. Query: Research-focused keywords (industry + validation terms)
2. Include domains: ["linkedin.com", "crunchbase.com", "clutch.co", "bbb.org"]
3. Exclude domains: ["yelp.com"] (already have Yelp data)
4. Use for: Verifying businesses, finding case studies, reputation signals
5. Example: "construction project management software adoption rates Toronto case studies customer testimonials"

=== HUNTER.IO STRATEGY (Email Discovery) ===
CRITICAL RULES:
1. Domain pattern: Extract likely domain patterns from company brief
2. Email format: Predict common formats (firstname.lastname@domain, info@domain, etc.)
3. Use for: High-value leads only (Tier A - score >= 65)
4. Strategy: Focus on finding decision-maker emails

=== LEAD CRITERIA (Qualification) ===
CRITICAL RULES:
1. must_have: Absolute requirements (website, established date, employee count)
2. nice_to_have: Quality boosters (case studies, certifications, reviews)
3. deal_breakers: Automatic exclusions (freelancers, residential-only, solo practitioners)

Return ONLY a valid JSON object (no markdown, no code blocks):
{{
  "yelp_search": {{
    "term": "specific search term (5-8 words)",
    "location": "City, State/Province",
    "categories": "category1,category2,category3",
    "price": "1,2",
    "attributes": "has_website",
    "sort_by": "best_match"
  }},
  "google_places_search": {{
    "query": "detailed 10-15 word natural language query with industry location size tech timeframe"
  }},
  "serpapi_search": {{
    "query": "optimized web search query 8-12 words",
    "location": "City, State/Province",
    "engine": "google"
  }},
  "tavily_research": {{
    "query": "research keywords for validation and intelligence",
    "include_domains": ["linkedin.com", "crunchbase.com", "clutch.co"],
    "exclude_domains": ["yelp.com"]
  }},
  "hunter_strategy": {{
    "domain_patterns": ["likely-domain-patterns"],
    "email_formats": ["firstname.lastname", "info", "contact"],
    "priority_departments": ["sales", "marketing", "operations"]
  }},
  "lead_criteria": {{
    "must_have": ["website", "established_business", "employee_count"],
    "nice_to_have": ["case_studies", "verified_clients", "certifications"],
    "deal_breakers": ["residential_only", "freelance", "solo_practitioner"]
  }}
}}

Example for "Toronto SaaS company selling project management tools to construction firms":
{{
  "yelp_search": {{
    "term": "construction project management software solutions",
    "location": "Toronto, ON",
    "categories": "contractors,structuralengineers,civilengineers,softwaredev",
    "price": "2,3",
    "attributes": "has_website",
    "sort_by": "best_match"
  }},
  "google_places_search": {{
    "query": "established construction firms using project management software Toronto GTA 10+ employees commercial focus founded 2018 or earlier"
  }},
  "serpapi_search": {{
    "query": "construction project management software companies Toronto Ontario",
    "location": "Toronto, ON",
    "engine": "google"
  }},
  "tavily_research": {{
    "query": "construction project management software adoption rates Toronto case studies customer testimonials",
    "include_domains": ["linkedin.com", "crunchbase.com", "clutch.co", "bbb.org"],
    "exclude_domains": ["yelp.com"]
  }},
  "hunter_strategy": {{
    "domain_patterns": ["construction", "build", "contractor"],
    "email_formats": ["firstname.lastname", "info", "contact"],
    "priority_departments": ["operations", "project management", "estimating"]
  }},
  "lead_criteria": {{
    "must_have": ["website", "established_2018_or_earlier", "10+_employees"],
    "nice_to_have": ["commercial_focus", "public_projects", "case_studies"],
    "deal_breakers": ["residential_only", "freelance", "solo_practitioner"]
  }}
}}

Now generate for the company brief above:"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response (remove markdown code blocks if present)
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parse JSON
            strategy = json.loads(response_text)
            
            # Validate structure - check for required keys
            required_keys = ['yelp_search', 'google_places_search', 'tavily_research', 'lead_criteria']
            missing_keys = [key for key in required_keys if key not in strategy]
            if missing_keys:
                raise ValueError(f"Invalid strategy format - missing required fields: {missing_keys}")
            
            # Validate Yelp price format (must be numeric, not dollar signs)
            yelp_price = strategy.get('yelp_search', {}).get('price')
            if yelp_price:
                # Check if it contains dollar signs (old format)
                if '$' in str(yelp_price):
                    log.warning(f"⚠️ Yelp price contains dollar signs: {yelp_price}. Converting to numeric format.")
                    # Convert $,$$ to 1,2 etc.
                    price_map = {'$': '1', '$$': '2', '$$$': '3', '$$$$': '4'}
                    price_str = str(yelp_price)
                    numeric_prices = []
                    for symbol, num in price_map.items():
                        if symbol in price_str:
                            numeric_prices.append(num)
                    if numeric_prices:
                        strategy['yelp_search']['price'] = ','.join(numeric_prices)
                    else:
                        strategy['yelp_search']['price'] = "2,3"  # Default mid-market
                        log.warning("   Using default price: 2,3 (mid-market)")
            
            # Ensure all optional API strategies exist (for backward compatibility)
            if 'serpapi_search' not in strategy:
                strategy['serpapi_search'] = {
                    'query': strategy['google_places_search'].get('query', ''),
                    'location': strategy['yelp_search'].get('location', ''),
                    'engine': 'google'
                }
            
            if 'hunter_strategy' not in strategy:
                strategy['hunter_strategy'] = {
                    'domain_patterns': [],
                    'email_formats': ['firstname.lastname', 'info', 'contact'],
                    'priority_departments': ['sales', 'marketing']
                }
            
            # Log comprehensive strategy summary
            log.info(f"✓ COMPREHENSIVE Multi-API Strategy Generated:")
            log.info(f"   📍 Location: {strategy['yelp_search'].get('location', 'N/A')}")
            log.info(f"   🏷️ Yelp Categories: {strategy['yelp_search'].get('categories', 'N/A')}")
            log.info(f"   💰 Yelp Price: {strategy['yelp_search'].get('price', 'N/A')} (numeric format)")
            log.info(f"   🔍 Yelp Term: {strategy['yelp_search'].get('term', 'N/A')}")
            log.info(f"   🌐 Google Places Query: {strategy['google_places_search'].get('query', 'N/A')[:80]}...")
            if 'serpapi_search' in strategy:
                log.info(f"   🔎 SerpAPI Query: {strategy['serpapi_search'].get('query', 'N/A')[:60]}...")
            log.info(f"   📊 Tavily Research: {strategy['tavily_research'].get('query', 'N/A')[:60]}...")
            log.info(f"   ✅ Must Have: {', '.join(strategy['lead_criteria'].get('must_have', []))}")
            log.info(f"   ❌ Deal Breakers: {', '.join(strategy['lead_criteria'].get('deal_breakers', []))}")
            
            return strategy
            
        except json.JSONDecodeError as e:
            log.error(f"❌ Failed to parse AI response as JSON: {e}")
            log.error(f"   Response: {response_text[:200]}")
            # Fallback to manual parsing
            return self._fallback_strategy(company_brief)
            
        except Exception as e:
            log.error(f"❌ AI query generation failed: {e}")
            return self._fallback_strategy(company_brief)
    
    def _fallback_strategy(self, company_brief: str) -> Dict:
        """
        Fallback strategy if AI generation fails.
        Extract basic keywords from brief and create minimal strategy.
        """
        log.warning("⚠️ Using fallback strategy (AI generation failed)")
        
        # Simple keyword extraction
        words = company_brief.lower().split()
        
        # Try to find location keywords
        location_keywords = {
            'toronto': 'Toronto, ON',
            'vancouver': 'Vancouver, BC',
            'montreal': 'Montreal, QC',
            'calgary': 'Calgary, AB',
            'ottawa': 'Ottawa, ON',
            'new york': 'New York, NY',
            'california': 'California, CA',
            'san francisco': 'San Francisco, CA',
            'los angeles': 'Los Angeles, CA'
        }
        location = "Toronto, ON"  # Default
        for word in words:
            for loc_key, loc_value in location_keywords.items():
                if loc_key in word.lower():
                    location = loc_value
                    break
        
        # Create basic fallback query
        term = ' '.join(words[:8])  # Use first 8 words as term
        
        return {
            'yelp_search': {
                'term': term,
                'location': location,
                'categories': None,
                'price': '2,3',  # Default mid-market (numeric format)
                'attributes': 'has_website',
                'sort_by': 'best_match'
            },
            'google_places_search': {
                'query': company_brief[:100]
            },
            'serpapi_search': {
                'query': term,
                'location': location,
                'engine': 'google'
            },
            'tavily_research': {
                'query': term,
                'include_domains': ['linkedin.com', 'crunchbase.com'],
                'exclude_domains': ['yelp.com']
            },
            'hunter_strategy': {
                'domain_patterns': [],
                'email_formats': ['firstname.lastname', 'info', 'contact'],
                'priority_departments': ['sales', 'marketing']
            },
            'lead_criteria': {
                'must_have': ['website'],
                'nice_to_have': [],
                'deal_breakers': ['residential_only', 'freelance']
            }
        }
