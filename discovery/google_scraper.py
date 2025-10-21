"""
Business discovery - Sample data generator for MVP testing.

REALITY CHECK:
All major search engines (Google, Bing, DuckDuckGo) and business directories
(Yelp, Yellow Pages) have sophisticated anti-bot measures that block scrapers.
Options:
1. Use APIs (Yelp Fusion API is FREE - 500 calls/day) → T25
2. Use proxies/CAPTCHA solvers ($$$)
3. Use sample data for MVP testing (this approach)

This implementation generates realistic sample data to test the full pipeline.
Once the pipeline works end-to-end, upgrade to real APIs in Phase 9.
"""
import time
import random
from typing import List, Dict
from utils.logging_utils import get_logger
from discovery.base_discovery import DiscoverySource

log = get_logger(__name__)


# Realistic business name templates
BUSINESS_TEMPLATES = [
    "{city} {vertical}",
    "{vertical} Express",
    "24/7 {vertical} Services",
    "Elite {vertical}",
    "Superior {vertical}",
    "Pro {vertical} Solutions",
    "{vertical} Masters",
    "ABC {vertical}",
    "Premier {vertical}",
    "Quality {vertical}",
    "Reliable {vertical}",
    "Expert {vertical} Pros",
    "{vertical} Specialists",
    "All-Star {vertical}",
    "Best {vertical} Co.",
]

# Realistic phone number generator
def generate_phone():
    area = random.choice(['905', '416', '647', '289'])
    exchange = random.randint(200, 999)
    number = random.randint(1000, 9999)
    return f"+1-{area}-{exchange}-{number}"


class GoogleScraper(DiscoverySource):
    """
    Sample data generator for MVP testing.
    
    Generates realistic business leads to test the full pipeline.
    Replace with Yelp Fusion API (T25) for production.
    """
    
    def __init__(self):
        self.delay = 0.3  # Minimal delay for local generation
    
    def fetch_leads(
        self,
        query: str,
        location: str,
        max_results: int = 25
    ) -> List[Dict]:
        """
        Generate sample business leads for testing.
        
        Args:
            query: Business vertical (e.g., "HVAC")
            location: Geographic location (e.g., "Milton, Ontario")
            max_results: Maximum results to return
        
        Returns:
            List of lead dictionaries with business_name and source_url
        """
        log.info(f"🔍 Generating sample leads for '{query}' in '{location}'")
        log.warning("⚠️  Using sample data - web scraping blocked by anti-bot")
        log.info("💡 To get real data: Use Yelp Fusion API (Task T25, FREE 500 calls/day)")
        
        # Extract city from location
        city = location.split(',')[0].strip() if ',' in location else location
        
        # Generate varied business names
        leads = []
        templates = random.sample(BUSINESS_TEMPLATES, min(max_results, len(BUSINESS_TEMPLATES)))
        
        for i, template in enumerate(templates[:max_results]):
            business_name = template.format(city=city, vertical=query)
            
            # Vary the data to simulate real-world scenarios
            has_website = random.random() > 0.2  # 80% have websites
            has_phone = random.random() > 0.1    # 90% have phones
            
            lead = {
                "business_name": business_name,
                "city": city,
                "website": f"https://{business_name.lower().replace(' ', '')}.com" if has_website else None,
                "phone": generate_phone() if has_phone else None,
                "source": "Sample Data",
                "source_url": f"https://yelp.com/biz/{business_name.lower().replace(' ', '-')}-{city.lower()}",
                "notes": []
            }
            
            leads.append(lead)
        
        log.info(f"✓ Generated {len(leads)} sample leads")
        log.info(f"   {sum(1 for l in leads if l['website'])} with websites")
        log.info(f"   {sum(1 for l in leads if l['phone'])} with phone numbers")
        
        time.sleep(self.delay)
        return leads
