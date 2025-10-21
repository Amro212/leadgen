"""
CSV export functionality for lead data.
Saves leads to CSV files with timestamps and professional formatting.
"""
from typing import List, Optional, Tuple
from datetime import datetime
import pandas as pd
from pathlib import Path
import re
from models.lead import Lead
from config.settings import SETTINGS
from utils.logging_utils import get_logger

log = get_logger(__name__)


def _normalize_phone(phone: Optional[str]) -> Tuple[str, bool, str]:
    """
    Normalize phone number to E.164 format.
    
    Returns:
        Tuple of (normalized_phone, is_valid, error_message)
    """
    if not phone:
        return ("", True, "")
    
    # Strip all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if we have enough digits (need at least 10 for North America)
    if len(digits) < 10:
        return (phone, False, f"Invalid phone: {phone} (only {len(digits)} digits)")
    
    # Format as E.164 for North America (+1-XXX-XXX-XXXX)
    if len(digits) == 10:
        # Add country code
        return (f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}", True, "")
    elif len(digits) == 11 and digits[0] == '1':
        # Has country code
        return (f"+1-{digits[1:4]}-{digits[4:7]}-{digits[7:]}", True, "")
    else:
        # Unknown format, keep as-is but mark invalid
        return (phone, False, f"Invalid phone format: {phone}")


def _generate_enrichment_summary(lead: Lead) -> str:
    """Generate a human-readable enrichment summary (ASCII-safe)."""
    parts = []
    
    # Contact Form
    if lead.has_contact_form is True:
        parts.append("CF=Yes")
    elif lead.has_contact_form is False:
        parts.append("CF=No")
    else:
        parts.append("CF=Unknown")
    
    # Booking
    if lead.has_booking is True:
        parts.append("BK=Yes")
    elif lead.has_booking is False:
        parts.append("BK=No")
    else:
        parts.append("BK=Unknown")
    
    # Emergency
    if lead.has_emergency_service is True:
        parts.append("Emergency=Yes")
    elif lead.has_emergency_service is False:
        parts.append("Emergency=No")
    
    # Financing
    if lead.has_financing is True:
        parts.append("Financing=Yes")
    
    # HTTPS
    if lead.uses_https is True:
        parts.append("HTTPS=Yes")
    elif lead.uses_https is False:
        parts.append("HTTPS=No")
    
    return " | ".join(parts) if parts else "No data"


def _generate_outreach_placeholders(lead: Lead) -> dict:
    """Generate placeholder outreach content based on missing features."""
    missing_features = []
    
    if not lead.has_booking:
        missing_features.append("online booking")
    if not lead.has_contact_form:
        missing_features.append("contact form")
    if not lead.has_financing:
        missing_features.append("financing options")
    
    if missing_features:
        features_str = " & ".join(missing_features)
        return {
            'outreach_snippet': f"Opportunity: add {features_str}.",
            'email_subject': "Quick idea to increase bookings.",
            'email_body': f"Hi - I noticed your site lacks {features_str}. Would you be interested in a simple solution?"
        }
    else:
        return {
            'outreach_snippet': "Well-optimized site - potential partnership opportunity.",
            'email_subject': "Partnership opportunity",
            'email_body': "Hi - Your business looks great. Interested in discussing growth opportunities?"
        }


def _format_lead_for_csv(lead: Lead) -> dict:
    """Format a lead for CSV export with clean, normalized data."""
    
    # Normalize phone number
    normalized_phone, phone_valid, phone_error = _normalize_phone(lead.phone)
    
    # Get primary email
    primary_email = lead.emails[0] if lead.emails else ""
    
    # Generate enrichment summary (ASCII-safe)
    enrichment_summary = _generate_enrichment_summary(lead)
    
    # Generate outreach placeholders
    outreach = _generate_outreach_placeholders(lead)
    
    # Compile internal notes
    notes_list = []
    if lead.notes:
        notes_list.extend(lead.notes)
    if not phone_valid and phone_error:
        notes_list.append(phone_error)
    
    internal_notes = "; ".join(notes_list) if notes_list else ""
    
    # Determine status
    status = lead.status
    if not phone_valid and lead.phone:
        status = "fail"
    
    # Format booleans as TRUE/FALSE strings
    def format_bool(value):
        if value is None:
            return ""
        return "TRUE" if value else "FALSE"
    
    # Ensure website has full scheme
    website = lead.website
    if website and not website.startswith(('http://', 'https://')):
        website = f"https://{website}"
    
    # Format timestamp (ISO8601 with Z suffix, rounded to seconds)
    try:
        dt = datetime.fromisoformat(lead.scrape_date.replace('Z', '+00:00'))
        scrape_date = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except:
        scrape_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return {
        # Meta fields
        'lead_id': lead.lead_id,
        'scrape_date': scrape_date,
        'status': status,
        'discovery_method': lead.discovery_method or lead.source or "Unknown",
        
        # Business info
        'business_name': lead.business_name,
        'website': website or "",
        'phone': f"'{normalized_phone}" if normalized_phone else "",  # Prefix with ' to force text in Excel
        'email': primary_email,
        'city': lead.city or "",
        
        # Website signals
        'has_contact_form': format_bool(lead.has_contact_form),
        'has_booking': format_bool(lead.has_booking),
        'has_emergency_service': format_bool(lead.has_emergency_service),
        'has_financing': format_bool(lead.has_financing),
        'uses_https': format_bool(lead.uses_https),
        
        # Scoring
        'score': int(lead.score),  # Convert to int for cleaner CSV
        'tier': lead.tier or "",
        
        # Metadata
        'source_url': lead.source_url or "",
        'enrichment_summary': enrichment_summary,
        'internal_notes': internal_notes,
        
        # Outreach placeholders
        'outreach_snippet': lead.outreach_snippet or outreach['outreach_snippet'],
        'email_subject': lead.email_subject or outreach['email_subject'],
        'email_body': lead.email_body or outreach['email_body'],
    }


def export_to_csv(leads: List[Lead], vertical: str, region: str) -> str:
    """
    Export leads to CSV file with professional formatting.
    
    Args:
        leads: List of Lead objects
        vertical: Business vertical (e.g., "HVAC")
        region: Geographic region (e.g., "Milton, Ontario")
    
    Returns:
        Path to the created CSV file
    """
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Clean vertical and region for filename
    vertical_clean = vertical.replace(" ", "_").replace(",", "")
    region_clean = region.replace(" ", "_").replace(",", "")
    
    # Create filename
    filename = f"{vertical_clean}_{region_clean}_{timestamp}.csv"
    filepath = Path(SETTINGS.OUTPUT_DIR) / filename
    
    # Ensure output directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Format leads for CSV
    formatted_leads = [_format_lead_for_csv(lead) for lead in leads]
    
    # Create DataFrame with specific column order (client-facing - no email_* columns yet)
    column_order = [
        'lead_id',
        'scrape_date',
        'business_name',
        'website',
        'phone',
        'email',
        'city',
        'has_contact_form',
        'has_booking',
        'has_emergency_service',
        'has_financing',
        'uses_https',
        'score',
        'tier',
        'status',
        'internal_notes',
        'discovery_method',
        'source_url',
        'enrichment_summary',
        'outreach_snippet',
        # Commented out until populated:
        # 'email_subject',
        # 'email_body',
    ]
    
    df = pd.DataFrame(formatted_leads)
    
    # Reorder columns (only include those that exist)
    existing_columns = [col for col in column_order if col in df.columns]
    df = df[existing_columns]
    
    # Save to CSV with UTF-8 encoding
    df.to_csv(filepath, index=False, encoding='utf-8')
    
    log.info(f"📄 Exported {len(leads)} leads to: {filepath}")
    
    return str(filepath)


def get_export_stats(leads: List[Lead]) -> dict:
    """
    Calculate export statistics.
    
    Args:
        leads: List of Lead objects
    
    Returns:
        Dictionary with statistics
    """
    tier_counts = {"A": 0, "B": 0, "C": 0}
    
    for lead in leads:
        if lead.tier:
            tier_counts[lead.tier] += 1
    
    # Calculate averages
    total_leads = len(leads)
    avg_score = sum(lead.score for lead in leads) / total_leads if total_leads > 0 else 0
    
    # Count enrichment signals
    with_email = sum(1 for lead in leads if lead.emails)
    with_phone = sum(1 for lead in leads if lead.phone)
    with_website = sum(1 for lead in leads if lead.website)
    with_form = sum(1 for lead in leads if lead.has_contact_form)
    
    return {
        'total_leads': total_leads,
        'tier_a': tier_counts['A'],
        'tier_b': tier_counts['B'],
        'tier_c': tier_counts['C'],
        'avg_score': round(avg_score, 1),
        'with_email': with_email,
        'with_phone': with_phone,
        'with_website': with_website,
        'with_form': with_form,
    }
