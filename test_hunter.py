"""Quick test script for Hunter.io email finder."""
from enrichment.hunter_email_finder import HunterEmailFinder

def test_hunter():
    print("Testing Hunter.io Email Finder...")
    
    try:
        hunter = HunterEmailFinder()
        print("✅ Hunter.io initialized")
        
        # Test with a known domain
        test_website = "stripe.com"
        print(f"\nSearching for emails on {test_website}...")
        
        result = hunter.find_emails(test_website, "Stripe")
        
        print(f"\n✅ Results:")
        print(f"   Emails found: {len(result['emails'])}")
        print(f"   Primary: {result['primary_email']}")
        print(f"   Confidence: {result['email_confidence']}%")
        print(f"   Verified: {result['emails_verified']}")
        
        if result['emails']:
            print(f"\n   All emails:")
            for email in result['emails'][:5]:  # Show first 5
                print(f"      - {email}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hunter()
