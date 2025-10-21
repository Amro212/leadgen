"""
Lead data model.
Defines the core data structure for a business lead.
"""
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, HttpUrl


class Lead(BaseModel):
    """
    Represents a business lead with discovery, enrichment, and scoring data.
    """
    
    # Core business information
    business_name: str = Field(..., description="Name of the business")
    city: Optional[str] = Field(None, description="City location")
    region: Optional[str] = Field(None, description="Region/state/province")
    website: Optional[str] = Field(None, description="Business website URL")
    phone: Optional[str] = Field(None, description="Business phone number")
    
    # Enrichment signals
    signals: Dict[str, Any] = Field(
        default_factory=dict,
        description="Enrichment signals (emails, forms, keywords, tech stack)"
    )
    
    # Email findings
    emails: List[str] = Field(default_factory=list, description="Found email addresses")
    
    # Feature flags (from enrichment)
    has_contact_form: Optional[bool] = Field(None, description="Website has contact form")
    has_booking: Optional[bool] = Field(None, description="Supports online booking/appointments")
    has_emergency_service: Optional[bool] = Field(None, description="Offers emergency/24-7 service")
    has_financing: Optional[bool] = Field(None, description="Offers financing options")
    uses_https: Optional[bool] = Field(None, description="Website uses HTTPS")
    
    # Technology signals
    tech_stack: List[str] = Field(
        default_factory=list,
        description="Detected technologies (WordPress, Wix, etc.)"
    )
    
    # Scoring
    score: float = Field(0.0, ge=0, le=100, description="Lead quality score (0-100)")
    tier: Optional[str] = Field(None, description="Lead tier (A/B/C)")
    
    # Metadata
    source: Optional[str] = Field(None, description="Discovery source (Google, Yelp, etc.)")
    source_url: Optional[str] = Field(None, description="URL where lead was discovered")
    notes: List[str] = Field(default_factory=list, description="Processing notes and errors")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "business_name": "ABC Heating & Cooling",
                "city": "Milton",
                "region": "Ontario",
                "website": "https://abchvac.com",
                "phone": "+1-905-555-0123",
                "emails": ["info@abchvac.com"],
                "has_contact_form": True,
                "has_booking": True,
                "has_emergency_service": True,
                "has_financing": False,
                "uses_https": True,
                "tech_stack": ["WordPress"],
                "score": 78.5,
                "tier": "A",
                "source": "Google",
                "source_url": "https://yelp.com/biz/abc-hvac",
                "notes": []
            }
        }
    
    def add_note(self, note: str) -> None:
        """Add a processing note."""
        self.notes.append(note)
    
    def add_signal(self, key: str, value: Any) -> None:
        """Add an enrichment signal."""
        self.signals[key] = value
