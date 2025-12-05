# Bryant Street Overlay Investigation - Data Quality Issue

## Issue Description
The parking overlays for Bryant St East (1901-1999) and Bryant St West (1900-1998) are not displaying over the correct sides of the street in the map interface.

## Investigation Date
December 5, 2024

## Findings

### Database Query Results

**CNN:** 3307000  
**Street:** Bryant Street  
**Segment:** Between Mariposa St and 18th St

#### Segment 1 (Left Side - L)
- **Side:** L
- **Address Range:** 1901-1999
- **Cardinal Direction:** East
- **Display Name:** Bryant Street (East side, 1901-1999)
- **Centerline Geometry:** ✓ Present (2 points)
  - First: [-122.410244115, 37.763029333]
  - Last: [-122.410118191, 37.76175942]
- **Blockface Geometry:** ✓ Present (2 points)
  - First: [-122.41024153817027, 37.76186409639788]
  - Last: [-122.41034882745923, 37.762949587938564]
- **Rules:** 1

#### Segment 2 (Right Side - R)
- **Side:** R
- **Address Range:** 1900-1998
- **Cardinal Direction:** West
- **Display Name:** Bryant Street (West side, 1900-1998)
- **Centerline Geometry:** ✓ Present (2 points)
  - First: [-122.410244115, 37.763029333]
  - Last: [-122.410118191, 37.76175942]
- **Blockface Geometry:** ✓ Present (2 points)
  - First: [-122.41029387098263, 37.76302439921921]
  - Last: [-122.41016794698263, 37.76175448621921]
- **Rules:** 1

### Data Quality Checks

✓ **Both sides present:** L and R sides exist  
✓ **No overlapping address ranges** on the same side  
✓ **All segments have cardinal directions** assigned  
✓ **All segments have both centerline and blockface geometries**

## Root Cause Analysis

### Issue Identified: Incorrect Blockface Geometry Coordinates

Comparing the centerline geometry (which represents the street centerline) with the blockface geometry (which should represent the offset for each side):

**Problem:** The blockface geometries for both L and R sides appear to be **swapped or incorrectly offset**.

#### Expected Behavior:
- **Left (L) side** with cardinal direction "East" should have blockface geometry **offset to the east** of the centerline
- **Right (R) side** with cardinal direction "West" should have blockface geometry **offset to the west** of the centerline

#### Actual Behavior:
Looking at the coordinates:
- **Centerline:** [-122.410244115, 37.763029333] to [-122.410118191, 37.76175942]
- **L side blockface:** [-122.41024153817027, 37.76186409639788] to [-122.41034882745923, 37.762949587938564]
- **R side blockface:** [-122.41029387098263, 37.76302439921921] to [-122.41016794698263, 37.76175448621921]

The blockface geometries appear to be on opposite sides of where they should be based on the cardinal directions.

### Potential Causes:

1. **Incorrect Side Assignment During Ingestion**
   - The L/R designation may be reversed relative to the blockface geometry
   - The cardinal direction calculation may be incorrect

2. **Blockface Geometry Source Data Issue**
   - The pep9 dataset (source of blockfaceGeometry) may have incorrect or swapped geometries
   - The spatial offset calculation during ingestion may be flawed

3. **Cardinal Direction Mapping Error**
   - The mapping between L/R sides and cardinal directions (N/S/E/W) may be incorrect
   - The street orientation detection logic may be faulty

## Impact

- **User Experience:** Users see parking regulations displayed on the wrong side of the street
- **Data Accuracy:** Undermines trust in the application's data quality
- **Scope:** This issue likely affects other streets beyond just Bryant St

## Recommended Solutions

### Short-term Fix:
1. **Swap the blockface geometries** for L and R sides for CNN 3307000
2. **Verify the fix** by checking the map display

### Long-term Fix:
1. **Audit the ingestion logic** in [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py)
   - Review the blockface geometry assignment logic
   - Verify the L/R to cardinal direction mapping
   - Check the spatial offset calculations

2. **Create a validation script** to detect similar issues across all street segments:
   - Compare blockface geometry positions relative to centerline
   - Verify cardinal directions match expected offsets
   - Flag segments where geometry appears swapped

3. **Re-ingest affected data** after fixing the root cause

## Files to Review

- [`backend/ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py) - Data ingestion logic
- [`backend/models.py`](backend/models.py) - StreetSegment model definition
- [`backend/main.py`](backend/main.py) - API endpoint that serves blockface data
- [`frontend/src/utils/sfmtaDataFetcher.ts`](frontend/src/utils/sfmtaDataFetcher.ts) - Frontend data transformation

## Next Steps

1. ✅ Investigation complete
2. ⏳ Create comprehensive data quality detection script
3. ⏳ Fix ingestion logic for blockface geometry assignment
4. ⏳ Re-ingest data for affected segments
5. ⏳ Validate fix on map interface