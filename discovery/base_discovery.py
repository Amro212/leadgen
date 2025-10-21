"""
Base interface for discovery sources.
Defines the contract for all business discovery implementations.
"""
from abc import ABC, abstractmethod
from typing import List, Dict


class DiscoverySource(ABC):
    """
    Abstract base class for business discovery sources.
    
    All discovery implementations (Google, Yelp, Google Places, etc.)
    must inherit from this class and implement fetch_leads().
    """
    
    @abstractmethod
    def fetch_leads(
        self,
        query: str,
        location: str,
        max_results: int = 25
    ) -> List[Dict]:
        """
        Fetch business leads based on search criteria.
        
        Args:
            query: Business vertical or category (e.g., "HVAC", "Plumber")
            location: Geographic location (e.g., "Milton, Ontario")
            max_results: Maximum number of leads to return
        
        Returns:
            List of lead dictionaries with at minimum:
                - business_name: str
                - source: str (name of this discovery source)
            
            Optional fields:
                - city: str
                - region: str
                - website: str
                - phone: str
                - source_url: str (URL where lead was found)
        
        Example:
            [
                {
                    "business_name": "ABC Heating & Cooling",
                    "city": "Milton",
                    "website": "https://abchvac.com",
                    "phone": "+1-905-555-0123",
                    "source": "Google",
                    "source_url": "https://yelp.com/biz/abc-hvac"
                },
                ...
            ]
        """
        pass
