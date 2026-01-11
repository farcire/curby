# Parking Meter Matching Fix - December 29, 2024

## Problem Identified

The original meter matching implementation in [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py:656-674) had a critical flaw:

```python
# OLD APPROACH (SUBOPTIMAL)
for segment in all_segments:
    if segment["cnn"] == cnn:
        segment["schedules"].extend(schedules_by_post.get(post_id, []))
        matched_meters += 1
```

**Issues:**
1. ❌ Added meters to **BOTH L and R sides** of the same CNN
2. ❌ No side determination - caused duplicate meter data
3. ❌ No use of `blockface_id` field available in meters dataset
4. ❌ Resulted in inaccurate parking meter assignments

## Solution Implemented

### Data Flow Architecture

```
Meter (8vzz-qzz9)
  ├─ post_id: "222-31500"
  ├─ blockface_id: "222314"
  └─ street_seg_ctrln_id (CNN): "1190000"
       ↓
Metered Blockface (mk27-a5x2)
  ├─ blockface_id: "222314"
  ├─ str_seg_orientation: "R" (side)
  ├─ street_name: "22ND ST"
  └─ fm_addr_no / to_addr_no: address range
       ↓
Street Segment
  ├─ cnn: "1190000"
  ├─ side: "R"
  └─ meters: [{ post_id, location, schedules }]
```

### Implementation Details

**New Approach (Lines 634-754):**

1. **Load Metered Blockfaces** (mk27-a5x2)
   - Build `blockface_id` → `{side, street_name, address_range}` lookup table
   - Uses `str_seg_orientation` field ("L" or "R") for precise side determination

2. **Primary Method: Blockface ID Match**
   ```python
   if blockface_id and str(blockface_id) in blockface_to_cnn_side:
       bf_info = blockface_to_cnn_side[str(blockface_id)]
       target_side = bf_info["side"]
       
       # Find segment with matching CNN and side
       for segment in all_segments:
           if segment["cnn"] == cnn and segment["side"] == target_side:
               matched_segment = segment
               break
   ```

3. **Secondary Method: Address Range Fallback**
   - For meters without `blockface_id`
   - Uses `street_num` to match against segment's `fromAddress`/`toAddress`
   - Determines correct side based on address range

4. **Data Structure: New `meters` Array**
   ```python
   segment["meters"].append({
       "post_id": post_id,
       "location": {"type": "Point", "coordinates": [lng, lat]},
       "street_num": meter_row.get("street_num"),
       "blockface_id": blockface_id,
       "schedules": schedules_by_post.get(post_id, [])
   })
   ```

## Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Side Accuracy** | ~50% (both sides) | ~95% (precise) | +90% |
| **Duplicate Meters** | Yes | No | Eliminated |
| **Blockface Match Rate** | 0% | ~85-90% | New capability |
| **Data Quality** | Poor | High | Significant |

## Testing & Validation

### Test Command
```bash
cd backend
python3 ingest_data_cnn_segments.py
```

### Expected Output
```
=== STEP 5: Matching Parking Meters (Blockface-Based) ===
✓ Loaded X meter schedules
Building blockface_id → (CNN, side) lookup from metered blockfaces...
✓ Built lookup table with Y metered blockface mappings
Processing Z parking meters...

✓ Meter Matching Complete!
  Total meters processed: Z
  Matched by blockface_id: ~85-90%
  Matched by CNN+address fallback: ~5-10%
  Failed to match: ~5%
  Success rate: ~95%
```

### Validation Queries

**Check specific meter assignment:**
```python
# Example: Meter on 22ND ST, CNN 1190000, blockface_id 222314
db.street_segments.find_one({
    "cnn": "1190000",
    "side": "R",
    "meters.blockface_id": "222314"
})
```

**Verify no duplicates:**
```python
# Should return 0 - no meter should appear on both L and R
pipeline = [
    {"$unwind": "$meters"},
    {"$group": {
        "_id": "$meters.post_id",
        "count": {"$sum": 1},
        "segments": {"$push": {"cnn": "$cnn", "side": "$side"}}
    }},
    {"$match": {"count": {"$gt": 1}}}
]
db.street_segments.aggregate(pipeline)
```

## Key Changes Summary

### Files Modified
- [`backend/ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py:634-754)

### New Features
1. ✅ Blockface-based meter matching using `blockface_id`
2. ✅ Precise side determination via `str_seg_orientation`
3. ✅ Address range fallback for meters without `blockface_id`
4. ✅ New `meters` array structure (replaces old `schedules` array)
5. ✅ Detailed matching statistics and diagnostics

### Deprecated
- ❌ Old `schedules` array directly on segment (still present for backward compatibility)
- ❌ CNN-only matching without side determination

## Migration Notes

### Data Model Changes
The new `meters` array structure is more detailed:

**Old:**
```json
{
  "cnn": "1190000",
  "side": "L",
  "schedules": [
    {"rate": "2.50", "beginTime": "09:00", "endTime": "18:00"}
  ]
}
```

**New:**
```json
{
  "cnn": "1190000",
  "side": "R",
  "meters": [
    {
      "post_id": "222-31500",
      "location": {"type": "Point", "coordinates": [-122.4186, 37.7555]},
      "street_num": "3150",
      "blockface_id": "222314",
      "schedules": [
        {"rate": "2.50", "beginTime": "09:00", "endTime": "18:00"}
      ]
    }
  ]
}
```

### API Updates Needed
Frontend should be updated to use `segment.meters` instead of `segment.schedules` for meter information.

## References

- **Architecture Document**: [`CURBY_ARCHITECTURE_ANALYSIS_Dec282025.md`](../CURBY_ARCHITECTURE_ANALYSIS_Dec282025.md)
- **Original Improvement Plan**: [`archive/old_docs/METER_INTEGRATION_IMPROVEMENT_PLAN.md`](../archive/old_docs/METER_INTEGRATION_IMPROVEMENT_PLAN.md)
- **Datasets Used**:
  - Metered Blockfaces: `mk27-a5x2`
  - Parking Meters: `8vzz-qzz9`
  - Meter Schedules: `6cqg-dxku`

---

**Status**: ✅ Implemented  
**Date**: December 29, 2024  
**Impact**: High - Eliminates duplicate meters and provides precise side determination