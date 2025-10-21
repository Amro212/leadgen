"""
Lead scoring engine.
Calculates quality scores and assigns tiers based on enrichment signals.
"""
from typing import Dict, Union
from models.lead import Lead
from config.weights import (
    TIER_A_THRESHOLD,
    TIER_B_THRESHOLD,
    WEIGHT_HAS_EMAIL,
    WEIGHT_HAS_PHONE,
    WEIGHT_HAS_CONTACT_FORM,
    WEIGHT_MULTIPLE_EMAILS,
    WEIGHT_HAS_WEBSITE,
    WEIGHT_USES_HTTPS,
    WEIGHT_HAS_MODERN_TECH,
    WEIGHT_NO_WEBSITE,
    WEIGHT_HAS_BOOKING,
    WEIGHT_HAS_EMERGENCY,
    WEIGHT_HAS_FINANCING,
)
from utils.logging_utils import get_logger

log = get_logger(__name__)


def score_lead(lead: Union[Lead, Dict]) -> Dict[str, Union[float, str]]:
    """
    Calculate quality score for a lead based on enrichment signals.
    
    Args:
        lead: Lead object or dictionary with lead data
    
    Returns:
        Dictionary with 'score' (float) and 'tier' (str)
    """
    # Handle both Lead objects and dictionaries
    if isinstance(lead, Lead):
        lead_data = lead.model_dump()
    else:
        lead_data = lead
    
    score = 0.0
    breakdown = []  # For debugging
    
    # ============================================
    # Contact Information (40 points max)
    # ============================================
    
    # Email address(es)
    emails = lead_data.get('emails', [])
    if emails and len(emails) > 0:
        score += WEIGHT_HAS_EMAIL
        breakdown.append(f"+{WEIGHT_HAS_EMAIL} (has email)")
        
        if len(emails) >= 2:
            score += WEIGHT_MULTIPLE_EMAILS
            breakdown.append(f"+{WEIGHT_MULTIPLE_EMAILS} (multiple emails)")
    
    # Phone number
    if lead_data.get('phone'):
        score += WEIGHT_HAS_PHONE
        breakdown.append(f"+{WEIGHT_HAS_PHONE} (has phone)")
    
    # Contact form
    if lead_data.get('has_contact_form'):
        score += WEIGHT_HAS_CONTACT_FORM
        breakdown.append(f"+{WEIGHT_HAS_CONTACT_FORM} (has contact form)")
    
    # ============================================
    # Digital Presence (30 points max)
    # ============================================
    
    # Website existence
    if lead_data.get('website'):
        score += WEIGHT_HAS_WEBSITE
        breakdown.append(f"+{WEIGHT_HAS_WEBSITE} (has website)")
        
        # HTTPS
        if lead_data.get('uses_https'):
            score += WEIGHT_USES_HTTPS
            breakdown.append(f"+{WEIGHT_USES_HTTPS} (uses HTTPS)")
        
        # Modern tech stack
        tech_stack = lead_data.get('tech_stack', [])
        if tech_stack and len(tech_stack) > 0:
            score += WEIGHT_HAS_MODERN_TECH
            breakdown.append(f"+{WEIGHT_HAS_MODERN_TECH} (modern tech: {', '.join(tech_stack)})")
    else:
        # Penalty for no website
        score += WEIGHT_NO_WEBSITE  # This is negative
        breakdown.append(f"{WEIGHT_NO_WEBSITE} (no website - penalty)")
    
    # ============================================
    # Business Features (30 points max)
    # ============================================
    
    # Online booking
    if lead_data.get('has_booking'):
        score += WEIGHT_HAS_BOOKING
        breakdown.append(f"+{WEIGHT_HAS_BOOKING} (has booking)")
    
    # Emergency/24-7 service
    if lead_data.get('has_emergency_service'):
        score += WEIGHT_HAS_EMERGENCY
        breakdown.append(f"+{WEIGHT_HAS_EMERGENCY} (emergency service)")
    
    # Financing
    if lead_data.get('has_financing'):
        score += WEIGHT_HAS_FINANCING
        breakdown.append(f"+{WEIGHT_HAS_FINANCING} (has financing)")
    
    # ============================================
    # Finalize Score and Tier
    # ============================================
    
    # Floor at 0, ceiling at 100
    score = max(0.0, min(100.0, score))
    
    # Assign tier
    if score >= TIER_A_THRESHOLD:
        tier = "A"
    elif score >= TIER_B_THRESHOLD:
        tier = "B"
    else:
        tier = "C"
    
    # Log breakdown for debugging (only at debug level)
    log.debug(f"Scored '{lead_data.get('business_name', 'Unknown')}': {score:.1f} ({tier})")
    log.debug(f"  Breakdown: {' | '.join(breakdown)}")
    
    return {
        "score": round(score, 1),
        "tier": tier
    }


def assign_tier(score: float) -> str:
    """
    Assign tier based on score.
    
    Args:
        score: Quality score (0-100)
    
    Returns:
        Tier string: "A", "B", or "C"
    """
    if score >= TIER_A_THRESHOLD:
        return "A"
    elif score >= TIER_B_THRESHOLD:
        return "B"
    else:
        return "C"
