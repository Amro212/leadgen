"""
Simple test script to see AI query generation output without running full pipeline.
Usage: python test_ai_query.py
"""

from outreach.query_generator import QueryGenerator
import json


def main():
    print("=" * 70)
    print("AI QUERY GENERATOR TEST")
    print("=" * 70)
    print()
    
    # Initialize the query generator
    query_gen = QueryGenerator()
    
    # Test with a sample company brief
    company_brief = input("Enter company brief (or press Enter for default): ").strip()
    
    if not company_brief:
        company_brief = "Toronto SaaS company selling project management tools to construction firms"
        print(f"Using default: {company_brief}")
    
    print()
    print("🤖 Generating PRECISION AI-powered search strategy...")
    print("-" * 70)
    
    # Generate the strategy
    strategy = query_gen.generate_search_strategy(company_brief)
    
    # Pretty print the results
    print()
    print("=" * 70)
    print("YELP SEARCH (Structured Parameters)")
    print("=" * 70)
    yelp = strategy['yelp_search']
    print(f"📍 Location: {yelp.get('location')}")
    print(f"🔍 Term: {yelp.get('term')}")
    print(f"🏷️  Categories: {yelp.get('categories')}")
    print(f"� Price: {yelp.get('price')}")
    print(f"✅ Attributes: {yelp.get('attributes')}")
    print(f"📊 Sort By: {yelp.get('sort_by')}")
    print()
    
    print("=" * 70)
    print("GOOGLE PLACES SEARCH (Detailed Query)")
    print("=" * 70)
    google = strategy['google_places_search']
    print(f"🌐 Query: {google.get('query')}")
    print()
    
    print("=" * 70)
    print("TAVILY RESEARCH")
    print("=" * 70)
    tavily = strategy['tavily_research']
    print(f"🔍 Query: {tavily.get('query')}")
    print(f"🌐 Domains: {', '.join(tavily.get('include_domains', []))}")
    print()
    
    print("=" * 70)
    print("LEAD CRITERIA")
    print("=" * 70)
    criteria = strategy['lead_criteria']
    print(f"✅ Must Have: {', '.join(criteria.get('must_have', []))}")
    print(f"⭐ Nice to Have: {', '.join(criteria.get('nice_to_have', []))}")
    print(f"❌ Deal Breakers: {', '.join(criteria.get('deal_breakers', []))}")
    print()
    
    print("-" * 70)
    print("📋 RAW JSON OUTPUT:")
    print(json.dumps(strategy, indent=2))
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
