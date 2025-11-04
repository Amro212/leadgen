"""
Tavily Deep Research - Business Verification & Intelligence
Uses Tavily Search + Extract APIs for comprehensive lead verification.
Only runs on Tier A leads (score >= 65) due to importance.
"""
import requests
from typing import List, Dict, Optional
from urllib.parse import urlparse
from config.settings import SETTINGS
from storage.api_usage import get_tracker
from utils.logging_utils import get_logger

log = get_logger(__name__)


class TavilyResearcher:
    """
    Tavily API client for deep business research and verification.
    
    API Docs: https://docs.tavily.com/documentation
    Pricing: Free tier = 1,000 credits/month (4,000 paid plan)
    
    Features:
    - /search: Find business mentions, reviews, websites (1 credit/search)
    - /extract: Deep content extraction from URLs (1 credit per 5 URLs)
    """
    
    SEARCH_URL = "https://api.tavily.com/search"
    EXTRACT_URL = "https://api.tavily.com/extract"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily client.
        
        Args:
            api_key: Tavily API key (defaults to SETTINGS.TAVILY_API_KEY)
        """
        self.api_key = api_key or SETTINGS.TAVILY_API_KEY
        
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
        
        self.tracker = get_tracker()
        log.info("✅ Tavily Researcher initialized")
    
    def research_business(self, business_name: str, city: str, website: Optional[str] = None) -> Dict:
        """
        Comprehensive business research using Tavily.
        
        Strategy:
        1. Search for business mentions (reviews, social, directories)
        2. Find actual business website (if not already known)
        3. Verify business is active (recent mentions)
        4. Check reputation signals (positive/negative mentions)
        
        Args:
            business_name: Business name
            city: City location
            website: Known website (optional, will try to find if missing)
        
        Returns:
            Dict with research findings:
                - verified_website: str | None - Actual business website found
                - recent_activity: bool - Has mentions in last 6 months
                - reputation_score: int (0-100) - Calculated from mentions
                - sources_found: int - Number of independent sources
                - review_sites: List[str] - Review platforms found
                - negative_flags: List[str] - Warning signs found
                - tavily_verified: bool - Research was successful
        """
        # Check quota
        if not self.tracker.can_use('tavily', count=1):
            remaining = self.tracker.get_remaining('tavily')
            log.warning(f"⚠️ Tavily quota exhausted ({remaining}/4000 remaining this month)")
            return self._empty_result()
        
        log.info(f"🔍 Tavily: Researching '{business_name}' in {city}")
        
        try:
            # Step 1: Search for business mentions
            search_results = self._search_business(business_name, city, website)
            
            if not search_results:
                log.info(f"   ℹ️ Tavily: No results found for {business_name}")
                self.tracker.increment('tavily', count=1)
                return self._empty_result()
            
            # Step 2: Analyze results
            analysis = self._analyze_results(search_results, business_name, website)
            
            # Increment usage
            self.tracker.increment('tavily', count=1)
            remaining = self.tracker.get_remaining('tavily')
            log.info(f"   📊 Tavily quota: {remaining}/4000 remaining this month")
            
            # Log findings
            log.info(f"   ✓ Tavily: Found {analysis['sources_found']} sources")
            if analysis['verified_website']:
                log.info(f"   🌐 Website: {analysis['verified_website']}")
            if analysis['reputation_score']:
                log.info(f"   ⭐ Reputation: {analysis['reputation_score']}/100")
            
            return analysis
            
        except Exception as e:
            log.error(f"❌ Tavily: Research failed for {business_name}: {e}")
            return self._empty_result()
    
    def _search_business(self, business_name: str, city: str, known_website: Optional[str]) -> Dict:
        """
        Execute Tavily search for business.
        
        Query strategy:
        - Primary: "{business_name}" {city} reviews contact website
        - Exclude: yelp.com (already have Yelp data)
        - Include: google.com/maps, facebook.com, linkedin.com, yellowpages
        - Time range: Past year (for recent activity)
        - Search depth: advanced (better results, 2 credits)
        """
        try:
            # Build search query
            query = f'"{business_name}" {city} reviews contact website'
            
            # API request
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "advanced",  # Better content extraction (2 credits)
                "max_results": 10,  # Get multiple sources
                "include_domains": [
                    "google.com/maps",
                    "facebook.com",
                    "linkedin.com",
                    "yellowpages.com",
                    "bbb.org",  # Better Business Bureau
                    "trustpilot.com"
                ],
                "exclude_domains": [
                    "yelp.com",  # Already have Yelp data
                    "instagram.com",  # Not useful for contact/website
                    "twitter.com"
                ],
                "time_range": "year",  # Last 12 months
                "include_raw_content": False,  # Don't need full HTML
                "include_answer": False  # Don't need AI summary (save credits)
            }
            
            log.debug(f"   Tavily query: {query}")
            
            response = requests.post(
                self.SEARCH_URL,
                headers=headers,
                json=payload,
                timeout=15
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                log.error("❌ Tavily: Rate limit exceeded (429)")
            elif e.response.status_code == 401:
                log.error("❌ Tavily: Invalid API key (401)")
            elif e.response.status_code == 402:
                log.error("❌ Tavily: Payment required - quota exceeded (402)")
            else:
                log.error(f"❌ Tavily: HTTP error {e.response.status_code}")
            return {}
            
        except requests.exceptions.RequestException as e:
            log.error(f"❌ Tavily: Request failed: {e}")
            return {}
    
    def _analyze_results(self, search_data: Dict, business_name: str, known_website: Optional[str]) -> Dict:
        """
        Analyze Tavily search results to extract insights.
        
        Extracts:
        - Actual business website (from URLs, not Yelp)
        - Recent activity (publication dates)
        - Reputation signals (positive/negative keywords)
        - Review platforms found
        - Warning flags
        """
        results = search_data.get('results', [])
        
        if not results:
            return self._empty_result()
        
        # Initialize analysis
        analysis = {
            'verified_website': None,
            'recent_activity': False,
            'reputation_score': 50,  # Neutral starting point
            'sources_found': len(results),
            'review_sites': [],
            'negative_flags': [],
            'tavily_verified': True
        }
        
        # Track findings
        website_candidates = []
        recent_count = 0
        positive_mentions = 0
        negative_mentions = 0
        
        # Negative keywords (reputation flags)
        negative_keywords = [
            'scam', 'fraud', 'avoid', 'terrible', 'worst', 
            'nightmare', 'lawsuit', 'complaint', 'warning',
            'unprofessional', 'dishonest', 'ripoff'
        ]
        
        # Positive keywords
        positive_keywords = [
            'excellent', 'great', 'best', 'professional',
            'reliable', 'recommend', 'quality', 'trusted',
            'amazing', 'fantastic', 'wonderful'
        ]
        
        for result in results:
            url = result.get('url', '')
            content = result.get('content', '').lower()
            title = result.get('title', '').lower()
            
            # 1. Find actual business website
            if business_name.lower() in url.lower():
                # URL contains business name = likely their website
                domain = urlparse(url).netloc
                if domain and not any(x in domain for x in ['yelp.com', 'facebook.com', 'google.com']):
                    website_candidates.append(url)
            
            # 2. Check for recent activity
            # Tavily doesn't always return dates, so check content for year mentions
            if '2024' in content or '2025' in content:
                recent_count += 1
            
            # 3. Identify review sites
            if 'google.com/maps' in url:
                analysis['review_sites'].append('Google Maps')
            elif 'facebook.com' in url:
                analysis['review_sites'].append('Facebook')
            elif 'bbb.org' in url:
                analysis['review_sites'].append('BBB')
            elif 'trustpilot.com' in url:
                analysis['review_sites'].append('Trustpilot')
            
            # 4. Sentiment analysis (basic keyword matching)
            for keyword in positive_keywords:
                if keyword in content or keyword in title:
                    positive_mentions += 1
            
            for keyword in negative_keywords:
                if keyword in content or keyword in title:
                    negative_mentions += 1
                    analysis['negative_flags'].append(f"Found '{keyword}' in {url}")
        
        # Deduplicate review sites
        analysis['review_sites'] = list(set(analysis['review_sites']))
        
        # Set verified website
        if website_candidates:
            analysis['verified_website'] = website_candidates[0]
        elif known_website and 'yelp.com' not in known_website:
            analysis['verified_website'] = known_website
        
        # Set recent activity flag
        analysis['recent_activity'] = recent_count >= 2
        
        # Calculate reputation score (0-100)
        # Base: 50 (neutral)
        # +5 per positive mention (max +30)
        # -10 per negative mention (max -50)
        # +10 if found on BBB or Trustpilot
        score = 50
        score += min(positive_mentions * 5, 30)
        score -= min(negative_mentions * 10, 50)
        if 'BBB' in analysis['review_sites'] or 'Trustpilot' in analysis['review_sites']:
            score += 10
        
        analysis['reputation_score'] = max(0, min(100, score))
        
        return analysis
    
    def extract_content(self, urls: List[str]) -> Dict:
        """
        Extract clean content from URLs using Tavily Extract API.
        
        Args:
            urls: List of URLs to extract (max 5 per call)
        
        Returns:
            Dict with extracted content per URL
        """
        if not self.tracker.can_use('tavily', count=1):
            log.warning("⚠️ Tavily quota exhausted - skipping extraction")
            return {}
        
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "api_key": self.api_key,
                "urls": urls[:5],  # Max 5 URLs per call
                "extract_depth": "basic",  # 1 credit per 5 URLs
                "format": "text"  # Plain text
            }
            
            response = requests.post(
                self.EXTRACT_URL,
                headers=headers,
                json=payload,
                timeout=15
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract costs 1 credit per 5 successful URLs
            self.tracker.increment('tavily', count=1)
            
            return data
            
        except Exception as e:
            log.error(f"❌ Tavily Extract failed: {e}")
            return {}
    
    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            'verified_website': None,
            'recent_activity': False,
            'reputation_score': 0,
            'sources_found': 0,
            'review_sites': [],
            'negative_flags': [],
            'tavily_verified': False
        }
