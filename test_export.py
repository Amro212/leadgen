"""
Quick test to verify XLSX export works correctly without using APIs.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.lead import Lead
from export.csv_export import export_leads


def main():
    print("=" * 60)
    print("🧪 TESTING XLSX EXPORT (No API calls)")
    print("=" * 60)
    print()
    
    # Create 3 sample leads
    leads = []
    
    # Lead 1: Tier A
    lead1 = Lead(
        business_name="Test Restaurant Austin",
        city="Austin",
        region="TX",
        score=75,
        tier="B"
    )
    lead1.phone = "+1-512-555-1234"
    lead1.emails = ["contact@testrestaurant.com"]
    lead1.website = "https://testrestaurant.com"
    leads.append(lead1)
    
    # Lead 2: Tier B
    lead2 = Lead(
        business_name="Sample Bar & Grill",
        city="Austin",
        region="TX",
        score=65,
        tier="B"
    )
    lead2.phone = "+1-512-555-5678"
    lead2.website = "https://samplebar.com"
    leads.append(lead2)
    
    # Lead 3: Tier C
    lead3 = Lead(
        business_name="Local Brewery",
        city="Austin",
        region="TX",
        score=45,
        tier="C"
    )
    lead3.phone = "+1-512-555-9999"
    leads.append(lead3)
    
    print(f"✅ Created {len(leads)} sample leads")
    print()
    
    # Export to CSV
    print("📄 Exporting to CSV...")
    csv_path = export_leads(
        leads=leads,
        vertical="Test",
        region="Austin",
        output_format="csv",
        sort_by_score=True
    )
    print(f"   ✅ CSV: {csv_path}")
    print()
    
    # Export to XLSX
    print("📊 Exporting to XLSX...")
    try:
        xlsx_path = export_leads(
            leads=leads,
            vertical="Test",
            region="Austin",
            output_format="xlsx",
            sort_by_score=True
        )
        print(f"   ✅ XLSX: {xlsx_path}")
        
        # Verify file was created and has content
        from pathlib import Path
        xlsx_file = Path(xlsx_path)
        if xlsx_file.exists():
            size = xlsx_file.stat().st_size
            print(f"   📏 File size: {size:,} bytes")
            
            if size < 1000:
                print("   ⚠️  WARNING: File size is suspiciously small!")
            else:
                print("   ✅ File size looks good")
        else:
            print("   ❌ ERROR: XLSX file was not created!")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("✅ Test complete! Check the output folder.")
    print("=" * 60)


if __name__ == "__main__":
    main()
