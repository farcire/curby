# Fuzzy Matching Validation Summary

## Overview
Validated the fuzzy matching algorithm against blockface records with known CNN IDs to assess accuracy.

## Results

### Summary Statistics
- **Total test records**: 113 blockfaces with both CNN ID and popupinfo
- **Successfully parsed**: 112 (99.1%)
- **Successfully matched**: 106 (94.6%)
- **Correct CNN matches**: 24 (21.4% accuracy)
- **Failed to match**: 6 records (5.4%)

### Key Findings

#### 1. **Low Accuracy (21.4%)**
The fuzzy matching algorithm correctly identifies the CNN in only ~1 out of 5 cases.

#### 2. **Common Mismatch Patterns**

**Pattern A: Off-by-one CNN errors**
Many predictions are very close to the actual CNN (differ by 1000 or less):
- Actual: 1362000 → Predicted: 1363000 (24th St between Castro & Noe)
- Actual: 2761000 → Predicted: 2762000 (Battery St between Pacific & Jackson)
- Actual: 3562000 → Predicted: 3563000 (California St between Broderick & Divisadero)
- Actual: 5554000 → Predicted: 5547000 (Fillmore St between Geary & Ellis)

**Pattern B: Completely different CNN segments**
Some predictions are far off, suggesting wrong street segment:
- Actual: 797000 → Predicted: 24165000 (17th St between Valencia & Mission)
- Actual: 1689000 → Predicted: 27674000 (31st Ave between Ortega & Noriega)
- Actual: 2136000 → Predicted: 24189000 (Alameda St between Potrero & Utah)

**Pattern C: No match found**
6 records couldn't be matched at all:
- 3rd Street between Howard St and Mission St
- 3rd Street between Shafter Ave and Revere Ave
- 4th Street between Bluxome St and Brannan St
- Broadway Street between Sansome St and Battery St

#### 3. **Root Causes**

**Issue 1: Street Intersections Dataset Limitations**
The `pu5n-qu5c` dataset has fields: `cnn`, `streetname`, `from_st`, `limits`, `theorder`

The algorithm tries to match:
- Street name (from popupinfo) → `streetname` field ✓
- Cross streets (from/to) → `from_st` field (only ONE cross street) ✗

**Problem**: The dataset only has ONE cross street (`from_st`), but blockfaces are defined by TWO cross streets (from_st and to_st). This makes it impossible to uniquely identify a segment.

**Issue 2: Multiple Segments Per Street**
A single street like "17th Street" has many CNN segments (one per block). Without both cross streets, we can't distinguish between:
- 17th St between Valencia & Mission (CNN 797000)
- 17th St between Mission & Capp (different CNN)
- 17th St between Capp & South Van Ness (different CNN)

**Issue 3: Cardinal Direction Mapping**
The heuristic mapping of cardinal directions to L/R sides is unreliable:
- North/East → R side
- South/West → L side

This assumes streets run in specific orientations, which isn't always true in SF's grid.

## Recommendations

### Option 1: Use a Better Dataset
Find a dataset that has:
- CNN ID
- Both cross streets (from AND to)
- Or explicit segment boundaries

**Potential datasets to investigate:**
- Street centerline network dataset (may have segment endpoints)
- Address ranges dataset (may have block-level granularity)
- Parking meter dataset (has CNN and specific locations)

### Option 2: Improve Matching Logic
If we must use the current dataset:

1. **Use geometry-based matching**
   - Match by spatial proximity instead of text matching
   - Use the blockface geometry to find the nearest CNN segment

2. **Build a CNN segment lookup table**
   - Pre-process all CNN segments with their cross streets
   - Create a comprehensive mapping of street + cross streets → CNN

3. **Use address ranges**
   - If available, use address numbers to narrow down segments
   - Match address ranges to CNN segments

### Option 3: Hybrid Approach
1. Use fuzzy matching as a first pass to narrow candidates
2. Use geometry-based validation to select the correct CNN
3. Fall back to manual verification for low-confidence matches

## Next Steps

1. **Investigate alternative datasets** that have better CNN segment information
2. **Implement geometry-based matching** using spatial joins
3. **Create a CNN segment reference table** from multiple data sources
4. **Test hybrid approach** combining text and geometry matching

## Conclusion

The current fuzzy matching approach using the street intersections dataset (`pu5n-qu5c`) achieves only 21.4% accuracy due to:
- Insufficient cross street information (only one cross street available)
- Inability to uniquely identify street segments
- Unreliable cardinal direction mapping

**A geometry-based approach or a better reference dataset is needed for reliable CNN matching.**