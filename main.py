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


def discovery_stage(vertical: str, region: str, max_results: int) -> List[Dict]:
    """
    Discovery stage: Find businesses based on vertical and location.
    
    Args:
        vertical: Business category (e.g., "HVAC")
        region: Geographic location (e.g., "Milton, Ontario")
        max_results: Maximum number of leads to discover
    
    Returns:
        List of raw lead dictionaries
    """
    log.info(f"🔍 Discovery: Searching for '{vertical}' in '{region}'")
    
    # Use aggregator to discover and dedupe leads (T08-T10)
    leads = discover_leads(vertical, region, max_results)
    
    log.info(f"✓ Discovery complete: Found {len(leads)} unique leads")
    return leads


def enrichment_stage(leads: List[Dict]) -> List[Dict]:
    """
    Enrichment stage: Add additional data to leads.
    
    Args:
        leads: Raw lead dictionaries from discovery
    
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


def export_stage(leads: List[Lead], vertical: str, region: str) -> None:
    """
    Export stage: Save leads to CSV and generate reports.
    
    Args:
        leads: Scored Lead objects
        vertical: Business vertical for filename
        region: Region for filename
    """
    log.info(f"💾 Export: Saving {len(leads)} leads")
    
    from export.csv_export import export_to_csv, get_export_stats
    from export.report_generator import generate_summary_report
    
    # Export to CSV
    csv_path = export_to_csv(leads, vertical, region)
    
    # Generate summary report
    report_path = generate_summary_report(leads, vertical, region, csv_path)
    
    # Get and log statistics
    stats = get_export_stats(leads)
    log.info(f"✓ Export complete:")
    log.info(f"  📄 CSV: {csv_path}")
    log.info(f"  📊 Report: {report_path}")
    log.info(f"  📈 Stats: {stats['total_leads']} leads, "
            f"A={stats['tier_a']}, B={stats['tier_b']}, C={stats['tier_c']}, "
            f"Avg={stats['avg_score']}")


def run_pipeline(vertical: str, region: str, max_results: int = 25) -> None:
    """
    Run the full lead generation pipeline.
    
    Args:
        vertical: Business category
        region: Geographic location
        max_results: Maximum leads to process
    """
    log.info("=" * 60)
    log.info(f"🚀 Starting Lead Generation Pipeline")
    log.info(f"   Vertical: {vertical}")
    log.info(f"   Region: {region}")
    log.info(f"   Max Results: {max_results}")
    log.info("=" * 60)
    
    try:
        # Stage 1: Discovery
        raw_leads = discovery_stage(vertical, region, max_results)
        
        # Stage 2: Enrichment
        enriched_leads = enrichment_stage(raw_leads)
        
        # Stage 3: Scoring
        scored_leads = scoring_stage(enriched_leads)
        
        # Stage 4: Hunter.io (Tier A only)
        verified_leads = hunter_enrichment_stage(scored_leads)
        
        # Stage 5: Export
        export_stage(verified_leads, vertical, region)
        
        log.success("🎉 Pipeline completed successfully!")
        
    except Exception as e:
        log.error(f"❌ Pipeline failed: {e}")
        raise


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Lead Generation System - Discover, enrich, and score business leads"
    )
    
    parser.add_argument(
        "--vertical",
        type=str,
        required=True,
        help="Business vertical/category (e.g., 'HVAC', 'Plumber')"
    )
    
    parser.add_argument(
        "--region",
        type=str,
        required=True,
        help="Geographic region (e.g., 'Milton, Ontario')"
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
        vertical=args.vertical,
        region=args.region,
        max_results=args.max
    )


if __name__ == "__main__":
    main()
