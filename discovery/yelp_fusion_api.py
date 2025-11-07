"""
Yelp Fusion API - Primary Discovery Source
Uses Yelp Business Search API to find real businesses.
"""
import requests
from typing import List, Dict, Optional
from discovery.base_discovery import DiscoverySource
from config.settings import SETTINGS
from storage.api_usage import get_tracker
from utils.logging_utils import get_logger

log = get_logger(__name__)


class YelpFusionAPI(DiscoverySource):
    """
    Yelp Fusion API implementation for business discovery.
    
    API Docs: https://docs.developer.yelp.com/reference/v3_business_search
    Free tier: 500 API calls per day
    """
    
    BASE_URL = "https://api.yelp.com/v3/businesses/search"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Yelp API client.
        
        Args:
            api_key: Yelp Fusion API key (defaults to SETTINGS.YELP_API_KEY)
        """
        self.api_key = api_key or SETTINGS.YELP_API_KEY
        
        if not self.api_key:
            raise ValueError("YELP_API_KEY not found in environment variables")
        
        self.tracker = get_tracker()
        log.info("✅ Yelp Fusion API initialized")
    
    def fetch_leads(self, query: str, location: str, max_results: int = 50) -> List[Dict]:
        """
        Search for businesses using Yelp Fusion API.
        
        Args:
            query: Business category or search term (e.g., "Digital Agencies")
            location: City and state/province (e.g., "Toronto, ON")
            max_results: Maximum number of results (Yelp max: 50 per call)
        
        Returns:
            List of lead dictionaries with business data
        """
        # Check quota before making API call
        if not self.tracker.can_use('yelp', count=1):
            remaining = self.tracker.get_remaining('yelp')
            log.warning(f"⚠️ Yelp API quota exhausted (0/{self.tracker.state['yelp']['limit']} remaining)")
            log.warning("   Returning empty results. Will reset tomorrow.")
            return []
        
        # Yelp limits to 50 results per call
        limit = min(max_results, 50)
        
        log.info(f"🔍 Yelp API: Searching for '{query}' in '{location}' (max {limit})")
        
        try:
            # Build request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json'
            }
            
            params = {
                'term': query,
                'location': location,
                'limit': limit,
                'sort_by': 'best_match'  # Can also be 'rating', 'review_count', 'distance'
            }
            
            # Make API call
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract businesses
            businesses = data.get('businesses', [])
            total_found = data.get('total', 0)
            
            log.info(f"✓ Yelp API: Found {len(businesses)} businesses (total available: {total_found})")
            
            # Increment usage counter
            self.tracker.increment('yelp', count=1)
            remaining = self.tracker.get_remaining('yelp')
            log.info(f"   📊 Yelp quota: {remaining}/{self.tracker.state['yelp']['limit']} remaining today")
            
            # Map to lead dictionaries
            leads = [self._map_to_lead(biz, query) for biz in businesses]
            
            return leads
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                log.error("❌ Yelp API: Rate limit exceeded (429)")
            elif e.response.status_code == 401:
                log.error("❌ Yelp API: Invalid API key (401)")
            else:
                log.error(f"❌ Yelp API: HTTP error {e.response.status_code}")
            return []
            
        except requests.exceptions.RequestException as e:
            log.error(f"❌ Yelp API: Request failed: {e}")
            return []
            
        except Exception as e:
            log.error(f"❌ Yelp API: Unexpected error: {e}")
            return []
    
    def fetch_leads_structured(
        self,
        term: str,
        location: str,
        categories: Optional[str] = None,
        price: Optional[str] = None,
        attributes: Optional[str] = None,
        sort_by: str = "best_match",
        max_results: int = 50
    ) -> List[Dict]:
        """
        Search for businesses using STRUCTURED Yelp Fusion API parameters.
        This method uses all available Yelp filtering options for precision targeting.
        
        Args:
            term: Search term (e.g., "construction software developers")
            location: City and state/province (e.g., "Toronto, ON")
            categories: Comma-separated Yelp category aliases (e.g., "softwaredev,itservices,contractors")
                       See: https://www.yelp.com/developers/documentation/v3/all_category_list
            price: Comma-separated price levels (e.g., "1,2,3" for $, $$, $$$)
            attributes: Comma-separated attributes (e.g., "hot_and_new,deals,reservation,waitlist_reservation")
            sort_by: Sort method - "best_match", "rating", "review_count", or "distance"
            max_results: Maximum number of results (Yelp max: 50 per call)
        
        Returns:
            List of lead dictionaries with business data
        """
        # Check quota before making API call
        if not self.tracker.can_use('yelp', count=1):
            remaining = self.tracker.get_remaining('yelp')
            log.warning(f"⚠️ Yelp API quota exhausted (0/{self.tracker.state['yelp']['limit']} remaining)")
            log.warning("   Returning empty results. Will reset tomorrow.")
            return []
        
        # Yelp limits to 50 results per call
        limit = min(max_results, 50)
        
        log.info(f"🔍 Yelp API (STRUCTURED): Searching for '{term}' in '{location}' (max {limit})")
        if categories:
            log.info(f"   📂 Categories: {categories}")
        if price:
            log.info(f"   💰 Price: {price}")
        if attributes:
            log.info(f"   🏷️ Attributes: {attributes}")
        
        try:
            # Build request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json'
            }
            
            params = {
                'term': term,
                'location': location,
                'limit': limit,
                'sort_by': sort_by
            }
            
            # Add optional structured parameters
            if categories:
                params['categories'] = categories
            if price:
                params['price'] = price
            if attributes:
                params['attributes'] = attributes
            
            # Make API call
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract businesses
            businesses = data.get('businesses', [])
            total_found = data.get('total', 0)
            
            log.info(f"✓ Yelp API: Found {len(businesses)} businesses (total available: {total_found})")
            
            # Increment usage counter
            self.tracker.increment('yelp', count=1)
            remaining = self.tracker.get_remaining('yelp')
            log.info(f"   📊 Yelp quota: {remaining}/{self.tracker.state['yelp']['limit']} remaining today")
            
            # Map to lead dictionaries
            leads = [self._map_to_lead(biz, term) for biz in businesses]
            
            return leads
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                log.error("❌ Yelp API: Rate limit exceeded (429)")
            elif e.response.status_code == 401:
                log.error("❌ Yelp API: Invalid API key (401)")
            else:
                log.error(f"❌ Yelp API: HTTP error {e.response.status_code}")
            return []
            
        except requests.exceptions.RequestException as e:
            log.error(f"❌ Yelp API: Request failed: {e}")
            return []
            
        except Exception as e:
            log.error(f"❌ Yelp API: Unexpected error: {e}")
            return []
    
    def _map_to_lead(self, business: Dict, query: str) -> Dict:
        """
        Map Yelp business response to lead dictionary format.
        
        Args:
            business: Yelp business object
            query: Original search query
        
        Returns:
            Lead dictionary
        """
        # Extract location components
        location = business.get('location', {})
        
        # Build address string
        address_parts = []
        if location.get('address1'):
            address_parts.append(location['address1'])
        if location.get('address2'):
            address_parts.append(location['address2'])
        
        address = ', '.join(address_parts) if address_parts else None
        
        # Format phone number (Yelp returns E.164 format: +14161234567)
        phone = business.get('phone', '').strip()
        if phone and phone.startswith('+1') and len(phone) == 12:
            # Convert +14161234567 to +1-416-123-4567
            phone = f"+1-{phone[2:5]}-{phone[5:8]}-{phone[8:]}"
        
        lead = {
            'business_name': business.get('name'),
            'website': business.get('url'),  # This is the Yelp URL, not business website
            'phone': phone,
            'city': location.get('city'),
            'state': location.get('state'),
            'country': location.get('country', 'US'),
            'address': address,
            'zip_code': location.get('zip_code'),
            'source_url': business.get('url'),
            'discovery_method': 'yelp_fusion_api',
            'yelp_rating': business.get('rating'),  # 1-5 star rating
            'yelp_review_count': business.get('review_count'),  # Number of reviews
            'yelp_price_level': business.get('price'),  # $ to $$$$
            'yelp_categories': [cat['title'] for cat in business.get('categories', [])],
            'notes': [f"Yelp search: '{query}'"]  # Changed from internal_notes to notes (list field)
        }
        
        # Note: Yelp doesn't provide actual business website in the search endpoint
        # We'll need to check if we can extract it during enrichment or use a different field
        log.debug(f"   Mapped: {lead['business_name']} | {lead['phone']} | {lead['city']}")
        
        return lead
