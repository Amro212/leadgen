"""Quick test script for Tavily researcher."""
from enrichment.tavily_researcher import TavilyResearcher

def test_tavily():
    print("Testing Tavily Deep Research...")
    
    try:
        tavily = TavilyResearcher()
        print("✅ Tavily initialized")
        
        # Test with a known business
        print("\nSearching for 'Shopify' in 'Ottawa, ON'...")
        result = tavily.research_business(
            business_name="Shopify",
            city="Ottawa, ON",
            website=None  # Let Tavily find it
        )
        
        print(f"\n✅ Results:")
        print(f"   Verified: {result['tavily_verified']}")
        print(f"   Website found: {result['verified_website']}")
        print(f"   Recent activity: {result['recent_activity']}")
        print(f"   Reputation score: {result['reputation_score']}/100")
        print(f"   Sources found: {result['sources_found']}")
        print(f"   Review sites: {result['review_sites']}")
        if result['negative_flags']:
            print(f"   ⚠️ Negative flags: {len(result['negative_flags'])}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tavily()
