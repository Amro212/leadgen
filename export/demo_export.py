"""
Example usage of the new B2B lead export system.
Demonstrates CSV and XLSX export with the standardized schema.
"""
from models.lead import Lead
from export.csv_export import export_leads, get_export_stats, print_export_summary


def create_sample_lead(
    business_name: str,
    score: float,
    tier: str = "B",
    email: str = None,
    phone: str = None,
    website: str = None
) -> Lead:
    """Create a sample lead for testing."""
    lead = Lead(
        business_name=business_name,
        city="Toronto",
        region="ON",
        score=score,
        tier=tier,
    )
    
    if email:
        lead.emails = [email]
    
    if phone:
        lead.phone = phone
    
    if website:
        lead.website = website
    
    # Add some enrichment data
    lead.has_contact_form = True
    lead.has_booking = False
    lead.uses_https = website.startswith("https") if website else None
    lead.yelp_rating = 4.5
    lead.yelp_review_count = 127
    lead.yelp_categories = ["Digital Marketing", "Advertising"]
    lead.google_rating = 4.7
    lead.google_review_count = 89
    
    return lead


def main():
    """Demonstrate the new export system."""
    
    print("\n" + "="*60)
    print("🚀 B2B LEAD EXPORT DEMO")
    print("="*60)
    
    # Create sample leads
    leads = [
        create_sample_lead(
            "Acme Digital Agency",
            score=92.5,
            tier="A",
            email="contact@acmedigital.com",
            phone="4165551234",
            website="https://acmedigital.com"
        ),
        create_sample_lead(
            "BrightSpark Marketing",
            score=78.3,
            tier="B",
            email="hello@brightspark.ca",
            phone="416-555-5678",
            website="brightspark.ca"
        ),
        create_sample_lead(
            "Creative Solutions Inc",
            score=65.1,
            tier="C",
            email="info@creativesolutions.com",
            phone="+1 416 555 9012",
            website="http://creativesolutions.com"
        ),
        create_sample_lead(
            "Digital Dynamics",
            score=85.7,
            tier="A",
            email="team@digitaldynamics.io",
            phone="(416) 555-3456",
            website="https://digitaldynamics.io"
        ),
        create_sample_lead(
            "Innovation Labs",
            score=71.2,
            tier="B",
            email="contact@innovationlabs.ca",
            phone="416.555.7890",
            website="innovationlabs.ca"
        ),
    ]
    
    print(f"\n✅ Created {len(leads)} sample leads")
    
    # Demo 1: CSV Export (sorted by score)
    print("\n" + "-"*60)
    print("📄 DEMO 1: CSV Export (default)")
    print("-"*60)
    
    csv_path = export_leads(
        leads=leads,
        vertical="Digital Agencies",
        region="Toronto, ON",
        output_format="csv",
        sort_by_score=True
    )
    
    print(f"\n✅ CSV exported successfully!")
    print(f"   Path: {csv_path}")
    
    # Show stats
    print_export_summary(leads, csv_path)
    
    # Demo 2: XLSX Export (no sorting)
    print("\n" + "-"*60)
    print("📊 DEMO 2: XLSX Export (with styling, unsorted)")
    print("-"*60)
    
    try:
        xlsx_path = export_leads(
            leads=leads,
            vertical="Digital Agencies",
            region="Toronto, ON",
            output_format="xlsx",
            sort_by_score=False
        )
        
        print(f"\n✅ XLSX exported successfully!")
        print(f"   Path: {xlsx_path}")
        print(f"   Features: Styled headers, auto-width, filters, frozen header")
        
    except Exception as e:
        print(f"\n⚠️  XLSX export failed: {e}")
        print(f"   Install openpyxl: pip install openpyxl")
    
    # Demo 3: Statistics
    print("\n" + "-"*60)
    print("📈 DEMO 3: Export Statistics")
    print("-"*60)
    
    stats = get_export_stats(leads)
    
    print(f"\nLead Quality Distribution:")
    print(f"  Tier A (85-100): {stats['tier_a']} leads")
    print(f"  Tier B (65-84):  {stats['tier_b']} leads")
    print(f"  Tier C (0-64):   {stats['tier_c']} leads")
    
    print(f"\nEnrichment Coverage:")
    print(f"  Email: {stats['with_email']}/{stats['total_leads']} ({stats['with_email']/stats['total_leads']*100:.0f}%)")
    print(f"  Phone: {stats['with_phone']}/{stats['total_leads']} ({stats['with_phone']/stats['total_leads']*100:.0f}%)")
    print(f"  Website: {stats['with_website']}/{stats['total_leads']} ({stats['with_website']/stats['total_leads']*100:.0f}%)")
    
    print("\n" + "="*60)
    print("✅ Demo complete! Check the output folder for files.")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
