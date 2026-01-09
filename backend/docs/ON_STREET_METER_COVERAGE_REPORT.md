# On-Street Meter Coverage Analysis Report

**Date:** December 29, 2024  
**Analysis:** Meter-to-CNN Matching Coverage

---

## Executive Summary

**Result:** 99.96% of on-street meters can be matched to CNNs using current data.

**Critical Finding:** 15 out of 37,421 on-street meters (0.04%) CANNOT be matched to the Active Streets dataset.

---

## Detailed Findings

### Dataset Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Meters** | 38,356 | 100% |
| **On-Street Meters** | 37,421 | 97.6% |
| **Off-Street Meters** | 935 | 2.4% |

### On-Street Meter Coverage

| Status | Count | Percentage |
|--------|-------|------------|
| **Matchable (have valid CNN)** | 37,406 | 99.96% |
| **NOT Matchable** | 15 | 0.04% |

### Breakdown of Unmatchable Meters

1. **Missing CNN field:** 14 meters (no `street_seg_ctrln_id`)
2. **Invalid CNN:** 1 meter (CNN = "0", not in Active Streets)

### Key Data Quality Observations

✓ **100% of on-street meters have `blockface_id`**  
✓ **99.96% of on-street meters have valid CNNs**  
✓ **2,308 out of 2,309 unique meter CNNs exist in Active Streets**

---

## Unmatchable Meters (Sample)

| Post ID | Street | Street # | CNN | Blockface ID | Issue |
|---------|--------|----------|-----|--------------|-------|
| 000-00000 | - | 0 | 0 | 0 | Invalid/test record |
| 491-06001 | INDIANA ST | 601 | NULL | 491061 | Missing CNN |
| 331-04009 | BRYANT ST | NULL | NULL | 331041 | Missing CNN |
| 669-00020 | STANYAN ST | NULL | NULL | 669002 | Missing CNN |
| 551-00006 | LAPU-LAPU ST | 6 | NULL | 551002 | Missing CNN |
| 669-00030 | STANYAN ST | NULL | NULL | 669001 | Missing CNN |
| 568-24006 | MISSION ST | 2406 | NULL | 568242 | Missing CNN |
| 562-26004 | MASON ST | 2604 | NULL | 562262 | Missing CNN |

---

## Implications for CNN Master Reference Architecture

### Current State

The current ingestion system (lines 686-785 in `ingest_data_cnn_segments.py`) uses:

1. **Primary Method:** `blockface_id` → Metered Blockfaces → CNN + side
2. **Fallback Method:** CNN + address range → determine side

**Problem:** The fallback method STILL requires a valid CNN, which 15 meters don't have.

### Critical Requirement

**We CANNOT discard on-street meters.** All 37,421 on-street meters must be represented in the system, even the 15 without CNNs.

---

## Recommended Solutions

### Option 1: Use Blockface ID as Primary Key (RECOMMENDED)

Since **100% of on-street meters have `blockface_id`**, we can:

1. Build mapping: `blockface_id` → CNN via Metered Blockfaces dataset
2. For the 15 meters without CNN:
   - Use `blockface_id` to look up in Metered Blockfaces
   - Extract street name, address range, orientation
   - Match to Active Streets using street name + address range
   - If still no match, use spatial proximity (lat/lon)

**Advantage:** Handles 100% of meters, including edge cases

### Option 2: Spatial Fallback for Unmatchable Meters

For meters without valid CNNs:

1. Use meter coordinates (longitude, latitude)
2. Find nearest street segment in Active Streets
3. Validate with street name if available
4. Assign to closest CNN segment

**Advantage:** Guaranteed match for all meters with coordinates

### Option 3: Manual Override Table

Create a manual mapping table for the 15 problematic meters:

```json
{
  "491-06001": {"cnn": "XXXXX", "side": "L", "notes": "Indiana St 601"},
  "331-04009": {"cnn": "XXXXX", "side": "R", "notes": "Bryant St"},
  ...
}
```

**Advantage:** 100% accuracy for known edge cases

---

## Implementation Plan

### Phase 1: Immediate Fix (Handle 15 Unmatchable Meters)

```python
def match_meter_to_cnn_comprehensive(meter):
    """
    Comprehensive meter matching with multiple fallbacks
    Ensures 100% of on-street meters are matched
    """
    cnn = meter.get('street_seg_ctrln_id')
    blockface_id = meter.get('blockface_id')
    
    # Method 1: Direct CNN match (99.96% of meters)
    if cnn and cnn != '0' and cnn in valid_cnns:
        return match_by_cnn(cnn, blockface_id)
    
    # Method 2: Blockface ID lookup (for meters without CNN)
    if blockface_id:
        metered_bf = lookup_metered_blockface(blockface_id)
        if metered_bf:
            # Use street name + address range to find CNN
            cnn = find_cnn_by_street_and_address(
                metered_bf['street_name'],
                metered_bf['fm_addr_no'],
                metered_bf['to_addr_no']
            )
            if cnn:
                return match_by_cnn(cnn, blockface_id)
    
    # Method 3: Spatial proximity fallback
    if meter.get('longitude') and meter.get('latitude'):
        nearest_segment = find_nearest_segment(
            meter['longitude'],
            meter['latitude'],
            meter.get('street_name')  # Validate with street name
        )
        if nearest_segment:
            return nearest_segment
    
    # Method 4: Manual override table
    if meter['post_id'] in manual_overrides:
        return manual_overrides[meter['post_id']]
    
    # Should never reach here for on-street meters
    raise Exception(f"Cannot match on-street meter: {meter['post_id']}")
```

### Phase 2: Data Quality Improvement

1. **Report to SFMTA:** Submit list of 15 meters with missing/invalid CNNs
2. **Request Updates:** Ask SFMTA to update meter dataset with correct CNNs
3. **Monitor:** Track data quality improvements over time

### Phase 3: Validation

1. **Test Coverage:** Verify 100% of on-street meters are matched
2. **Accuracy Check:** Validate spatial matches against street names
3. **Performance:** Ensure fallback methods don't impact query speed

---

## Conclusion

**Current State:**
- 99.96% of on-street meters can be matched using CNN
- 15 meters (0.04%) require fallback strategies

**Recommendation:**
- Implement comprehensive matching with multiple fallbacks
- Use blockface_id + spatial proximity for edge cases
- Maintain manual override table for known issues
- Report data quality issues to SFMTA

**Result:**
- **100% coverage** of on-street meters guaranteed
- **Zero data loss** - no meters discarded
- **Deterministic matching** for 99.96% of meters
- **Fallback strategies** for remaining 0.04%

---

## Related Documents

- [`backend/ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) - Current meter matching implementation
- [`backend/CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md) - Proposed architecture
- [`backend/analyze_on_street_meter_coverage.py`](analyze_on_street_meter_coverage.py) - Analysis script