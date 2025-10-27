"""Quick test script to verify Google Places API connectivity."""
import sys
from discovery.google_places_api import GooglePlacesAPI

def test_google_places():
    print("Testing Google Places API...")
    
    try:
        api = GooglePlacesAPI()
        print("✅ GooglePlacesAPI initialized")
        
        # Test with small search
        leads = api.fetch_leads("Digital Agencies", "Toronto, ON", max_results=3)
        
        if leads:
            print(f"\n✅ SUCCESS: Found {len(leads)} leads")
            for i, lead in enumerate(leads, 1):
                print(f"\n{i}. {lead['business_name']}")
                print(f"   Phone: {lead.get('phone', 'N/A')}")
                print(f"   City: {lead.get('city', 'N/A')}")
                print(f"   Rating: {lead.get('google_rating', 'N/A')}")
                print(f"   Reviews: {lead.get('google_review_count', 'N/A')}")
        else:
            print("\n⚠️ No leads returned (check API key or billing)")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_google_places()
