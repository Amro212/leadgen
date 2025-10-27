"""
API Usage Tracker - Monitor and manage API quota usage
Tracks daily and monthly limits with automatic resets.
"""
import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Optional
from utils.logging_utils import get_logger

log = get_logger(__name__)


class APIUsageTracker:
    """
    Tracks API usage with daily/monthly quotas and automatic resets.
    State persists to JSON file for cross-session tracking.
    """
    
    def __init__(self, state_file: Optional[str] = None):
        """
        Initialize tracker with state file path.
        
        Args:
            state_file: Path to JSON state file (default: output/api_usage.json)
        """
        if state_file is None:
            state_file = "output/api_usage.json"
        
        self.state_file = Path(state_file)
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load state from JSON file or initialize if not exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    log.debug(f"Loaded API usage state from {self.state_file}")
                    return state
            except Exception as e:
                log.error(f"Failed to load API state: {e}")
                return self._initialize_state()
        else:
            log.info(f"No existing API state found, initializing new tracker")
            return self._initialize_state()
    
    def _initialize_state(self) -> Dict:
        """Initialize empty state for all APIs."""
        today_str = date.today().isoformat()
        this_month = date.today().strftime("%Y-%m")
        
        return {
            'yelp': {
                'daily': 0,
                'last_reset': today_str,
                'limit': 500
            },
            'google_places': {
                'monthly': 0,
                'last_reset': this_month,
                'limit': 2000
            },
            'serpapi': {
                'monthly': 0,
                'last_reset': this_month,
                'limit': 100
            },
            'hunter': {
                'monthly': 0,
                'last_reset': this_month,
                'limit': 25
            },
            'tavily': {
                'monthly': 0,
                'last_reset': this_month,
                'limit': 4000
            },
            'gemini': {
                'daily': 0,
                'last_reset': today_str,
                'limit': 1500
            }
        }
    
    def _save_state(self):
        """Persist state to JSON file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            log.debug(f"Saved API usage state to {self.state_file}")
        except Exception as e:
            log.error(f"Failed to save API state: {e}")
    
    def _check_and_reset(self, api_name: str):
        """Check if reset is needed and perform auto-reset."""
        api = self.state[api_name]
        
        if 'daily' in api:
            # Daily reset
            today_str = date.today().isoformat()
            if api['last_reset'] != today_str:
                old_count = api['daily']
                api['daily'] = 0
                api['last_reset'] = today_str
                log.info(f"🔄 {api_name.upper()}: Daily quota reset (was {old_count}/{api['limit']})")
        
        if 'monthly' in api:
            # Monthly reset
            this_month = date.today().strftime("%Y-%m")
            if api['last_reset'] != this_month:
                old_count = api['monthly']
                api['monthly'] = 0
                api['last_reset'] = this_month
                log.info(f"🔄 {api_name.upper()}: Monthly quota reset (was {old_count}/{api['limit']})")
    
    def can_use(self, api_name: str, count: int = 1) -> bool:
        """
        Check if API has sufficient quota remaining.
        
        Args:
            api_name: API name (yelp, google_places, etc.)
            count: Number of calls to check for (default: 1)
        
        Returns:
            True if quota available, False otherwise
        """
        if api_name not in self.state:
            log.warning(f"Unknown API: {api_name}")
            return False
        
        self._check_and_reset(api_name)
        api = self.state[api_name]
        
        if 'daily' in api:
            remaining = api['limit'] - api['daily']
            return api['daily'] + count <= api['limit']
        else:
            remaining = api['limit'] - api['monthly']
            return api['monthly'] + count <= api['limit']
    
    def increment(self, api_name: str, count: int = 1):
        """
        Increment usage counter for an API.
        
        Args:
            api_name: API name (yelp, google_places, etc.)
            count: Number of calls to add (default: 1)
        """
        if api_name not in self.state:
            log.warning(f"Unknown API: {api_name}")
            return
        
        self._check_and_reset(api_name)
        api = self.state[api_name]
        
        if 'daily' in api:
            api['daily'] += count
            remaining = api['limit'] - api['daily']
            log.debug(f"{api_name.upper()}: {api['daily']}/{api['limit']} used today ({remaining} remaining)")
        else:
            api['monthly'] += count
            remaining = api['limit'] - api['monthly']
            log.debug(f"{api_name.upper()}: {api['monthly']}/{api['limit']} used this month ({remaining} remaining)")
        
        self._save_state()
    
    def get_remaining(self, api_name: str) -> int:
        """
        Get remaining quota for an API.
        
        Args:
            api_name: API name
        
        Returns:
            Number of calls remaining
        """
        if api_name not in self.state:
            return 0
        
        self._check_and_reset(api_name)
        api = self.state[api_name]
        
        if 'daily' in api:
            return api['limit'] - api['daily']
        else:
            return api['limit'] - api['monthly']
    
    def get_status(self) -> Dict[str, str]:
        """
        Get formatted status for all APIs.
        
        Returns:
            Dictionary mapping API names to status strings
        """
        status = {}
        
        for api_name in self.state.keys():
            self._check_and_reset(api_name)
            api = self.state[api_name]
            
            if 'daily' in api:
                status[api_name] = f"{api['daily']}/{api['limit']} today"
            else:
                status[api_name] = f"{api['monthly']}/{api['limit']} this month"
        
        return status
    
    def log_status(self):
        """Log current status for all APIs."""
        status = self.get_status()
        log.info("📊 API Usage Status:")
        for api_name, usage in status.items():
            log.info(f"   {api_name.upper()}: {usage}")


# Global singleton instance
_tracker: Optional[APIUsageTracker] = None


def get_tracker() -> APIUsageTracker:
    """Get or create the global API usage tracker."""
    global _tracker
    if _tracker is None:
        _tracker = APIUsageTracker()
    return _tracker
