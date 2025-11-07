"""
AI-Powered Query Generator - Convert company descriptions into optimized search queries.
Uses Gemini 2.0 Flash for fast, intelligent query generation.
"""
import json
import google.generativeai as genai
from typing import Dict, List
from config.settings import SETTINGS
from utils.logging_utils import get_logger

log = get_logger(__name__)


class QueryGenerator:
    """
    Gemini-powered query generator that converts company briefs into optimized discovery queries.
    
    Input: "Acme Software is a Toronto B2B SaaS company selling project management tools..."
    Output: 3-5 targeted queries + location + filtering criteria
    """
    
    def __init__(self, api_key: str = None):
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
        
        log.info("✅ AI Query Generator initialized (Gemini 2.0 Flash)")
    
    def generate_search_strategy(self, company_brief: str) -> Dict:
        """
        Generate PRECISION search strategy with structured API parameters.
        
        Args:
            company_brief: 2-3 sentence description of the company and lead requirements
        
        Returns:
            Dict with:
                - yelp_search: Dict with term, location, categories, price, attributes, sort_by
                - google_places_search: Dict with detailed natural language query
                - tavily_research: Dict with query and include_domains
                - lead_criteria: Dict with must_have, nice_to_have, deal_breakers
        """
        log.info("🤖 Generating PRECISION AI-powered search strategy...")
        log.info(f"   Company Brief: {company_brief[:100]}{'...' if len(company_brief) > 100 else ''}")
        
        prompt = f"""You are a B2B lead generation expert with deep knowledge of Yelp's category system and advanced search operators.

Company Brief:
{company_brief}

Generate a PRECISION search strategy using STRUCTURED API parameters (not generic queries).

CRITICAL RULES FOR YELP:
1. Use EXACT Yelp category aliases from: https://www.yelp.com/developers/documentation/v3/all_category_list
   Examples: "softwaredev", "itservices", "marketingagencies", "advertisingagencies", "contractors", "hvac", "plumbers"
2. Set price filter to target company stage: "$,$$" for mid-market, "$$,$$$" for enterprise (avoid "$$$$")
3. Use specific terms, not generic words like "companies" or "businesses"
4. Add attributes: "has_website" (verified businesses only)

CRITICAL RULES FOR GOOGLE PLACES:
1. Write a DETAILED 10-15 word natural language query
2. Include: Industry + Location + Business size signals + Tech/process indicators + Timeframe
3. Example: "established B2B SaaS development companies building enterprise project management tools Toronto GTA 50+ employees founded 2015 or earlier"

CRITICAL RULES FOR LEAD CRITERIA:
1. must_have: Features that are absolutely required (website, employees, established date)
2. nice_to_have: Bonus features that increase lead quality
3. deal_breakers: Exclude these types (freelancers, residential, solo practitioners)

Return ONLY a valid JSON object (no markdown, no code blocks):
{{
  "yelp_search": {{
    "term": "specific search term (5-8 words max)",
    "location": "City, State/Province",
    "categories": "category1,category2,category3",
    "price": "$,$$",
    "attributes": "has_website",
    "sort_by": "best_match"
  }},
  "google_places_search": {{
    "query": "detailed 10-15 word natural language query with industry location size tech timeframe"
  }},
  "tavily_research": {{
    "query": "validation keywords for deep research",
    "include_domains": ["linkedin.com", "crunchbase.com", "clutch.co"]
  }},
  "lead_criteria": {{
    "must_have": ["website", "established_business"],
    "nice_to_have": ["case_studies", "verified_clients"],
    "deal_breakers": ["residential_only", "freelance", "solo_practitioner"]
  }}
}}

Example for "Vancouver marketing agency targeting healthcare advertisers":
{{
  "yelp_search": {{
    "term": "healthcare medical advertising marketing",
    "location": "San Francisco, CA",
    "categories": "marketingagencies,advertisingagencies,mediaservices",
    "price": "$$,$$$",
    "attributes": "has_website",
    "sort_by": "best_match"
  }},
  "google_places_search": {{
    "query": "established healthcare advertising agencies managing pharmaceutical medical device campaigns San Francisco Bay Area enterprise clients 20+ employees founded 2010 or earlier with case studies"
  }},
  "tavily_research": {{
    "query": "healthcare advertising agencies pharmaceutical medical device clients case studies",
    "include_domains": ["linkedin.com", "clutch.co", "agencylist.com"]
  }},
  "lead_criteria": {{
    "must_have": ["website", "established_2015_or_earlier", "10+_employees"],
    "nice_to_have": ["healthcare_clients", "pharma_compliance", "case_studies"],
    "deal_breakers": ["freelance", "solo_practitioner", "residential_only"]
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
            
            # Validate structure
            required_keys = ['yelp_search', 'google_places_search', 'tavily_research', 'lead_criteria']
            if not all(key in strategy for key in required_keys):
                raise ValueError(f"Invalid strategy format - missing required fields. Expected: {required_keys}")
            
            log.info(f"✓ PRECISION AI Strategy Generated:")
            log.info(f"   📍 Location: {strategy['yelp_search'].get('location', 'N/A')}")
            log.info(f"   🏷️ Yelp Categories: {strategy['yelp_search'].get('categories', 'N/A')}")
            log.info(f"   💰 Price Filter: {strategy['yelp_search'].get('price', 'N/A')}")
            log.info(f"   🔍 Yelp Term: {strategy['yelp_search'].get('term', 'N/A')}")
            log.info(f"   🌐 Google Query: {strategy['google_places_search'].get('query', 'N/A')[:80]}...")
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
        Extract basic keywords from brief.
        """
        log.warning("⚠️ Using fallback strategy (AI generation failed)")
        
        # Simple keyword extraction
        words = company_brief.lower().split()
        
        # Try to find location keywords
        location_keywords = ['toronto', 'ontario', 'vancouver', 'montreal', 'canada', 'new york', 'california']
        location = "Toronto, ON"  # Default
        for word in words:
            for loc in location_keywords:
                if loc in word:
                    location = f"{loc.title()}, ON"
                    break
        
        # Create basic fallback query
        term = company_brief[:50]  # Use first 50 chars as term
        
        return {
            'yelp_search': {
                'term': term,
                'location': location,
                'categories': None,
                'price': None,
                'attributes': 'has_website',
                'sort_by': 'best_match'
            },
            'google_places_search': {
                'query': company_brief[:100]
            },
            'tavily_research': {
                'query': term,
                'include_domains': ['linkedin.com']
            },
            'lead_criteria': {
                'must_have': ['website'],
                'nice_to_have': [],
                'deal_breakers': ['residential_only']
            }
        }
