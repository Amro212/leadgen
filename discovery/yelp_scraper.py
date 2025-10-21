"""
Yelp profile scraper for enriching discovery data.

Note: Yelp blocks direct scraping with 403 errors.
For MVP, this module validates and enriches sample data.
For production, upgrade to Yelp Fusion API (T25).
"""
import time
from typing import Dict, Optional
from utils.logging_utils import get_logger

log = get_logger(__name__)


class YelpScraper:
    """
    Yelp profile data extractor (stub for MVP).
    
    In production, replace with Yelp Fusion API calls.
    """
    
    def __init__(self):
        self.delay = 0.5
    
    def scrape_profile(self, yelp_url: str) -> Dict:
        """
        Extract business details from a Yelp profile URL.
        
        Args:
            yelp_url: Full Yelp business page URL
        
        Returns:
            Dictionary with business details (name, city, phone, website)
            Returns empty dict if scraping fails.
        """
        log.debug(f"Processing Yelp URL: {yelp_url}")
        
        # For MVP: Since we can't actually scrape, return placeholder
        # In T25, this will make real API calls
        
        try:
            # Extract business slug from URL
            if '/biz/' in yelp_url:
                slug = yelp_url.split('/biz/')[-1].split('?')[0]
                
                # Parse slug for basic info (e.g., "business-name-city")
                parts = slug.split('-')
                
                # This is a stub - real implementation would fetch from Yelp
                result = {
                    "yelp_url": yelp_url,
                    "notes": ["Stub data - upgrade to Yelp API (T25) for real scraping"]
                }
                
                time.sleep(self.delay)
                return result
            else:
                log.warning(f"Invalid Yelp URL format: {yelp_url}")
                return {}
                
        except Exception as e:
            log.error(f"Failed to process Yelp URL: {e}")
            return {}
    
    def enrich_lead(self, lead: Dict) -> Dict:
        """
        Enrich a lead dictionary with Yelp profile data.
        
        Args:
            lead: Lead dictionary from discovery
        
        Returns:
            Enriched lead dictionary
        """
        if not lead.get('source_url'):
            log.debug(f"No source URL for {lead.get('business_name', 'Unknown')}")
            return lead
        
        # Scrape the Yelp profile
        profile_data = self.scrape_profile(lead['source_url'])
        
        # Merge profile data into lead (without overwriting existing data)
        for key, value in profile_data.items():
            if key not in lead or lead[key] is None:
                lead[key] = value
        
        return lead
