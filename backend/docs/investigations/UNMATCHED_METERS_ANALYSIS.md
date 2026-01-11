# Unmatched Meters Analysis

**Date:** December 29, 2024  
**Status:** In Progress

## Summary

The ingestion reported **15 meters failed to match** out of 38,356 total meters (99.96% success rate).

## Initial Findings

From preliminary analysis, we found:

### 1. Placeholder/Test Record
- **Post ID:** 000-00000
- **CNN:** 0
- **Blockface ID:** 0
- **Location:** 0 nan
- **Coordinates:** (37.7702, -122.46475)
- **Reason:** Blockface ID not in metered blockfaces dataset
- **Analysis:** This appears to be a test/placeholder record with all zero values

## Failure Points

Meters can fail to match at two points in the ingestion logic:

### Failure Point 1: Initial Validation (Line 710)
```python
if not cnn or not post_id:
    match_stats["failed"] += 1
    continue
```
Meters without a valid CNN or post_id are immediately rejected.

### Failure Point 2: Matching Logic (Line 781)
```python
if matched_segment:
    match_stats[match_method] += 1
else:
    match_stats["failed"] += 1
```
Meters that pass validation but fail both:
- **Method 1:** Blockface ID match (primary method)
- **Method 2:** CNN + address range fallback

## Matching Methods

### Method 1: Blockface ID Match (Primary - Most Accurate)
- Uses `blockface_id` from meter record
- Looks up corresponding CNN and side from metered blockfaces dataset
- Finds segment with matching CNN and side
- **Success Rate:** 38,341 meters (100.0% of matched meters)

### Method 2: CNN + Address Fallback
- Used when blockface_id is missing or not found
- Matches by CNN and checks if meter's street number falls within segment's address range
- **Success Rate:** 0 meters (not needed - blockface matching was sufficient)

## Possible Reasons for Failures

1. **Missing Data:** Meter has no CNN or post_id
2. **Orphaned Blockface:** Blockface ID exists but not in metered blockfaces dataset
3. **CNN Mismatch:** Blockface ID maps to a CNN that doesn't exist in segments
4. **Side Mismatch:** Blockface ID maps to a CNN+side combination that doesn't exist
5. **Test/Placeholder Records:** Invalid data like the 000-00000 record

## Next Steps

1. ✅ Complete full analysis of all 15 unmatched meters
2. 📊 Categorize failures by reason
3. 🔍 Investigate if any failures represent real meters that should be matched
4. 📝 Document findings and recommendations

## Full Results - All 15 Unmatched Meters

### Pattern Analysis

**Key Finding:** 14 out of 15 failures (93%) have the same root cause:
- **CNN field is NaN/missing** in the meters dataset
- Blockface ID exists and is valid
- But without CNN, we cannot match to street segments

### Detailed List

#### 1. Test/Placeholder Record
- **Post ID:** 000-00000
- **CNN:** 0
- **Blockface ID:** 0
- **Location:** 0 nan
- **Issue:** Invalid test data with all zeros

#### 2-15. Missing CNN Data (14 meters)
All have valid blockface IDs but missing CNN values:

| # | Post ID | Blockface ID | Location | Coordinates |
|---|---------|--------------|----------|-------------|
| 2 | 491-06001 | 491061 | 601 INDIANA ST | (37.762, -122.391) |
| 3 | 331-04009 | 331041 | BRYANT ST | (37.782, -122.395) |
| 4 | 669-00020 | 669002 | STANYAN ST | (37.781, -122.456) |
| 5 | 551-00006 | 551002 | 6 LAPU-LAPU ST | (37.782, -122.399) |
| 6 | 669-00030 | 669001 | STANYAN ST | (37.781, -122.456) |
| 7 | 568-24006 | 568242 | 2406 MISSION ST | (37.757, -122.419) |
| 8 | 562-26004 | 562262 | 2604 MASON ST | (37.808, -122.414) |
| 9 | 669-00010 | 669001 | STANYAN ST | (37.781, -122.456) |
| 10 | 222-31007 | 222311 | 3107 22ND ST | (37.755, -122.418) |
| 11 | 669-00040 | 669002 | STANYAN ST | (37.781, -122.456) |
| 12 | 418-02003 | 418021 | 203 FOLSOM ST | (37.789, -122.392) |
| 13 | 658-04003 | 658041 | 403 SPEAR ST | (37.789, -122.389) |
| 14 | 418-00003 | 418001 | 3 FOLSOM ST | (37.790, -122.391) |
| 15 | 363-10005 | 363101 | 1005 COLUMBUS AVE | (37.804, -122.416) |

### Notable Patterns

1. **Stanyan Street Cluster:** 4 meters on Stanyan St (post IDs 669-00020, 669-00030, 669-00010, 669-00040)
2. **Downtown Meters:** Several in downtown SF (Folsom St, Spear St)
3. **Mission District:** Mission St and nearby streets

## Root Cause Analysis

### Why These Meters Failed

**The Two-Step Matching Process:**

Our matching algorithm works like this:
```
Step 1: blockface_id → Look up in metered_blockfaces → Get side (L or R)
Step 2: meter.CNN + side → Find segment with matching (CNN, side)
```

**What Goes Wrong:**

For these 14 meters:
1. ✅ **Step 1 succeeds:** Blockface ID 491061 → Found in metered blockfaces → Side = "L"
2. ❌ **Step 2 fails:** Meter's CNN field is `nan` (missing)
3. ❌ Cannot find segment with (CNN=nan, side="L")

**Key Discovery:**
- The **metered blockfaces dataset does NOT contain CNN**
- It only has: blockface_id, street_name, side, address_range
- We **must** get CNN from the meter record itself
- But for these 14 meters, the `street_seg_ctrln_id` field is NaN

**Example: Meter 491-06001**
```
Meter record:
  post_id: 491-06001
  blockface_id: 491061
  CNN: nan ← MISSING!
  location: 601 INDIANA ST

Metered blockfaces lookup:
  blockface_id 491061 → street: INDIANA ST, side: L, range: 601-699

Attempted match:
  Need segment with: CNN=nan, side=L
  Result: ❌ Cannot match with missing CNN
```

### Why This Matters (or Doesn't)

**Impact Assessment: MINIMAL**
- Only 15 out of 38,356 meters affected (0.04%)
- 14 of these are data quality issues in the source dataset (missing CNN)
- 1 is a test/placeholder record
- All 15 have valid GPS coordinates, so they could potentially be matched spatially if needed

## Recommendations

### Option 1: Accept Current State ✅ RECOMMENDED
- 99.96% success rate is excellent
- The 14 meters with missing CNNs are data quality issues in SFMTA's source data
- Not worth complex workarounds for 0.04% of meters

### Option 2: Spatial Fallback (If Needed)
If these 14 meters are critical, could implement:
```python
# Use GPS coordinates to find nearest street segment
# Match meter to closest segment within reasonable distance
```

### Option 3: Report to SFMTA
- The 14 meters with missing CNNs should be reported to SFMTA
- They can update their source data to include the CNN values

## Conclusion

**Status: ✅ RESOLVED - No Action Needed**

The 15 unmatched meters represent:
- 1 invalid test record (can be ignored)
- 14 meters with missing CNN data in SFMTA's source dataset

With a 99.96% success rate, the meter matching system is working excellently. The failures are due to data quality issues in the source data, not problems with our matching logic.

---

## Technical Details

**Datasets Used:**
- Meters: `8vzz-qzz9` (38,356 records)
- Metered Blockfaces: `mk27-a5x2` (3,131 records)
- Street Segments: MongoDB `street_segments` collection (34,324 records)

**Analysis Script:** `backend/list_unmatched_meters.py`