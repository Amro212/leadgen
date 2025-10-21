"""
Scoring weights for lead quality calculation.

The scoring system evaluates leads based on:
1. Contactability (can we reach them?)
2. Digital presence (do they have a modern online presence?)
3. Business signals (do they show signs of being a good prospect?)

Total possible score: 100 points
"""

# Tier thresholds
TIER_A_THRESHOLD = 65  # High-quality leads
TIER_B_THRESHOLD = 45  # Medium-quality leads
# Below 45 = Tier C (low-quality)

# Contact Information Weights (40 points total)
# Having multiple contact methods is valuable
WEIGHT_HAS_EMAIL = 15           # Found at least one email
WEIGHT_HAS_PHONE = 10           # Has phone number
WEIGHT_HAS_CONTACT_FORM = 10    # Has contact form on website
WEIGHT_MULTIPLE_EMAILS = 5      # Has 2+ email addresses

# Digital Presence Weights (30 points total)
# Modern, professional online presence indicates a good business
WEIGHT_HAS_WEBSITE = 10         # Has a website
WEIGHT_USES_HTTPS = 5           # Website uses HTTPS (security/professionalism)
WEIGHT_HAS_MODERN_TECH = 10     # Uses modern platform (WordPress, Wix, Squarespace, etc.)
WEIGHT_NO_WEBSITE = -15         # PENALTY: No website at all

# Business Feature Weights (30 points total)
# These indicate business sophistication and openness to new tools
WEIGHT_HAS_BOOKING = 12         # Online booking/appointment system
WEIGHT_HAS_EMERGENCY = 8        # Emergency/24-7 service (higher revenue, urgency)
WEIGHT_HAS_FINANCING = 10       # Offers financing (complex sales, good prospect)

# Scoring guidelines:
# - Start at 0 and add points for each signal
# - Penalties can result in negative scores (floor at 0)
# - Maximum theoretical score: 100
# - Typical high-quality lead: 65-85
# - Typical medium-quality lead: 45-64
# - Typical low-quality lead: 0-44
