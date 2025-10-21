"""
Website scraper for extracting business signals.
Fetches homepage and contact page to find emails, forms, keywords, and tech stack.
"""
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from utils.http_utils import get
from utils.logging_utils import get_logger

log = get_logger(__name__)


class WebsiteScraper:
    """
    Scrapes business websites to extract enrichment signals.
    """
    
    # Keywords to search for
    BOOKING_KEYWORDS = ['booking', 'appointment', 'schedule', 'book now', 'reserve']
    EMERGENCY_KEYWORDS = ['emergency', '24/7', '24 hour', 'urgent', 'same day']
    FINANCING_KEYWORDS = ['financing', 'payment plan', 'credit', 'installment']
    
    # Tech stack detection patterns
    TECH_PATTERNS = {
        'WordPress': ['wp-content', 'wp-includes', 'wordpress'],
        'Wix': ['wix.com', 'wixstatic'],
        'Squarespace': ['squarespace', 'sqsp'],
        'Shopify': ['shopify', 'cdn.shopify'],
        'Webflow': ['webflow'],
    }
    
    def scrape_website(self, url: str) -> Dict:
        """
        Scrape a business website for enrichment signals.
        
        Args:
            url: Website URL to scrape
        
        Returns:
            Dictionary with extracted signals
        """
        log.info(f"Scraping website: {url}")
        
        signals = {
            'emails': [],
            'has_contact_form': None,
            'has_booking': None,
            'has_emergency_service': None,
            'has_financing': None,
            'uses_https': url.startswith('https://'),
            'tech_stack': [],
            'notes': []
        }
        
        try:
            # Fetch homepage
            homepage_response = get(url)
            if not homepage_response:
                signals['notes'].append("Failed to fetch homepage")
                return signals
            
            homepage_html = homepage_response.text
            homepage_soup = BeautifulSoup(homepage_html, 'html.parser')
            
            # Extract emails from homepage
            emails = self._extract_emails(homepage_html)
            signals['emails'].extend(emails)
            
            # Check for contact form
            signals['has_contact_form'] = self._has_form(homepage_soup)
            
            # Check for keywords
            homepage_text = homepage_soup.get_text().lower()
            signals['has_booking'] = self._has_keywords(homepage_text, self.BOOKING_KEYWORDS)
            signals['has_emergency_service'] = self._has_keywords(homepage_text, self.EMERGENCY_KEYWORDS)
            signals['has_financing'] = self._has_keywords(homepage_text, self.FINANCING_KEYWORDS)
            
            # Detect tech stack
            signals['tech_stack'] = self._detect_tech_stack(homepage_html)
            
            # Try to fetch contact page for more emails
            contact_url = self._find_contact_page(homepage_soup, url)
            if contact_url:
                contact_emails = self._scrape_contact_page(contact_url)
                signals['emails'].extend(contact_emails)
            
            # Dedupe emails
            signals['emails'] = list(set(signals['emails']))
            
            log.info(f"✓ Scraped {url}: {len(signals['emails'])} emails, "
                    f"{'form' if signals['has_contact_form'] else 'no form'}, "
                    f"{len(signals['tech_stack'])} tech detected")
            
        except Exception as e:
            log.error(f"Error scraping {url}: {e}")
            signals['notes'].append(f"Scraping error: {str(e)}")
        
        return signals
    
    def _extract_emails(self, html: str) -> List[str]:
        """Extract email addresses from HTML."""
        # Regex pattern for emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, html)
        
        # Filter out common false positives
        filtered = [
            email for email in emails
            if not any(skip in email.lower() for skip in ['example.com', 'test.com', 'domain.com'])
        ]
        
        return list(set(filtered))
    
    def _has_form(self, soup: BeautifulSoup) -> bool:
        """Check if page has a contact form."""
        forms = soup.find_all('form')
        
        # Look for forms with email or message fields
        for form in forms:
            inputs = form.find_all(['input', 'textarea'])
            for inp in inputs:
                inp_type = inp.get('type', '').lower()
                inp_name = inp.get('name', '').lower()
                inp_id = inp.get('id', '').lower()
                
                # Check for email/message/contact fields
                if any(keyword in f"{inp_type} {inp_name} {inp_id}" 
                       for keyword in ['email', 'message', 'contact', 'inquiry']):
                    return True
        
        return False
    
    def _has_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords."""
        return any(keyword in text for keyword in keywords)
    
    def _detect_tech_stack(self, html: str) -> List[str]:
        """Detect technology stack from HTML."""
        detected = []
        html_lower = html.lower()
        
        for tech, patterns in self.TECH_PATTERNS.items():
            if any(pattern in html_lower for pattern in patterns):
                detected.append(tech)
        
        return detected
    
    def _find_contact_page(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Find link to contact page."""
        contact_keywords = ['contact', 'contact-us', 'get-in-touch', 'reach-us']
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '').lower()
            text = link.get_text().lower()
            
            # Check if link points to contact page
            if any(keyword in f"{href} {text}" for keyword in contact_keywords):
                # Convert to absolute URL
                contact_url = urljoin(base_url, link['href'])
                # Make sure it's the same domain
                if self._same_domain(base_url, contact_url):
                    return contact_url
        
        return None
    
    def _scrape_contact_page(self, url: str) -> List[str]:
        """Scrape contact page for additional emails."""
        try:
            response = get(url)
            if response:
                return self._extract_emails(response.text)
        except Exception as e:
            log.debug(f"Could not scrape contact page {url}: {e}")
        
        return []
    
    def _same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain."""
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except Exception:
            return False
