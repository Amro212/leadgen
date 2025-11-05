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
    
    def generate_search_strategy(self, company_brief: str, max_queries: int = 4) -> Dict:
        """
        Generate optimized search strategy from company description.
        
        Args:
            company_brief: 2-3 sentence description of the company and lead requirements
            max_queries: Maximum number of queries to generate (default: 4)
        
        Returns:
            Dict with:
                - primary_queries: List[str] - 3-5 optimized search terms
                - location: str - Target geographic area
                - reasoning: str - Why these queries were chosen
        """
        log.info("🤖 Generating AI-powered search strategy...")
        log.info(f"   Company Brief: {company_brief[:100]}{'...' if len(company_brief) > 100 else ''}")
        
        prompt = f"""You are a B2B lead generation expert. Analyze this company description and generate optimized search queries for finding relevant business leads.

Company Brief:
{company_brief}

Your task:
1. Generate {max_queries} specific, targeted search queries (3-7 words each)
2. Determine the best geographic location to search
3. Explain your reasoning

Rules:
- Queries should focus on WHAT businesses do, not generic titles
- Consider technical capabilities, industries served, and specializations
- Think about adjacent/complementary businesses (e.g., "construction tech" also means "BIM software", "project management tools")
- Location should match the company's target market (extract from brief if mentioned)
- Be specific - avoid generic terms like "companies" or "agencies"

Return ONLY a valid JSON object in this exact format (no markdown, no extra text):
{{
  "primary_queries": [
    "query 1",
    "query 2", 
    "query 3",
    "query 4"
  ],
  "location": "City, Province/State",
  "reasoning": "Brief explanation of strategy"
}}

Example input: "Shopify is a Toronto e-commerce company looking for agencies that build custom integrations and apps."
Example output:
{{
  "primary_queries": [
    "Shopify app developers Toronto",
    "e-commerce integration specialists Canada",
    "custom API development agencies Toronto",
    "Shopify Plus partners Ontario"
  ],
  "location": "Toronto, ON",
  "reasoning": "Focused on technical capabilities (integrations, APIs, apps) and Shopify ecosystem partners rather than generic web agencies"
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
            if 'primary_queries' not in strategy or 'location' not in strategy:
                raise ValueError("Invalid strategy format - missing required fields")
            
            log.info(f"✓ AI Strategy Generated:")
            log.info(f"   📍 Location: {strategy['location']}")
            log.info(f"   🔍 Queries: {len(strategy['primary_queries'])}")
            for i, query in enumerate(strategy['primary_queries'], 1):
                log.info(f"      {i}. {query}")
            if 'reasoning' in strategy:
                log.info(f"   💡 Reasoning: {strategy['reasoning']}")
            
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
        
        # Create generic query
        queries = [company_brief[:50]]  # Use first 50 chars as query
        
        return {
            'primary_queries': queries,
            'location': location,
            'reasoning': 'Fallback strategy - AI generation failed'
        }
