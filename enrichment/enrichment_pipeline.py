"""
Enrichment pipeline that orchestrates website scraping for all leads.
"""
from typing import List, Dict, Optional
from enrichment.base_enrichment import EnrichmentSource
from enrichment.website_scraper import WebsiteScraper
from utils.logging_utils import get_logger

log = get_logger(__name__)

# Hunter.io is optional (only for Tier A leads)
try:
    from enrichment.hunter_email_finder import HunterEmailFinder
    HUNTER_AVAILABLE = True
except Exception as e:
    log.warning(f"⚠️ Hunter.io not available: {e}")
    HUNTER_AVAILABLE = False


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
                        # Set primary email
                        enriched_lead['email'] = signals['emails'][0]
                    
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


def enrich_leads(leads: List[Dict], use_hunter: bool = True) -> List[Dict]:
    """
    Convenience function to enrich leads.
    Applies website scraping to all leads, then Hunter.io to Tier A leads only.
    
    Args:
        leads: List of lead dictionaries
        use_hunter: Whether to use Hunter.io for email verification (default: True)
    
    Returns:
        List of enriched lead dictionaries
    """
    # Step 1: Website scraping (all leads)
    enrichment = WebsiteEnrichment()
    enriched_leads = enrichment.enrich(leads)
    
    # Step 2: Hunter.io email verification (Tier A leads only, if available)
    if use_hunter and HUNTER_AVAILABLE:
        enriched_leads = _apply_hunter_enrichment(enriched_leads)
    
    return enriched_leads


def _apply_hunter_enrichment(leads: List[Dict]) -> List[Dict]:
    """
    Apply Hunter.io email enrichment to Tier A leads only.
    
    Args:
        leads: List of enriched lead dictionaries
    
    Returns:
        List of leads with Hunter.io data (Tier A only)
    """
    try:
        hunter = HunterEmailFinder()
    except Exception as e:
        log.warning(f"⚠️ Hunter.io initialization failed: {e}")
        return leads
    
    # Filter for Tier A leads (score >= 65)
    tier_a_leads = [lead for lead in leads if lead.get('score', 0) >= 65]
    
    if not tier_a_leads:
        log.info("ℹ️ No Tier A leads found - skipping Hunter.io enrichment")
        return leads
    
    log.info(f"🔍 Hunter.io: Enriching {len(tier_a_leads)} Tier A leads (score >= 65)")
    
    enriched_count = 0
    for lead in leads:
        # Only enrich Tier A leads with a website
        if lead.get('score', 0) >= 65 and lead.get('website'):
            website = lead['website']
            business_name = lead.get('business_name', 'Unknown')
            
            # Find emails via Hunter.io
            result = hunter.find_emails(website, business_name)
            
            # Update lead with Hunter.io data
            if result['emails']:
                # Merge with existing emails (preserve scraped emails)
                existing_emails = lead.get('emails', [])
                all_emails = list(set(existing_emails + result['emails']))
                lead['emails'] = all_emails
                
                # Update primary email if Hunter found one with higher confidence
                if result['primary_email'] and not lead.get('email'):
                    lead['email'] = result['primary_email']
                
                enriched_count += 1
            
            # Add Hunter.io metadata
            lead['emails_verified'] = result['emails_verified']
            lead['email_confidence'] = result['email_confidence']
            lead['hunter_verified'] = True
            
            # Add note
            if 'notes' not in lead:
                lead['notes'] = []
            if result['emails']:
                lead['notes'].append(f"Hunter.io: Found {len(result['emails'])} emails (confidence: {result['email_confidence']}%)")
            else:
                lead['notes'].append("Hunter.io: No emails found")
    
    log.info(f"✓ Hunter.io: Enriched {enriched_count}/{len(tier_a_leads)} Tier A leads with verified emails")
    
    return leads
