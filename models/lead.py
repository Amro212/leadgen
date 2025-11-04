"""
Lead data model.
Defines the core data structure for a business lead.
"""
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class Lead(BaseModel):
    """
    Represents a business lead with discovery, enrichment, and scoring data.
    """
    
    # Meta fields
    lead_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique lead identifier")
    scrape_date: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="UTC timestamp of scrape")
    discovery_method: Optional[str] = Field(None, description="Source method (e.g., Yelp API, Google Places, Scraper)")
    status: str = Field("success", description="Processing status: success/fail")
    
    # Core business information
    business_name: str = Field(..., description="Name of the business")
    city: Optional[str] = Field(None, description="City location")
    region: Optional[str] = Field(None, description="Region/state/province")
    website: Optional[str] = Field(None, description="Business website URL")
    phone: Optional[str] = Field(None, description="Business phone number")
    
    # Email findings (flattened from list to single primary email)
    email: Optional[str] = Field(None, description="Primary contact email")
    emails: List[str] = Field(default_factory=list, description="All found email addresses")
    
    # Email verification (from Hunter.io)
    emails_verified: bool = Field(False, description="Whether emails were verified via Hunter.io")
    email_confidence: int = Field(0, ge=0, le=100, description="Email confidence score (0-100)")
    hunter_verified: bool = Field(False, description="Hunter.io enrichment was run")
    
    # Feature flags (from enrichment)
    has_contact_form: Optional[bool] = Field(None, description="Website has contact form")
    has_booking: Optional[bool] = Field(None, description="Supports online booking/appointments")
    has_emergency_service: Optional[bool] = Field(None, description="Offers emergency/24-7 service")
    has_financing: Optional[bool] = Field(None, description="Offers financing options")
    uses_https: Optional[bool] = Field(None, description="Website uses HTTPS")
    
    # Yelp metrics (from discovery)
    yelp_rating: Optional[float] = Field(None, ge=0, le=5, description="Yelp rating (0-5 stars, 0 = no rating)")
    yelp_review_count: Optional[int] = Field(None, ge=0, description="Number of Yelp reviews")
    yelp_price_level: Optional[str] = Field(None, description="Price level ($, $$, $$$, $$$$)")
    yelp_categories: List[str] = Field(default_factory=list, description="Yelp business categories")
    
    # Google Places metrics (from discovery)
    google_rating: Optional[float] = Field(None, ge=0, le=5, description="Google rating (0-5 stars)")
    google_review_count: Optional[int] = Field(None, ge=0, description="Number of Google reviews")
    google_price_level: Optional[int] = Field(None, ge=0, le=4, description="Google price level (0-4, 0=Free, 4=Very Expensive)")
    google_place_id: Optional[str] = Field(None, description="Google Place ID for future API calls")
    
    # Tavily research (from deep research - Tier A only)
    tavily_verified: bool = Field(False, description="Tavily deep research was run")
    tavily_website_found: Optional[str] = Field(None, description="Actual business website found by Tavily")
    tavily_recent_activity: bool = Field(False, description="Business has recent mentions (last 6 months)")
    tavily_reputation_score: int = Field(0, ge=0, le=100, description="Reputation score based on mentions (0-100)")
    tavily_sources_found: int = Field(0, ge=0, description="Number of independent sources found")
    tavily_review_sites: List[str] = Field(default_factory=list, description="Review platforms found (Google Maps, BBB, etc.)")
    tavily_negative_flags: List[str] = Field(default_factory=list, description="Warning signs found during research")
    
    # Technology signals (commented out until populated - will be in internal_notes for now)
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
    
    # Enrichment summary
    enrichment_summary: Optional[str] = Field(None, description="Summary of key features detected")
    
    # Internal tracking
    internal_notes: Optional[str] = Field(None, description="Debug and processing notes")
    notes: List[str] = Field(default_factory=list, description="Processing notes and errors (internal)")
    
    # Enrichment signals (internal - not in CSV)
    signals: Dict[str, Any] = Field(
        default_factory=dict,
        description="Enrichment signals (internal tracking)"
    )
    
    # Future outreach placeholders (optional)
    outreach_snippet: Optional[str] = Field(None, description="Suggested outreach snippet")
    email_subject: Optional[str] = Field(None, description="Suggested email subject line")
    email_body: Optional[str] = Field(None, description="Suggested email body template")
    
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
