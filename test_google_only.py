"""
Test script to use ONLY Google Places API for lead generation.
Bypasses Yelp completely to test Google Places extraction.
"""
from discovery.google_places_api import GooglePlacesAPI
from models.lead import Lead
from export.csv_export import export_to_csv
from export.report_generator import generate_summary_report
from scoring.scoring_engine import score_lead
from utils.logging_utils import get_logger
from datetime import datetime

log = get_logger(__name__)


def main():
    print("\n" + "="*70)
    print("🧪 GOOGLE PLACES ONLY TEST")
    print("   Testing Google Places API exclusively (no Yelp)")
    print("="*70 + "\n")
    
    # Initialize Google Places API
    try:
        google_api = GooglePlacesAPI()
        log.info("✅ Google Places API initialized")
    except Exception as e:
        log.error(f"❌ Failed to initialize Google Places API: {e}")
        return
    
    # Fetch leads from Google Places ONLY
    query = "Digital Agencies"
    location = "Toronto, ON"
    max_results = 10
    
    log.info(f"🔍 Searching for '{query}' in '{location}' (max {max_results})")
    
    raw_leads = google_api.fetch_leads(query, location, max_results)
    
    if not raw_leads:
        log.error("❌ No leads returned from Google Places API")
        return
    
    log.info(f"✓ Google Places returned {len(raw_leads)} leads")
    
    # Convert to Lead objects
    leads = []
    for raw_lead in raw_leads:
        try:
            lead = Lead(**raw_lead)
            leads.append(lead)
        except Exception as e:
            log.warning(f"⚠️ Failed to create Lead object: {e}")
    
    log.info(f"✓ Created {len(leads)} Lead objects")
    
    # Score the leads
    for lead in leads:
        score_result = score_lead(lead)
        lead.score = score_result['score']
        lead.tier = score_result['tier']
    
    log.info(f"✓ Scored {len(leads)} leads")
    
    # Count tiers
    tier_counts = {"A": 0, "B": 0, "C": 0}
    for lead in leads:
        if lead.tier:
            tier_counts[lead.tier] = tier_counts.get(lead.tier, 0) + 1
    
    log.info(f"📊 Tiers: A={tier_counts['A']}, B={tier_counts['B']}, C={tier_counts['C']}")
    
    # Export to CSV
    csv_path = export_to_csv(leads, query, location)
    log.info(f"✓ Exported to: {csv_path}")
    
    # Generate report
    report_path = generate_summary_report(
        leads=leads,
        vertical=query,
        region=location,
        csv_filepath=csv_path
    )
    log.info(f"✓ Report generated: {report_path}")
    
    # Print sample data
    print("\n" + "="*70)
    print("📊 SAMPLE LEADS FROM GOOGLE PLACES:")
    print("="*70)
    for i, lead in enumerate(leads[:3], 1):
        print(f"\n{i}. {lead.business_name}")
        print(f"   Phone: {lead.phone or 'N/A'}")
        print(f"   City: {lead.city or 'N/A'}")
        print(f"   Google Rating: {lead.google_rating or 'N/A'}")
        print(f"   Google Reviews: {lead.google_review_count or 'N/A'}")
        print(f"   Google Price: {lead.google_price_level if lead.google_price_level is not None else 'N/A'}")
        print(f"   Score: {lead.score} (Tier {lead.tier})")
        print(f"   Discovery: {lead.discovery_method}")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE!")
    print(f"   📄 CSV: {csv_path}")
    print(f"   📊 Report: {report_path}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
