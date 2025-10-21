"""
Base interface for enrichment sources.
Defines the contract for all lead enrichment implementations.
"""
from abc import ABC, abstractmethod
from typing import List, Dict
from models.lead import Lead


class EnrichmentSource(ABC):
    """
    Abstract base class for lead enrichment sources.
    
    All enrichment implementations (website scraper, Hunter.io, Clearbit, etc.)
    must inherit from this class and implement enrich().
    """
    
    @abstractmethod
    def enrich(self, leads: List[Dict]) -> List[Dict]:
        """
        Enrich leads with additional data.
        
        Args:
            leads: List of lead dictionaries from discovery
        
        Returns:
            List of enriched lead dictionaries with additional fields:
                - emails: List[str] (found email addresses)
                - has_contact_form: bool
                - has_booking: bool
                - has_emergency_service: bool
                - has_financing: bool
                - uses_https: bool
                - tech_stack: List[str] (detected technologies)
                - signals: Dict (any additional enrichment data)
                - notes: List[str] (processing notes/errors)
        
        Note:
            - Should preserve all original fields from input leads
            - Should handle errors gracefully and add to 'notes' field
            - May return leads with None values if enrichment fails
        
        Example:
            Input:
                [{"business_name": "ABC HVAC", "website": "https://abchvac.com"}]
            
            Output:
                [{
                    "business_name": "ABC HVAC",
                    "website": "https://abchvac.com",
                    "emails": ["info@abchvac.com"],
                    "has_contact_form": True,
                    "has_booking": True,
                    "uses_https": True,
                    "tech_stack": ["WordPress"],
                    "notes": []
                }]
        """
        pass
