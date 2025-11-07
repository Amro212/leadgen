"""
Summary report generation for lead exports.
Creates text-based summary reports alongside CSV exports.
"""
from typing import List
from datetime import datetime
from pathlib import Path
from models.lead import Lead
from utils.logging_utils import get_logger

log = get_logger(__name__)


def generate_summary_report(leads: List[Lead], vertical: str, region: str, csv_filepath: str) -> str:
    """
    Generate a summary report for exported leads.
    
    Args:
        leads: List of Lead objects
        vertical: Business vertical
        region: Geographic region
        csv_filepath: Path to the CSV or XLSX file (used for naming)
    
    Returns:
        Path to the created report file
    """
    # Create report filename (replace extension with _summary.txt)
    from pathlib import Path
    base_path = Path(csv_filepath).with_suffix('')
    report_filepath = f"{base_path}_summary.txt"
    
    # Calculate statistics
    total = len(leads)
    tier_counts = {"A": 0, "B": 0, "C": 0}
    
    for lead in leads:
        if lead.tier:
            tier_counts[lead.tier] += 1
    
    avg_score = sum(lead.score for lead in leads) / total if total > 0 else 0
    
    # Get top leads by tier
    a_tier_leads = sorted([l for l in leads if l.tier == "A"], key=lambda x: x.score, reverse=True)[:5]
    b_tier_leads = sorted([l for l in leads if l.tier == "B"], key=lambda x: x.score, reverse=True)[:5]
    
    # Count enrichment signals
    with_email = sum(1 for lead in leads if lead.emails)
    with_phone = sum(1 for lead in leads if lead.phone)
    with_website = sum(1 for lead in leads if lead.website)
    with_form = sum(1 for lead in leads if lead.has_contact_form)
    with_booking = sum(1 for lead in leads if lead.has_booking)
    with_emergency = sum(1 for lead in leads if lead.has_emergency_service)
    with_financing = sum(1 for lead in leads if lead.has_financing)
    
    # Build report content
    report_lines = [
        "=" * 80,
        "LEAD GENERATION SUMMARY REPORT",
        "=" * 80,
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Vertical: {vertical}",
        f"Region: {region}",
        f"CSV Export: {Path(csv_filepath).name}",
        "",
        "=" * 80,
        "OVERVIEW",
        "=" * 80,
        "",
        f"Total Leads: {total}",
        f"Average Score: {avg_score:.1f}",
        "",
        "Tier Distribution:",
        f"  🏆 Tier A (≥65): {tier_counts['A']:3d} ({tier_counts['A']/total*100:.1f}%)" if total > 0 else "  🏆 Tier A (≥65):   0 (0.0%)",
        f"  📊 Tier B (≥45): {tier_counts['B']:3d} ({tier_counts['B']/total*100:.1f}%)" if total > 0 else "  📊 Tier B (≥45):   0 (0.0%)",
        f"  📉 Tier C (<45): {tier_counts['C']:3d} ({tier_counts['C']/total*100:.1f}%)" if total > 0 else "  📉 Tier C (<45):   0 (0.0%)",
        "",
        "=" * 80,
        "ENRICHMENT COVERAGE",
        "=" * 80,
        "",
        f"Leads with Email:     {with_email:3d} ({with_email/total*100:.1f}%)" if total > 0 else "Leads with Email:       0 (0.0%)",
        f"Leads with Phone:     {with_phone:3d} ({with_phone/total*100:.1f}%)" if total > 0 else "Leads with Phone:       0 (0.0%)",
        f"Leads with Website:   {with_website:3d} ({with_website/total*100:.1f}%)" if total > 0 else "Leads with Website:     0 (0.0%)",
        f"Leads with Form:      {with_form:3d} ({with_form/total*100:.1f}%)" if total > 0 else "Leads with Form:        0 (0.0%)",
        f"Leads with Booking:   {with_booking:3d} ({with_booking/total*100:.1f}%)" if total > 0 else "Leads with Booking:     0 (0.0%)",
        f"Leads with Emergency: {with_emergency:3d} ({with_emergency/total*100:.1f}%)" if total > 0 else "Leads with Emergency:   0 (0.0%)",
        f"Leads with Financing: {with_financing:3d} ({with_financing/total*100:.1f}%)" if total > 0 else "Leads with Financing:   0 (0.0%)",
        "",
    ]
    
    # Add top A-tier leads
    if a_tier_leads:
        report_lines.extend([
            "=" * 80,
            f"TOP {len(a_tier_leads)} A-TIER LEADS",
            "=" * 80,
            "",
        ])
        
        for i, lead in enumerate(a_tier_leads, 1):
            report_lines.extend([
                f"{i}. {lead.business_name}",
                f"   Score: {lead.score:.1f} | Tier: {lead.tier}",
                f"   Phone: {lead.phone or 'N/A'}",
                f"   Website: {lead.website or 'N/A'}",
                f"   Emails: {', '.join(lead.emails) if lead.emails else 'None'}",
                f"   Signals: Form={lead.has_contact_form}, Booking={lead.has_booking}, Emergency={lead.has_emergency_service}",
                "",
            ])
    else:
        report_lines.extend([
            "=" * 80,
            "TOP A-TIER LEADS",
            "=" * 80,
            "",
            "No A-tier leads found.",
            "",
        ])
    
    # Add top B-tier leads if no A-tier
    if not a_tier_leads and b_tier_leads:
        report_lines.extend([
            "=" * 80,
            f"TOP {len(b_tier_leads)} B-TIER LEADS",
            "=" * 80,
            "",
        ])
        
        for i, lead in enumerate(b_tier_leads, 1):
            report_lines.extend([
                f"{i}. {lead.business_name}",
                f"   Score: {lead.score:.1f} | Tier: {lead.tier}",
                f"   Phone: {lead.phone or 'N/A'}",
                f"   Website: {lead.website or 'N/A'}",
                f"   Emails: {', '.join(lead.emails) if lead.emails else 'None'}",
                "",
            ])
    
    # Add footer
    report_lines.extend([
        "=" * 80,
        "END OF REPORT",
        "=" * 80,
    ])
    
    # Write report to file
    with open(report_filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    log.info(f"📊 Generated summary report: {report_filepath}")
    
    return report_filepath
