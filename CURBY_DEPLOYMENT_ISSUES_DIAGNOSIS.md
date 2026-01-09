# Curby Deployment Issues - Comprehensive Diagnosis & Fix Plan

**Date:** January 1, 2026  
**Status:** Three Critical Issues Identified

---

## Issue Summary

1. **Modal Blank Screen** (CRITICAL) - Modal crashes when clicking blockface
2. **Performance Issue** - Slow loading despite cached CNN master dataset  
3. **Map Zoom Constraints Missing** - Users can zoom out too far

---

## Issue #1: Modal Blank Screen (CRITICAL)

### Root Cause
Frontend [`BlockfaceDetail.tsx`](frontend/src/components/BlockfaceDetail.tsx:119) references undefined variables:
- Line 119: `formattedRules` - never defined
- Line 134: `nextRestriction` - never defined  
- Lines 56-61: References `blockface.modalContent` which doesn't exist in type definition

### Current Behavior
- User clicks blockface → Modal attempts to render → JavaScript error → Blank screen
- Console shows: "Cannot read property 'map' of undefined"

### Why It Happened
Previous fix attempt added code expecting `modalContent` field from backend, but:
1. Backend doesn't call `format_segment_for_modal()` from regulation normalizer
2. Frontend type definition doesn't include `modalContent` field
3. Fallback logic tries to use `rule.description` but rules show raw types like "Street Cleaning" instead of formatted "Street Cleaning Thu 12am-6am"

---

## Issue #2: Performance - Slow Loading

### Current Architecture
```
User Request → Backend API → MongoDB Query → Return Raw Data → Frontend
```

### Performance Bottleneck Analysis

**Backend (`main.py` lines 101-183):**
- Queries MongoDB for segments in radius
- Returns raw rules without formatting
- NO caching headers
- NO pre-computed display strings

**What's Missing:**
1. Regulation normalizer's `format_segment_for_modal()` not called
2. No HTTP cache headers (Cache-Control, ETag)
3. No service worker for PWA caching
4. Fetches ALL segments in radius (could be 50-100 segments)

### PWA Caching Behavior
**Expected:** First load slow, subsequent loads fast (cached)  
**Actual:** Slow every time (no caching configured)

---

## Issue #3: Map Zoom Constraints

### Current State
[`MapView.tsx`](frontend/src/components/MapView.tsx:59-60) HAS constraints:
```typescript
minZoom: 15,  // Line 59
maxZoom: 18,  // Line 60
```

### Issue
Constraints may not be working as expected. Need to verify if Leaflet is respecting these settings.

---

## Architectural Analysis: Backend vs Frontend Ownership

### Current (Broken) Architecture
```
Backend: Raw data only
Frontend: Tries to format rules → CRASHES
```

### Proposed Architecture
```
Backend (Regulation Normalizer): ALL text/data formatting
Frontend: Pure display shell (graphics, icons, layout only)
```

### What Backend Should Own (Regulation Normalizer)
1. ✅ Rule descriptions: "Street Cleaning Thu 12am-6am"
2. ✅ Time formatting: "8am-6pm" (not "08:00 AM - 06:00 PM")
3. ✅ Day formatting: "Weekdays", "Thu", "M-F"
4. ✅ Duration formatting: "2hr limit" (not "120 minutes")
5. ✅ Exception text: "except permit"
6. ✅ Next restriction: "Thu 12am"
7. ✅ Cross-streets: "Arkansas St → Carolina St"
8. ✅ Location text: "MARIPOSA ST (South, 1501-1699)"
9. ❓ Street name cleaning: **NOT NEEDED** - use `streetnamegc` from Active Streets
10. ❓ Cardinal direction formatting: **NEEDS INVESTIGATION**
11. ❓ Address range formatting: **NEEDS INVESTIGATION**

### What Frontend Should Own
1. ✅ Banner colors (green/red gradients)
2. ✅ Emojis (✅ 🚫 🤔)
3. ✅ Icons (MapPin, AlertCircle, Navigation)
4. ✅ Layout and spacing
5. ✅ Buttons (Report Error, Get Directions)
6. ✅ Animations and transitions

---

## Key Discovery: Street Name Cleaning NOT NEEDED

**Finding:** Active Streets dataset already has `streetnamegc` field with cleaned names  
**Action:** Deprecate `cleanStreetName()` function in frontend  
**Impact:** Simpler code, use SFMTA's official cleaned names

---

## Cardinal Direction & Address Range Formatting

### Questions to Answer:
1. **Cardinal Direction:** What formatting is needed?
   - Current: "North", "South", "East", "West", "L", "R"
   - Desired: ???
   - Source: Multiple datasets (street cleaning, meters, intersections)

2. **Address Range:** What formatting is needed?
   - Current: `fromAddress: 1501, toAddress: 1699`
   - Desired: "1501-1699" or something else?
   - Should backend pre-format or frontend concatenate?

---

## Caching Strategy: Pre-Compute vs Runtime

### Option A: Runtime Formatting (Current Proposal)
```python
# In main.py get_blockfaces()
for doc in db.street_segments.find(query):
    modal_content = format_segment_for_modal(doc)  # ← Add this
    segment_response['modalContent'] = modal_content
```

**Pros:**
- Easy to implement
- Data always fresh
- No storage overhead

**Cons:**
- Adds 5-10ms per segment
- For 50 segments: +250-500ms
- **This could be the performance issue!**

### Option B: Pre-Compute at Ingestion (RECOMMENDED)
```python
# During data ingestion
segment['modalContent'] = format_segment_for_modal(segment)
db.street_segments.insert_one(segment)
```

**Pros:**
- ✅ Zero runtime overhead
- ✅ Faster API responses
- ✅ Solves performance issue
- ✅ Cached in MongoDB CNN master dataset

**Cons:**
- ⚠️ Requires re-ingestion when format changes
- ⚠️ Slightly larger MongoDB storage (~200 bytes per segment)

**Storage Impact:**
- 10,000 segments × 200 bytes = 2MB (negligible)

---

## Recommended Solution

### Phase 1: Fix Modal Crash (IMMEDIATE)
1. Add `modalContent` field to Blockface type
2. Update backend to call `format_segment_for_modal()`
3. Simplify frontend to pure display shell
4. Remove `cleanStreetName()` function
5. Use `streetnamegc` from Active Streets

### Phase 2: Optimize Performance (NEXT)
1. Pre-compute `modalContent` during ingestion
2. Add HTTP cache headers to API
3. Implement service worker for PWA caching
4. Add ETag support for conditional requests

### Phase 3: Fix Zoom Constraints (VERIFY)
1. Test if current constraints work
2. If not, investigate Leaflet configuration
3. Add visual feedback when at zoom limits

---

## Implementation Priority

1. **CRITICAL:** Fix modal crash (blocks all usage)
2. **HIGH:** Optimize performance (poor UX)
3. **MEDIUM:** Fix zoom constraints (minor UX issue)

---

## Next Steps

**Immediate Actions Needed:**
1. Clarify cardinal direction formatting requirements
2. Clarify address range formatting requirements
3. Decide: Runtime formatting (Option A) or Pre-compute (Option B)?
4. Implement Phase 1 fixes

**Questions for User:**
1. What format for cardinal directions? (North/South or N/S or keep as-is?)
2. What format for address ranges? (1501-1699 or "1501 to 1699" or keep separate?)
3. Should we pre-compute at ingestion (Option B) for best performance?