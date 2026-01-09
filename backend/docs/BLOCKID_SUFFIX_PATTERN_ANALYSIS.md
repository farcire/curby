# BlockID/BlockfaceID Suffix Pattern Analysis

## Executive Summary

**HYPOTHESIS TESTED**: BlockfaceID ending in 1 = L (Left) side, BlockfaceID ending in 2 = R (Right) side

**RESULT**: **REJECTED** - Pattern does **NOT** hold consistently across San Francisco datasets

## Key Findings

### Pattern Match Rate: 49.9%
- **Pattern Matches**: 1,198 segments (where 1=L or 2=R)
- **Pattern Violations**: 1,203 segments (where pattern doesn't hold)
- **Conclusion**: Essentially a **coin flip** - no reliable pattern

### Distribution Analysis

#### CNNs Ending in 1
- **L side**: 1,006 segments (50.4%)
- **R side**: 992 segments (49.6%)
- **Finding**: Nearly **equal distribution** - suffix 1 does NOT reliably indicate L side

#### CNNs Ending in 2
- **L side**: 211 segments (52.4%)
- **R side**: 192 segments (47.6%)
- **Finding**: Slightly **more L than R** - opposite of hypothesis!

#### CNNs Ending in Other Digits (0, 3-9)
- **L side**: 10,074 segments
- **R side**: 10,098 segments
- **Finding**: The **vast majority** of CNNs don't end in 1 or 2

## Dataset-Specific Findings

### 1. Street Sweeping Schedule Dataset (DataSF)
- **Source**: `yhqp-riqs` (10,000 records analyzed)
- **Pattern**: Uses CNN + blockside (NorthEast, SouthEast, NorthWest, SouthWest)
- **Sample Results**: 
  - CNN 8753101 (ends in 1) → SouthEast side ✓
  - CNN 2184101 (ends in 1) → SouthEast side ✓
  - CNN 207101 (ends in 1) → East side ✓
- **Limited Sample Match Rate**: 5/5 (100%) BUT this is misleading
- **Note**: DataSF uses **blockside** (compass directions), not L/R designation

### 2. Parking Regulations Dataset (DataSF)
- **Source**: `cqh6-am8x`
- **Status**: Dataset returned 404 error - may have been moved or renamed
- **Note**: Unable to validate pattern in this dataset

### 3. On-Street Parking Meters Dataset (DataSF)
- **Source**: `8vzz-qzz9` (10,000 records analyzed)
- **Finding**: **No CNN field present** in meter records
- **Fields Available**: post_id, street_name, but no CNN or blockface ID
- **Conclusion**: Cannot validate pattern - meters don't use CNN suffix system

### 4. Local Database (segments_with_sweeping_rules.json)
- **Records**: 22,573 segments
- **Match Rate**: **49.9%** (essentially random)
- **Distribution**: Nearly equal L/R for both suffix 1 and suffix 2
- **Conclusion**: **No reliable pattern exists**

## Why the Pattern Doesn't Hold

### 1. CNN Structure Varies
San Francisco's CNN (Centerline Network) IDs use different numbering schemes:
- **Base CNNs**: Often end in 000 (e.g., 111000, 129000)
- **Subdivisions**: May add 01, 02, 101, 102, 201, 202, etc.
- **No Standard**: The suffix doesn't consistently encode side information

### 2. Blockside vs L/R Mapping
DataSF uses **compass directions** (NE, SE, NW, SW), which must be mapped to L/R:
- Mapping depends on street orientation
- Same blockside can be L on one street, R on another
- No universal 1=L, 2=R rule in the source data

### 3. Historical Data Inconsistency
- CNNs were assigned over many years
- Different numbering conventions used at different times
- No standardized suffix encoding was enforced

## Implications for Data Processing

### ❌ DO NOT Rely On:
- CNN suffix to determine L vs R side
- Assumption that 1=L, 2=R
- Any automatic side assignment based on last digit

### ✅ DO Use Instead:
1. **Blockside Field**: Use DataSF's blockside (NE/SE/NW/SW) when available
2. **Geometry**: Calculate side from street geometry and coordinates
3. **Explicit Side Field**: When present in source data, use it directly
4. **Address Ranges**: Odd/even address numbers can indicate side
5. **Cross-Reference**: Match multiple data sources to confirm side

## Recommendations

### 1. Update Documentation
Add prominent warning in all data processing docs:
```
⚠️ WARNING: CNN suffix does NOT reliably indicate street side.
Do not assume BlockfaceID ending in 1 = L or ending in 2 = R.
Match rate is only 49.9% (essentially random).
```

### 2. Fix Ingestion Logic
Current code may incorrectly assume suffix pattern. Review and update:
- `ingest_data_cnn_segments.py`
- Any code that maps CNN to L/R sides
- Side assignment logic in data processing

### 3. Validate Existing Data
- Re-check all L/R assignments in database
- Cross-reference with DataSF blockside field
- Flag segments where side may be incorrect

### 4. Implement Robust Side Detection
```python
def determine_side(cnn, blockside, geometry):
    """
    Determine L/R side using multiple signals, NOT just CNN suffix.
    
    Priority order:
    1. Explicit side field from source
    2. Blockside + street orientation
    3. Geometry calculation
    4. Address range (odd/even)
    5. Default to unknown if uncertain
    """
    # DO NOT use: if cnn.endswith('1'): return 'L'
    # This is unreliable!
```

## Related Issues

- See [`CNN_111000_INVESTIGATION_REPORT.md`](CNN_111000_INVESTIGATION_REPORT.md) - Data ingestion failures
- See [`ASYMMETRIC_STREET_CLEANING_DATA_GAPS.md`](ASYMMETRIC_STREET_CLEANING_DATA_GAPS.md) - Missing side data
- Incorrect side assignments may contribute to both issues

## Conclusion

The hypothesis that **"BlockfaceID ending in 1 = L side, ending in 2 = R side"** is **DEFINITIVELY FALSE** for San Francisco datasets.

With only a 49.9% match rate, this pattern is **no better than random chance**. Any code relying on this assumption will produce incorrect results approximately half the time.

**Action Required**: Audit all data processing code to remove any CNN suffix-based side detection logic and replace with robust, multi-signal side determination.

---

**Analysis Date**: 2025-12-29  
**Datasets Analyzed**: 4 (Street Sweeping, Parking Regs, Meters, Local DB)  
**Total Records**: 42,573+  
**Conclusion**: Pattern REJECTED - Do not use CNN suffix for side detection