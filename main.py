"""
Lead Generation System - Main Orchestrator
Entry point for the lead generation pipeline.
"""
import argparse
from typing import List, Dict
from utils.logging_utils import get_logger
from models.lead import Lead
from discovery.aggregator import discover_leads

# Initialize logger
log = get_logger(__name__)


def discovery_stage(company_brief: str, max_results: int) -> List[Dict]:
    """
    Discovery stage: PRECISION AI-powered search with structured API parameters.
    
    Args:
        company_brief: 2-3 sentence company description (AI generates precise strategy)
        max_results: Maximum number of leads to discover
    
    Returns:
        List of raw lead dictionaries
    """
    log.info(f"🔍 Discovery: Generating PRECISION search strategy...")
    
    # Step 1: Generate AI-powered PRECISION search strategy
    from outreach.query_generator import QueryGenerator
    
    query_gen = QueryGenerator()
    strategy = query_gen.generate_search_strategy(company_brief)
    
    # Step 2: Execute SINGLE precision search using structured parameters
    log.info(f"🎯 Executing precision-targeted search...")
    
    from discovery.aggregator import DiscoveryAggregator
    aggregator = DiscoveryAggregator()
    
    # Use the new structured discovery method
    leads = aggregator.discover_structured(
        yelp_params=strategy['yelp_search'],
        google_query=strategy['google_places_search']['query'],
        max_results=max_results
    )
    
    log.info(f"✓ Discovery complete: Found {len(leads)} precision-targeted leads")
    
    return leads[:max_results]


def website_discovery_stage(leads: List[Dict]) -> List[Dict]:
    """
    Website discovery stage: Find actual business websites using multiple APIs.
    
    Args:
        leads: Raw lead dictionaries from discovery (may have Yelp URLs or None)
    
    Returns:
        Leads with actual business websites discovered
    """
    log.info(f"🌐 Website Discovery: Finding actual websites for {len(leads)} leads...")
    
    from enrichment.website_discovery import WebsiteDiscovery
    discoverer = WebsiteDiscovery()
    leads_with_websites = discoverer.discover_websites(leads)
    
    websites_found = sum(1 for lead in leads_with_websites if lead.get('website') and 'yelp.com' not in (lead.get('website') or '').lower())
    log.info(f"✓ Website Discovery: Found {websites_found}/{len(leads)} actual websites")
    
    return leads_with_websites


def enrichment_stage(leads: List[Dict]) -> List[Dict]:
    """
    Enrichment stage: Add additional data to leads (website scraping, etc.).
    
    Args:
        leads: Lead dictionaries with actual websites discovered
    
    Returns:
        Enriched lead dictionaries
    """
    log.info(f"🔬 Enrichment: Processing {len(leads)} leads")
    
    from enrichment.enrichment_pipeline import enrich_leads
    enriched = enrich_leads(leads)
    
    log.info(f"✓ Enrichment complete: {len(enriched)} leads processed")
    return enriched


def scoring_stage(leads: List[Dict]) -> List[Lead]:
    """
    Scoring stage: Score and tier leads.
    
    Args:
        leads: Enriched lead dictionaries
    
    Returns:
        List of scored Lead objects
    """
    log.info(f"📊 Scoring: Evaluating {len(leads)} leads")
    
    from scoring.scoring_engine import score_lead
    
    scored_leads = []
    tier_counts = {"A": 0, "B": 0, "C": 0}
    
    for lead_dict in leads:
        # Calculate score and tier
        scoring_result = score_lead(lead_dict)
        
        # Add score and tier to dict
        lead_dict['score'] = scoring_result['score']
        lead_dict['tier'] = scoring_result['tier']
        
        # Convert to Lead object
        lead = Lead(**lead_dict)
        scored_leads.append(lead)
        
        # Count tiers
        tier_counts[lead.tier] += 1
    
    log.info(f"✓ Scoring complete: A={tier_counts['A']}, B={tier_counts['B']}, C={tier_counts['C']}")
    return scored_leads


def hunter_enrichment_stage(leads: List[Lead]) -> List[Lead]:
    """
    Hunter.io enrichment stage: Verify emails for Tier A leads only.
    
    Args:
        leads: Scored Lead objects
    
    Returns:
        List of leads with Hunter.io data (Tier A only enriched)
    """
    # Check if Hunter.io is available
    try:
        from enrichment.hunter_email_finder import HunterEmailFinder
        from storage.api_usage import get_tracker
        
        tracker = get_tracker()
        if not tracker.can_use('hunter', count=1):
            log.info("⚠️ Hunter.io quota exhausted - skipping email verification")
            return leads
        
        # Count Tier A leads
        tier_a_leads = [lead for lead in leads if lead.tier == 'A']
        
        if not tier_a_leads:
            log.info("ℹ️ No Tier A leads found - skipping Hunter.io enrichment")
            return leads
        
        log.info(f"🔍 Hunter.io: Enriching {len(tier_a_leads)} Tier A leads")
        
        hunter = HunterEmailFinder()
        enriched_count = 0
        
        for lead in tier_a_leads:
            if lead.website:
                # Find emails via Hunter.io
                result = hunter.find_emails(lead.website, lead.business_name)
                
                # Update lead with Hunter.io data
                if result['emails']:
                    # Merge with existing emails
                    existing_emails = lead.emails or []
                    all_emails = list(set(existing_emails + result['emails']))
                    lead.emails = all_emails
                    
                    # Update primary email if Hunter found one
                    if result['primary_email'] and not lead.email:
                        lead.email = result['primary_email']
                    
                    enriched_count += 1
                
                # Add Hunter.io metadata
                lead.emails_verified = result['emails_verified']
                lead.email_confidence = result['email_confidence']
                lead.hunter_verified = True
                
                # Add note
                if result['emails']:
                    lead.notes.append(f"Hunter.io: Found {len(result['emails'])} emails (confidence: {result['email_confidence']}%)")
                else:
                    lead.notes.append("Hunter.io: No emails found")
        
        log.info(f"✓ Hunter.io: Enriched {enriched_count}/{len(tier_a_leads)} Tier A leads with verified emails")
        
    except Exception as e:
        log.warning(f"⚠️ Hunter.io enrichment failed: {e}")
    
    return leads


def tavily_research_stage(leads: List[Lead]) -> List[Lead]:
    """
    Tavily deep research stage: Verify business & find actual website for Tier A leads.
    
    Args:
        leads: Scored Lead objects (after Hunter.io)
    
    Returns:
        List of leads with Tavily research data (Tier A only enriched)
    """
    try:
        from enrichment.tavily_researcher import TavilyResearcher
        from storage.api_usage import get_tracker
        
        tracker = get_tracker()
        if not tracker.can_use('tavily', count=1):
            log.info("⚠️ Tavily quota exhausted - skipping deep research")
            return leads
        
        # Count Tier A leads
        tier_a_leads = [lead for lead in leads if lead.tier == 'A']
        
        if not tier_a_leads:
            log.info("ℹ️ No Tier A leads found - skipping Tavily research")
            return leads
        
        log.info(f"🔍 Tavily: Researching {len(tier_a_leads)} Tier A leads")
        
        tavily = TavilyResearcher()
        researched_count = 0
        
        for lead in tier_a_leads:
            # Research business (finds website, reviews, reputation)
            result = tavily.research_business(
                business_name=lead.business_name,
                city=lead.city or "",
                website=lead.website
            )
            
            # Update lead with Tavily data
            if result['tavily_verified']:
                # Update website if Tavily found a better one
                if result['verified_website'] and 'yelp.com' not in (lead.website or ""):
                    # Only override if current website is Yelp or empty
                    if not lead.website or 'yelp.com' in lead.website:
                        lead.website = result['verified_website']
                        lead.notes.append(f"Tavily: Found actual website - {result['verified_website']}")
                    else:
                        # Store as alternative if different
                        if result['verified_website'] != lead.website:
                            lead.tavily_website_found = result['verified_website']
                
                researched_count += 1
            
            # Add Tavily metadata
            lead.tavily_verified = result['tavily_verified']
            lead.tavily_website_found = result['verified_website']
            lead.tavily_recent_activity = result['recent_activity']
            lead.tavily_reputation_score = result['reputation_score']
            lead.tavily_sources_found = result['sources_found']
            lead.tavily_review_sites = result['review_sites']
            lead.tavily_negative_flags = result['negative_flags']
            
            # Add summary note
            if result['tavily_verified']:
                summary_parts = []
                if result['verified_website']:
                    summary_parts.append(f"Website verified")
                if result['recent_activity']:
                    summary_parts.append("Recent activity")
                if result['reputation_score']:
                    summary_parts.append(f"Reputation: {result['reputation_score']}/100")
                if result['sources_found']:
                    summary_parts.append(f"{result['sources_found']} sources")
                
                summary = f"Tavily: {', '.join(summary_parts)}"
                lead.notes.append(summary)
                
                # Warn about negative flags
                if result['negative_flags']:
                    lead.notes.append(f"⚠️ Tavily: {len(result['negative_flags'])} negative flags found")
        
        log.info(f"✓ Tavily: Researched {researched_count}/{len(tier_a_leads)} Tier A leads")
        
    except Exception as e:
        log.warning(f"⚠️ Tavily research failed: {e}")
    
    return leads


def export_stage(leads: List[Lead], company_brief: str) -> None:
    """
    Export stage: Save leads to CSV and generate reports.
    
    Args:
        leads: Scored Lead objects
        company_brief: Company description for filename context
    """
    log.info(f"💾 Export: Saving {len(leads)} leads")
    
    from export.csv_export import export_leads, get_export_stats
    from export.report_generator import generate_summary_report
    
    # Create simplified identifiers from company brief for filenames
    # Use first few words as context
    brief_words = company_brief.split()[:3]
    vertical = " ".join(brief_words)  # Use first 3 words as vertical
    region = "Leads"  # Generic region since we're using AI briefs
    
    # Export to CSV (universal compatibility)
    csv_path = export_leads(
        leads=leads,
        vertical=vertical,
        region=region,
        output_format="csv",
        sort_by_score=True
    )
    
    # Export to XLSX (professional styling)
    xlsx_path = export_leads(
        leads=leads,
        vertical=vertical,
        region=region,
        output_format="xlsx",
        sort_by_score=True
    )
    
    # Generate summary report
    report_path = generate_summary_report(leads, vertical, region, csv_path)
    
    # Get and log statistics
    stats = get_export_stats(leads)
    log.info(f"✓ Export complete:")
    log.info(f"  📄 CSV: {csv_path}")
    log.info(f"  📊 XLSX: {xlsx_path}")
    log.info(f"  📋 Report: {report_path}")
    log.info(f"  📈 Stats: {stats['total_leads']} leads, "
            f"A={stats['tier_a']}, B={stats['tier_b']}, C={stats['tier_c']}, "
            f"Avg={stats['avg_score']}")


def run_pipeline(company_brief: str, max_results: int = 25) -> None:
    """
    Run the full lead generation pipeline.
    
    Args:
        company_brief: 2-3 sentence description of company and lead requirements
        max_results: Maximum leads to process
    """
    log.info("=" * 60)
    log.info(f"🚀 Starting AI-Powered Lead Generation Pipeline")
    log.info(f"   Company Brief: {company_brief}")
    log.info(f"   Max Results: {max_results}")
    log.info("=" * 60)
    
    try:
        # Stage 1: Discovery (AI-powered query generation)
        raw_leads = discovery_stage(company_brief, max_results)
        
        # Stage 2: Website Discovery (find actual business websites)
        leads_with_websites = website_discovery_stage(raw_leads)
        
        # Stage 3: Enrichment (website scraping, contact forms, etc.)
        enriched_leads = enrichment_stage(leads_with_websites)
        
        # Stage 4: Scoring (score leads based on enrichment data)
        scored_leads = scoring_stage(enriched_leads)
        
        # Stage 5: Hunter.io (Tier A only - email discovery)
        verified_leads = hunter_enrichment_stage(scored_leads)
        
        # Stage 6: Tavily Deep Research (Tier A only - reputation, verification)
        researched_leads = tavily_research_stage(verified_leads)
        
        # Stage 7: Export
        export_stage(researched_leads, company_brief)
        
        log.success("🎉 Pipeline completed successfully!")
        
    except Exception as e:
        log.error(f"❌ Pipeline failed: {e}")
        raise


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Lead Generation System - AI-powered lead discovery, enrichment, and scoring"
    )
    
    parser.add_argument(
        "--company-brief",
        type=str,
        required=True,
        help="2-3 sentence description of your company and lead requirements (e.g., 'Toronto SaaS company selling project management tools to construction firms')"
    )
    
    parser.add_argument(
        "--max",
        type=int,
        default=25,
        help="Maximum number of leads to process (default: 25)"
    )
    
    args = parser.parse_args()
    
    # Run the pipeline
    run_pipeline(
        company_brief=args.company_brief,
        max_results=args.max
    )


if __name__ == "__main__":
    main()
