"""
Website Discovery - Find actual business websites using multiple APIs.
Uses SerpAPI, Tavily, and Google Places Details to find real websites.
"""
import requests
from typing import List, Dict, Optional
from urllib.parse import urlparse
from config.settings import SETTINGS
from storage.api_usage import get_tracker
from utils.logging_utils import get_logger

log = get_logger(__name__)


class WebsiteDiscovery:
    """
    Discovers actual business websites using multiple APIs.
    
    Strategy:
    1. Google Places Details API (if place_id available) - fastest, most accurate
    2. SerpAPI web search (if available) - finds websites via Google search
    3. Tavily research (fallback) - deep search for business websites
    """
    
    def __init__(self):
        self.tracker = get_tracker()
        self.google_api_key = SETTINGS.GOOGLE_API_KEY
        self.serpapi_key = SETTINGS.SERPAPI_API_KEY
        self.tavily_key = SETTINGS.TAVILY_API_KEY
        
        self.google_available = bool(self.google_api_key)
        self.serpapi_available = bool(self.serpapi_key)
        self.tavily_available = bool(self.tavily_key)
        
        log.info("✅ Website Discovery initialized")
        log.info(f"   Google Places Details: {'✅' if self.google_available else '❌'}")
        log.info(f"   SerpAPI: {'✅' if self.serpapi_available else '❌'}")
        log.info(f"   Tavily: {'✅' if self.tavily_available else '❌'}")
    
    def discover_websites(self, leads: List[Dict]) -> List[Dict]:
        """
        Discover actual business websites for leads.
        
        Args:
            leads: List of lead dictionaries (may have Yelp URLs or None as website)
        
        Returns:
            List of leads with actual business websites discovered
        """
        log.info(f"🔍 Website Discovery: Finding actual websites for {len(leads)} leads...")
        
        enriched_leads = []
        websites_found = 0
        
        for lead in leads:
            enriched_lead = lead.copy()
            current_website = lead.get('website', '')
            
            # Skip if already has a real website (not Yelp URL)
            if current_website and 'yelp.com' not in current_website.lower():
                enriched_leads.append(enriched_lead)
                continue
            
            # Try to find actual website
            actual_website = None
            
            # Priority 1: Google Places Details API (if place_id available)
            if self.google_available and lead.get('google_place_id'):
                actual_website = self._get_website_from_google_places(lead['google_place_id'])
                if actual_website:
                    log.debug(f"   ✓ Found via Google Places: {lead.get('business_name')} -> {actual_website}")
            
            # Priority 2: SerpAPI web search (if Google Places didn't work)
            if not actual_website and self.serpapi_available:
                business_name = lead.get('business_name', '')
                city = lead.get('city', '')
                if business_name and city:
                    actual_website = self._get_website_from_serpapi(business_name, city)
                    if actual_website:
                        log.debug(f"   ✓ Found via SerpAPI: {business_name} -> {actual_website}")
            
            # Priority 3: Tavily research (fallback)
            if not actual_website and self.tavily_available:
                business_name = lead.get('business_name', '')
                city = lead.get('city', '')
                if business_name and city:
                    actual_website = self._get_website_from_tavily(business_name, city)
                    if actual_website:
                        log.debug(f"   ✓ Found via Tavily: {business_name} -> {actual_website}")
            
            # Update lead with discovered website
            if actual_website:
                enriched_lead['website'] = actual_website
                if 'notes' not in enriched_lead:
                    enriched_lead['notes'] = []
                enriched_lead['notes'].append(f"Website discovered via API")
                websites_found += 1
            else:
                # Keep Yelp URL as source_url but clear website field
                if 'yelp.com' in (current_website or '').lower():
                    enriched_lead['source_url'] = current_website
                    enriched_lead['website'] = None
                    if 'notes' not in enriched_lead:
                        enriched_lead['notes'] = []
                    enriched_lead['notes'].append("No actual website found (Yelp URL only)")
            
            enriched_leads.append(enriched_lead)
        
        log.info(f"✓ Website Discovery: Found {websites_found}/{len(leads)} actual websites")
        return enriched_leads
    
    def _get_website_from_google_places(self, place_id: str) -> Optional[str]:
        """
        Get business website from Google Places Details API.
        
        Args:
            place_id: Google Place ID
        
        Returns:
            Website URL or None
        """
        if not self.tracker.can_use('google_places', count=1):
            return None
        
        try:
            url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                'place_id': place_id,
                'fields': 'website',
                'key': self.google_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('result'):
                website = data['result'].get('website')
                if website:
                    self.tracker.increment('google_places', count=1)
                    return website
            
            return None
            
        except Exception as e:
            log.debug(f"   Google Places Details failed: {e}")
            return None
    
    def _get_website_from_serpapi(self, business_name: str, city: str) -> Optional[str]:
        """
        Get business website from SerpAPI Google search.
        
        Args:
            business_name: Business name
            city: City location
        
        Returns:
            Website URL or None
        """
        if not self.tracker.can_use('serpapi', count=1):
            return None
        
        try:
            url = "https://serpapi.com/search"
            params = {
                'q': f'"{business_name}" {city} website',
                'engine': 'google',
                'api_key': self.serpapi_key,
                'num': 5  # Check top 5 results
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract website from organic results
            organic_results = data.get('organic_results', [])
            for result in organic_results:
                link = result.get('link', '')
                # Skip Yelp, Facebook, Google Maps, etc.
                if link and not any(skip in link.lower() for skip in ['yelp.com', 'facebook.com', 'google.com/maps', 'google.com/search']):
                    # Check if link contains business name (likely their website)
                    if business_name.lower().replace(' ', '') in link.lower().replace(' ', '').replace('-', ''):
                        self.tracker.increment('serpapi', count=1)
                        return link
            
            return None
            
        except Exception as e:
            log.debug(f"   SerpAPI search failed: {e}")
            return None
    
    def _get_website_from_tavily(self, business_name: str, city: str) -> Optional[str]:
        """
        Get business website from Tavily research.
        
        Args:
            business_name: Business name
            city: City location
        
        Returns:
            Website URL or None
        """
        if not self.tracker.can_use('tavily', count=1):
            return None
        
        try:
            from enrichment.tavily_researcher import TavilyResearcher
            tavily = TavilyResearcher()
            
            # Use Tavily's research method
            result = tavily.research_business(business_name, city, website=None)
            
            if result.get('verified_website'):
                return result['verified_website']
            
            return None
            
        except Exception as e:
            log.debug(f"   Tavily research failed: {e}")
            return None

