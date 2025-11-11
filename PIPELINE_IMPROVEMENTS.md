# Lead Generation Pipeline Improvements

## Problem Analysis

### Issues Identified:
1. **All leads were Tier C** (score 0-25) - no Tier A/B leads
2. **Yelp API returning Yelp URLs** instead of actual business websites
3. **Google Places not fetching websites** - needs Details API call
4. **No website discovery stage** - trying to scrape Yelp URLs
5. **Tavily/Hunter only running on Tier A** - but we need them BEFORE scoring to boost scores
6. **SerpAPI not being used** - available but not integrated

### Root Cause:
- Leads were scored BEFORE finding actual websites
- Without websites, leads couldn't get enrichment signals (emails, contact forms, tech stack)
- Low scores meant Tavily/Hunter never ran
- Vicious cycle: No websites → Low scores → No enrichment → No websites

## Solution Implemented

### New Pipeline Flow:
```
1. Discovery (Yelp + Google Places)
   ↓
2. Website Discovery (NEW!) ← Find actual websites
   ↓
3. Enrichment (Website scraping)
   ↓
4. Scoring (Based on enrichment data)
   ↓
5. Hunter.io (Tier A only)
   ↓
6. Tavily Deep Research (Tier A only)
   ↓
7. Export
```

### Key Changes:

#### 1. Website Discovery Stage (NEW)
- **File**: `enrichment/website_discovery.py`
- **Purpose**: Find actual business websites using multiple APIs
- **Strategy**:
  1. Google Places Details API (if place_id available) - fastest, most accurate
  2. SerpAPI web search (if available) - finds websites via Google search
  3. Tavily research (fallback) - deep search for business websites

#### 2. Fixed Yelp API Mapping
- **File**: `discovery/yelp_fusion_api.py`
- **Change**: Set `website: None` instead of Yelp URL
- **Reason**: Yelp search endpoint doesn't provide actual business websites
- **Result**: Yelp URL stored in `source_url`, website discovered later

#### 3. Updated Enrichment Pipeline
- **File**: `enrichment/enrichment_pipeline.py`
- **Change**: Skip scraping if website is a Yelp URL
- **Reason**: Yelp URLs don't contain business website content

#### 4. Reordered Pipeline Stages
- **File**: `main.py`
- **Change**: Website discovery happens BEFORE enrichment
- **Result**: Leads have actual websites before scoring, enabling better enrichment

## Expected Improvements

### Before:
- ❌ All leads Tier C (0-25 points)
- ❌ No websites found (Yelp URLs only)
- ❌ No emails discovered
- ❌ No contact forms detected
- ❌ Tavily/Hunter never ran

### After:
- ✅ Leads have actual websites discovered
- ✅ Websites can be scraped for enrichment signals
- ✅ Higher scores from website + contact form + emails
- ✅ Tier A/B leads will trigger Tavily/Hunter enrichment
- ✅ More complete lead data in spreadsheet

## API Usage Strategy

### Website Discovery Priority:
1. **Google Places Details** (1 API call per lead with place_id)
   - Most accurate
   - Free tier: 2,000/month
   - Use for Google Places leads

2. **SerpAPI** (1 API call per lead)
   - Finds websites via Google search
   - Free tier: 100/month
   - Use when Google Places Details unavailable

3. **Tavily** (1 credit per search)
   - Deep research fallback
   - Free tier: 1,000/month
   - Use as last resort

### Cost Optimization:
- Google Places Details: Only for leads with place_id (already have it)
- SerpAPI: Use sparingly (limited quota)
- Tavily: Use basic search for website discovery (save advanced for Tier A)

## Next Steps

1. **Test the pipeline** with a small batch (--max 10)
2. **Monitor API usage** - check quotas are being used efficiently
3. **Adjust scoring weights** if needed based on results
4. **Consider adding**:
   - LinkedIn URL discovery (via SerpAPI/Tavily)
   - Employee count estimation (via website/Tavily)
   - Tech stack detection improvements

## Files Modified

1. `enrichment/website_discovery.py` - NEW
2. `discovery/yelp_fusion_api.py` - Fixed website mapping
3. `enrichment/enrichment_pipeline.py` - Skip Yelp URLs
4. `main.py` - Added website discovery stage, reordered pipeline

