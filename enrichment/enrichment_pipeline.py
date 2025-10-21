"""
Enrichment pipeline that orchestrates website scraping for all leads.
"""
from typing import List, Dict
from enrichment.base_enrichment import EnrichmentSource
from enrichment.website_scraper import WebsiteScraper
from utils.logging_utils import get_logger

log = get_logger(__name__)


class WebsiteEnrichment(EnrichmentSource):
    """
    Enrichment source that uses website scraping to extract signals.
    """
    
    def __init__(self):
        self.scraper = WebsiteScraper()
    
    def enrich(self, leads: List[Dict]) -> List[Dict]:
        """
        Enrich leads by scraping their websites.
        
        Args:
            leads: List of lead dictionaries
        
        Returns:
            List of enriched lead dictionaries
        """
        log.info(f"Enriching {len(leads)} leads...")
        
        enriched_leads = []
        success_count = 0
        error_count = 0
        
        for lead in leads:
            enriched_lead = lead.copy()
            
            # Only enrich if lead has a website
            if lead.get('website'):
                website = lead['website']
                
                try:
                    # Scrape website for signals
                    signals = self.scraper.scrape_website(website)
                    
                    # Merge signals into lead (preserve existing data)
                    if signals['emails']:
                        enriched_lead['emails'] = signals['emails']
                    
                    if signals['has_contact_form'] is not None:
                        enriched_lead['has_contact_form'] = signals['has_contact_form']
                    
                    if signals['has_booking'] is not None:
                        enriched_lead['has_booking'] = signals['has_booking']
                    
                    if signals['has_emergency_service'] is not None:
                        enriched_lead['has_emergency_service'] = signals['has_emergency_service']
                    
                    if signals['has_financing'] is not None:
                        enriched_lead['has_financing'] = signals['has_financing']
                    
                    if signals['uses_https'] is not None:
                        enriched_lead['uses_https'] = signals['uses_https']
                    
                    if signals['tech_stack']:
                        enriched_lead['tech_stack'] = signals['tech_stack']
                    
                    # Store enrichment signals
                    if 'signals' not in enriched_lead:
                        enriched_lead['signals'] = {}
                    enriched_lead['signals']['website_scraped'] = True
                    
                    # Add notes if any
                    if signals['notes']:
                        if 'notes' not in enriched_lead:
                            enriched_lead['notes'] = []
                        enriched_lead['notes'].extend(signals['notes'])
                    
                    # Track success if we got meaningful data
                    if signals['emails'] or signals['has_contact_form']:
                        success_count += 1
                    
                except Exception as e:
                    log.error(f"Error enriching lead {lead.get('business_name')}: {e}")
                    error_count += 1
                    
                    # Add error note
                    if 'notes' not in enriched_lead:
                        enriched_lead['notes'] = []
                    enriched_lead['notes'].append(f"Enrichment error: {str(e)}")
            
            else:
                # No website to scrape
                if 'notes' not in enriched_lead:
                    enriched_lead['notes'] = []
                enriched_lead['notes'].append("No website to enrich")
            
            enriched_leads.append(enriched_lead)
        
        log.info(f"Enrichment complete: {success_count} successful, {error_count} errors, "
                f"{len(leads) - success_count - error_count} skipped")
        
        return enriched_leads


def enrich_leads(leads: List[Dict]) -> List[Dict]:
    """
    Convenience function to enrich leads.
    
    Args:
        leads: List of lead dictionaries
    
    Returns:
        List of enriched lead dictionaries
    """
    enrichment = WebsiteEnrichment()
    return enrichment.enrich(leads)
