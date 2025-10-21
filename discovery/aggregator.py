"""
Discovery aggregator - combines and deduplicates leads from multiple sources.
"""
from typing import List, Dict, Set
from urllib.parse import urlparse
from utils.logging_utils import get_logger
from discovery.google_scraper import GoogleScraper
from discovery.yelp_scraper import YelpScraper

log = get_logger(__name__)


class DiscoveryAggregator:
    """
    Aggregates leads from multiple discovery sources and deduplicates.
    """
    
    def __init__(self):
        self.google_scraper = GoogleScraper()
        self.yelp_scraper = YelpScraper()
    
    def discover_and_aggregate(
        self,
        query: str,
        location: str,
        max_results: int = 25
    ) -> List[Dict]:
        """
        Discover businesses and aggregate results.
        
        Args:
            query: Business vertical
            location: Geographic location
            max_results: Maximum leads to return
        
        Returns:
            List of unique, enriched lead dictionaries
        """
        log.info(f"Starting aggregated discovery for '{query}' in '{location}'")
        
        # Step 1: Get initial leads from Google/search
        raw_leads = self.google_scraper.fetch_leads(query, location, max_results)
        log.info(f"Initial discovery returned {len(raw_leads)} leads")
        
        # Step 2: Enrich with Yelp profile data
        enriched_leads = []
        for lead in raw_leads:
            enriched = self.yelp_scraper.enrich_lead(lead)
            enriched_leads.append(enriched)
        
        log.info(f"Enriched {len(enriched_leads)} leads with profile data")
        
        # Step 3: Deduplicate
        unique_leads = self._deduplicate(enriched_leads)
        log.info(f"After deduplication: {len(unique_leads)} unique leads")
        
        # Step 4: Normalize data
        normalized_leads = [self._normalize_lead(lead) for lead in unique_leads]
        
        return normalized_leads[:max_results]
    
    def _deduplicate(self, leads: List[Dict]) -> List[Dict]:
        """
        Remove duplicate leads based on website domain or name+phone.
        
        Args:
            leads: List of lead dictionaries
        
        Returns:
            Deduplicated list
        """
        seen_identifiers: Set[str] = set()
        unique_leads = []
        
        for lead in leads:
            # Create unique identifier
            identifiers = []
            
            # 1. By website domain
            if lead.get('website'):
                domain = self._extract_domain(lead['website'])
                if domain:
                    identifiers.append(f"domain:{domain}")
            
            # 2. By name + phone
            if lead.get('business_name') and lead.get('phone'):
                name_phone = f"name_phone:{lead['business_name'].lower()}:{lead['phone']}"
                identifiers.append(name_phone)
            
            # 3. By source URL
            if lead.get('source_url'):
                identifiers.append(f"url:{lead['source_url']}")
            
            # Check if any identifier was seen before
            is_duplicate = False
            for identifier in identifiers:
                if identifier in seen_identifiers:
                    is_duplicate = True
                    log.debug(f"Duplicate found: {lead.get('business_name')} ({identifier})")
                    break
            
            if not is_duplicate:
                # Add all identifiers to seen set
                for identifier in identifiers:
                    seen_identifiers.add(identifier)
                unique_leads.append(lead)
        
        duplicates_removed = len(leads) - len(unique_leads)
        if duplicates_removed > 0:
            log.info(f"Removed {duplicates_removed} duplicates")
        
        return unique_leads
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return ""
    
    def _normalize_lead(self, lead: Dict) -> Dict:
        """
        Normalize lead data (lowercase domains, clean phone, etc.).
        
        Args:
            lead: Lead dictionary
        
        Returns:
            Normalized lead dictionary
        """
        # Normalize website URL
        if lead.get('website'):
            website = lead['website'].lower().strip()
            # Ensure it has a scheme
            if not website.startswith('http'):
                website = f"https://{website}"
            lead['website'] = website
        
        # Normalize phone (remove spaces, dashes if needed for comparison)
        if lead.get('phone'):
            lead['phone'] = lead['phone'].strip()
        
        # Normalize business name (title case)
        if lead.get('business_name'):
            lead['business_name'] = lead['business_name'].strip()
        
        return lead


# Convenience function for main.py
def discover_leads(query: str, location: str, max_results: int = 25) -> List[Dict]:
    """
    Main discovery function - aggregates from all sources.
    
    Args:
        query: Business vertical
        location: Geographic location  
        max_results: Maximum leads to return
    
    Returns:
        List of unique lead dictionaries
    """
    aggregator = DiscoveryAggregator()
    return aggregator.discover_and_aggregate(query, location, max_results)
