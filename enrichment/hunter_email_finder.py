"""
Hunter.io Email Finder - Email Verification for High-Value Leads
Uses Hunter.io Domain Search API to find and verify emails.
Only runs on Tier A leads (score >= 65) due to limited quota (25/month).
"""
import requests
from typing import List, Dict, Optional
from urllib.parse import urlparse
from config.settings import SETTINGS
from storage.api_usage import get_tracker
from utils.logging_utils import get_logger

log = get_logger(__name__)


class HunterEmailFinder:
    """
    Hunter.io email finder for verifying/discovering business emails.
    
    API Docs: https://hunter.io/api/v2/docs
    Pricing: Free tier = 25 searches/month
    """
    
    DOMAIN_SEARCH_URL = "https://api.hunter.io/v2/domain-search"
    EMAIL_VERIFIER_URL = "https://api.hunter.io/v2/email-verifier"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Hunter.io client.
        
        Args:
            api_key: Hunter.io API key (defaults to SETTINGS.HUNTER_API_KEY)
        """
        self.api_key = api_key or SETTINGS.HUNTER_API_KEY
        
        if not self.api_key:
            raise ValueError("HUNTER_API_KEY not found in environment variables")
        
        self.tracker = get_tracker()
        log.info("✅ Hunter.io Email Finder initialized")
    
    def find_emails(self, website: str, company_name: Optional[str] = None) -> Dict:
        """
        Find emails for a domain using Hunter.io Domain Search.
        
        Args:
            website: Business website URL
            company_name: Business name (optional, for logging)
        
        Returns:
            Dict with keys:
                - emails: List[str] - All discovered emails
                - primary_email: Optional[str] - Most likely primary email
                - email_confidence: int - Confidence score (0-100)
                - emails_verified: bool - Whether emails were verified
                - hunter_data: Dict - Raw API response (for debugging)
        """
        # Check quota before making API call
        if not self.tracker.can_use('hunter', count=1):
            remaining = self.tracker.get_remaining('hunter')
            log.warning(f"⚠️ Hunter.io quota exhausted ({remaining}/25 remaining this month)")
            log.warning("   Skipping email verification. Will reset next month.")
            return {
                'emails': [],
                'primary_email': None,
                'email_confidence': 0,
                'emails_verified': False,
                'hunter_data': None
            }
        
        # Extract domain from website URL
        try:
            if not website.startswith(('http://', 'https://')):
                website = f"https://{website}"
            domain = urlparse(website).netloc
            if not domain:
                log.warning(f"⚠️ Invalid website URL: {website}")
                return self._empty_result()
        except Exception as e:
            log.warning(f"⚠️ Failed to parse website URL {website}: {e}")
            return self._empty_result()
        
        # Log search
        display_name = company_name or domain
        log.info(f"🔍 Hunter.io: Searching emails for '{display_name}' ({domain})")
        
        try:
            # Make API call
            params = {
                'domain': domain,
                'api_key': self.api_key
            }
            
            response = requests.get(
                self.DOMAIN_SEARCH_URL,
                params=params,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if 'errors' in data:
                errors = data['errors']
                log.error(f"❌ Hunter.io API error: {errors}")
                return self._empty_result()
            
            # Extract emails from response
            result_data = data.get('data', {})
            emails_list = result_data.get('emails', [])
            
            if not emails_list:
                log.info(f"   ℹ️ Hunter.io: No emails found for {domain}")
                self.tracker.increment('hunter', count=1)
                remaining = self.tracker.get_remaining('hunter')
                log.info(f"   📊 Hunter.io quota: {remaining}/25 remaining this month")
                return self._empty_result()
            
            # Extract email data
            all_emails = []
            primary_email = None
            max_confidence = 0
            
            for email_obj in emails_list:
                email = email_obj.get('value')
                if not email:
                    continue
                
                all_emails.append(email)
                
                # Track highest confidence email as primary
                confidence = email_obj.get('confidence', 0)
                if confidence > max_confidence:
                    max_confidence = confidence
                    primary_email = email
            
            # If no confidence scores, use first email
            if not primary_email and all_emails:
                primary_email = all_emails[0]
                max_confidence = 50  # Default confidence
            
            log.info(f"   ✓ Hunter.io: Found {len(all_emails)} emails (confidence: {max_confidence}%)")
            if primary_email:
                log.info(f"   📧 Primary: {primary_email}")
            
            # Increment usage counter
            self.tracker.increment('hunter', count=1)
            remaining = self.tracker.get_remaining('hunter')
            log.info(f"   📊 Hunter.io quota: {remaining}/25 remaining this month")
            
            return {
                'emails': all_emails,
                'primary_email': primary_email,
                'email_confidence': max_confidence,
                'emails_verified': True,
                'hunter_data': result_data
            }
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                log.error("❌ Hunter.io: Rate limit exceeded (429)")
            elif e.response.status_code == 401:
                log.error("❌ Hunter.io: Invalid API key (401)")
            elif e.response.status_code == 402:
                log.error("❌ Hunter.io: Payment required - quota exceeded (402)")
            else:
                log.error(f"❌ Hunter.io: HTTP error {e.response.status_code}")
            return self._empty_result()
            
        except requests.exceptions.RequestException as e:
            log.error(f"❌ Hunter.io: Request failed: {e}")
            return self._empty_result()
            
        except Exception as e:
            log.error(f"❌ Hunter.io: Unexpected error: {e}")
            return self._empty_result()
    
    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            'emails': [],
            'primary_email': None,
            'email_confidence': 0,
            'emails_verified': False,
            'hunter_data': None
        }
    
    def verify_email(self, email: str) -> Dict:
        """
        Verify a single email address (costs 1 request).
        
        Args:
            email: Email address to verify
        
        Returns:
            Dict with verification results
        """
        # Check quota
        if not self.tracker.can_use('hunter', count=1):
            remaining = self.tracker.get_remaining('hunter')
            log.warning(f"⚠️ Hunter.io quota exhausted ({remaining}/25 remaining)")
            return {'valid': None, 'confidence': 0}
        
        log.info(f"🔍 Hunter.io: Verifying email {email}")
        
        try:
            params = {
                'email': email,
                'api_key': self.api_key
            }
            
            response = requests.get(
                self.EMAIL_VERIFIER_URL,
                params=params,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            result = data.get('data', {})
            status = result.get('status')  # 'valid', 'invalid', 'accept_all', 'unknown'
            score = result.get('score', 0)  # 0-100
            
            log.info(f"   ✓ Hunter.io: Email {email} - Status: {status}, Score: {score}")
            
            self.tracker.increment('hunter', count=1)
            remaining = self.tracker.get_remaining('hunter')
            log.info(f"   📊 Hunter.io quota: {remaining}/25 remaining this month")
            
            return {
                'valid': status == 'valid',
                'confidence': score,
                'status': status,
                'hunter_data': result
            }
            
        except Exception as e:
            log.error(f"❌ Hunter.io: Email verification failed: {e}")
            return {'valid': None, 'confidence': 0}
