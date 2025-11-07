"""
Google Places API - Secondary Discovery Source
Uses Google Places API to find businesses with enhanced attributes.
"""
import requests
from typing import List, Dict, Optional
from discovery.base_discovery import DiscoverySource
from config.settings import SETTINGS
from storage.api_usage import get_tracker
from utils.logging_utils import get_logger

log = get_logger(__name__)


class GooglePlacesAPI(DiscoverySource):
    """
    Google Places API implementation for business discovery.
    
    API Docs: https://developers.google.com/maps/documentation/places/web-service/search-text
    Free tier: $200 credit per month (~2,000 calls at $0.10/call)
    """
    
    TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Places API client.
        
        Args:
            api_key: Google API key (defaults to SETTINGS.GOOGLE_API_KEY)
        """
        self.api_key = api_key or SETTINGS.GOOGLE_API_KEY
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        self.tracker = get_tracker()
        log.info("✅ Google Places API initialized")
    
    def fetch_leads(self, query: str, location: str, max_results: int = 50) -> List[Dict]:
        """
        Search for businesses using Google Places API.
        
        Args:
            query: Natural language search query - can be detailed (10-15 words)
                   Example: "established B2B SaaS development companies building enterprise 
                            project management tools Toronto GTA 50+ employees founded 2015 or earlier"
            location: City and state/province (e.g., "Toronto, ON") - can be empty if query includes location
            max_results: Maximum number of results (max: 60 with pagination)
        
        Returns:
            List of lead dictionaries with business data
        
        Note:
            Google Places API excels with detailed, context-rich natural language queries.
            The more specific the query, the better the results.
        """
        # Check quota before making API call
        if not self.tracker.can_use('google_places', count=1):
            remaining = self.tracker.get_remaining('google_places')
            log.warning(f"⚠️ Google Places API quota exhausted ({remaining}/2000 remaining this month)")
            log.warning("   Returning empty results. Will reset next month.")
            return []
        
        # Limit to 20 results (each page is up to 20, pagination costs more API calls)
        limit = min(max_results, 20)
        
        log.info(f"🔍 Google Places API: Searching for '{query}' in '{location}' (max {limit})")
        
        try:
            # Build request
            params = {
                'query': f"{query} in {location}",
                'key': self.api_key
            }
            
            # Make API call
            response = requests.get(
                self.TEXT_SEARCH_URL,
                params=params,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if data.get('status') not in ['OK', 'ZERO_RESULTS']:
                log.error(f"❌ Google Places API error: {data.get('status')} - {data.get('error_message', '')}")
                return []
            
            # Extract places
            places = data.get('results', [])
            
            if not places:
                log.warning(f"⚠️ Google Places API: No results found for '{query}' in '{location}'")
                return []
            
            log.info(f"✓ Google Places API: Found {len(places)} businesses")
            
            # Increment usage counter
            self.tracker.increment('google_places', count=1)
            remaining = self.tracker.get_remaining('google_places')
            log.info(f"   📊 Google Places quota: {remaining}/2000 remaining this month")
            
            # Map to lead dictionaries
            leads = []
            for place in places[:limit]:
                lead = self._map_to_lead(place, query)
                if lead:
                    leads.append(lead)
            
            return leads
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                log.error("❌ Google Places API: Rate limit exceeded (429)")
            elif e.response.status_code == 403:
                log.error("❌ Google Places API: Invalid API key or billing not enabled (403)")
            else:
                log.error(f"❌ Google Places API: HTTP error {e.response.status_code}")
            return []
            
        except requests.exceptions.RequestException as e:
            log.error(f"❌ Google Places API: Request failed: {e}")
            return []
            
        except Exception as e:
            log.error(f"❌ Google Places API: Unexpected error: {e}")
            return []
    
    def _map_to_lead(self, place: Dict, query: str) -> Optional[Dict]:
        """
        Map Google Places response to lead dictionary format.
        
        Args:
            place: Google Place object
            query: Original search query
        
        Returns:
            Lead dictionary or None if mapping failed
        """
        try:
            # Extract location components
            address_components = place.get('formatted_address', '').split(', ')
            
            # Try to parse city and state from address
            city = None
            state = None
            country = None
            
            if len(address_components) >= 3:
                city = address_components[-3] if len(address_components) > 2 else None
                state = address_components[-2].split()[0] if len(address_components) > 1 else None  # Extract "ON" from "ON M5H 2N2"
                country = address_components[-1] if address_components else None
            
            # Format phone number if available (Google returns formatted)
            phone = place.get('formatted_phone_number')
            if phone and phone.startswith('+1'):
                # Already in good format
                pass
            elif phone:
                # Try to normalize
                digits = ''.join(filter(str.isdigit, phone))
                if len(digits) == 10:
                    phone = f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
                elif len(digits) == 11 and digits[0] == '1':
                    phone = f"+1-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
            
            lead = {
                'business_name': place.get('name'),
                'website': None,  # Not in basic search, need details API
                'phone': phone,
                'city': city,
                'state': state,
                'country': country,
                'address': place.get('formatted_address'),
                'source_url': f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id')}",
                'discovery_method': 'google_places_api',
                'google_rating': place.get('rating'),
                'google_review_count': place.get('user_ratings_total'),
                'google_price_level': place.get('price_level'),  # 0-4 scale
                'google_place_id': place.get('place_id'),
                'notes': [f"Google Places search: '{query}'"]
            }
            
            log.debug(f"   Mapped: {lead['business_name']} | {lead['phone']} | {lead['city']}")
            
            return lead
            
        except Exception as e:
            log.warning(f"⚠️ Failed to map place: {e}")
            return None
