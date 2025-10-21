"""
HTTP utilities with retry logic, rate limiting, and user agent rotation.
Provides reliable HTTP requests for web scraping.
"""
import time
import random
import requests
from typing import Optional, Dict
from urllib.parse import urlparse
from utils.logging_utils import get_logger

log = get_logger(__name__)


# User agent rotation pool
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


class HTTPClient:
    """
    HTTP client with retry logic and rate limiting.
    """
    
    def __init__(
        self,
        timeout: int = 8,
        max_retries: int = 3,
        delay_between_requests: float = 1.5
    ):
        """
        Initialize HTTP client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            delay_between_requests: Minimum delay between requests (seconds)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay = delay_between_requests
        self.last_request_time: Dict[str, float] = {}  # Domain -> timestamp
        self.session = requests.Session()
    
    def get(
        self,
        url: str,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Optional[requests.Response]:
        """
        Fetch URL with retry logic and rate limiting.
        
        Args:
            url: URL to fetch
            headers: Optional custom headers
            timeout: Optional timeout override (uses default if None)
            **kwargs: Additional arguments for requests.get
        
        Returns:
            Response object or None if all retries failed
        """
        # Extract domain for rate limiting
        domain = self._extract_domain(url)
        
        # Rate limiting: ensure minimum delay per domain
        self._apply_rate_limit(domain)
        
        # Prepare headers with random user agent
        request_headers = self._prepare_headers(headers)
        
        # Use provided timeout or default
        request_timeout = timeout if timeout is not None else self.timeout
        
        # Retry loop
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                log.debug(f"Fetching {url} (attempt {attempt}/{self.max_retries})")
                
                response = self.session.get(
                    url,
                    headers=request_headers,
                    timeout=request_timeout,
                    **kwargs
                )
                
                # Check if successful
                response.raise_for_status()
                
                log.debug(f"✓ {url} → {response.status_code}")
                
                # Update last request time
                self.last_request_time[domain] = time.time()
                
                return response
                
            except requests.exceptions.Timeout as e:
                last_error = f"Timeout: {e}"
                log.warning(f"Timeout on {url} (attempt {attempt})")
                
            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP {e.response.status_code}: {e}"
                
                # Don't retry on 404 or 403
                if e.response.status_code in [403, 404, 410]:
                    log.warning(f"Non-retryable error {e.response.status_code} for {url}")
                    return None
                
                log.warning(f"HTTP error on {url}: {e.response.status_code} (attempt {attempt})")
                
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {e}"
                log.warning(f"Connection error on {url} (attempt {attempt})")
                
            except requests.exceptions.RequestException as e:
                last_error = f"Request error: {e}"
                log.warning(f"Request failed for {url}: {e}")
            
            # Exponential backoff before retry
            if attempt < self.max_retries:
                backoff = 2 ** attempt  # 2, 4, 8 seconds
                log.debug(f"Waiting {backoff}s before retry...")
                time.sleep(backoff)
        
        # All retries failed
        log.error(f"Failed to fetch {url} after {self.max_retries} attempts: {last_error}")
        return None
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for rate limiting."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return "unknown"
    
    def _apply_rate_limit(self, domain: str) -> None:
        """Ensure minimum delay between requests to same domain."""
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.delay:
                sleep_time = self.delay - elapsed
                log.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
                time.sleep(sleep_time)
    
    def _prepare_headers(self, custom_headers: Optional[Dict] = None) -> Dict:
        """Prepare request headers with random user agent."""
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Merge custom headers
        if custom_headers:
            headers.update(custom_headers)
        
        return headers


# Global client instance
_http_client = HTTPClient()


def get(url: str, **kwargs) -> Optional[requests.Response]:
    """
    Convenience function for HTTP GET with retry and rate limiting.
    
    Args:
        url: URL to fetch
        **kwargs: Additional arguments
    
    Returns:
        Response object or None if failed
    """
    return _http_client.get(url, **kwargs)
