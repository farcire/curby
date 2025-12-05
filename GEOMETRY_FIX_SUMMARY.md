# Blockface Geometry Assignment Fix - Summary

## Problem Identified
- **864 street segments** had blockface geometries assigned to the wrong side (L vs R) of the centerline
- This caused parking overlays to display on the incorrect side of streets in the map interface
- Error rate: ~5% of segments (864 out of 17,162 CNNs × 2 sides = 34,324 segments)

## Root Cause
The `get_side_of_street()` function in [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py:50-114) used a **single-point cross product calculation** to determine which side of the centerline a blockface geometry belongs to. This approach was insufficient for:
- Curved street segments
- Complex geometries
- Streets with irregular shapes

## Solution Implemented

### Enhanced `get_side_of_street()` Function
**Location**: [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py:50-114)

**Key Improvements**:
1. **Multi-point sampling**: Samples 3 points along the blockface (at 25%, 50%, 75% positions)
2. **Voting mechanism**: Each sample point votes for L or R based on cross product
3. **Majority vote**: The side with most votes wins
4. **Adaptive delta**: Uses line length to calculate appropriate tangent vector
5. **Numerical stability**: Threshold check (abs(cross) > 1e-10) to avoid noise

```python
def get_side_of_street(centerline_geo: Dict, blockface_geo: Dict) -> str:
    """
    Determines if the blockface geometry is on the Left or Right side of the centerline.
    Uses multiple sample points along the blockface for robust side determination.
    """
    # Sample multiple points along the blockface for voting
    sample_positions = [0.25, 0.5, 0.75]
    votes = {'L': 0, 'R': 0}
    
    for position in sample_positions:
        # Calculate cross product for each sample point
        # Vote for L or R based on cross product sign
        cross = tangent[0] * to_bf[1] - tangent[1] * to_bf[0]
        if cross > 0:
            votes['L'] += 1
        else:
            votes['R'] += 1
    
    # Return side with most votes
    return 'L' if votes['L'] > votes['R'] else 'R'
```

### MongoDB Connection Improvements
**Location**: [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py:385-404)

Added longer timeout settings to handle network latency:
- `serverSelectionTimeoutMS`: 60 seconds
- `connectTimeoutMS`: 60 seconds  
- `socketTimeoutMS`: 60 seconds
- Connection test with `ping` command before proceeding

### Detection Script Path Fix
**Location**: [`detect_geometry_issues.py`](backend/detect_geometry_issues.py:284)

Fixed output file path from `'backend/geometry_issues_report.json'` to `'geometry_issues_report.json'` to work correctly when run from the backend directory.

## Current Status

### ✅ Completed
1. ✅ Reviewed ingestion logic in [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py)
2. ✅ Ran [`detect_geometry_issues.py`](backend/detect_geometry_issues.py) - identified 864 swapped geometries
3. ✅ Analyzed results and identified root cause (single-point cross product)
4. ✅ Fixed the blockface geometry assignment logic (multi-point voting)
5. ✅ Enhanced MongoDB connection with longer timeouts

### 🔄 In Progress
6. 🔄 Re-ingest affected data
   - **Status**: Ingestion script is running but experiencing MongoDB Atlas connection timeouts
   - **Issue**: Network connectivity to MongoDB Atlas cluster
   - **Next Steps**: 
     - Verify MongoDB Atlas IP whitelist includes current IP
     - Check network connectivity
     - Consider running ingestion during off-peak hours
     - May need to run ingestion locally with stable connection

### ⏳ Pending
7. ⏳ Validate the fix on the map interface
   - After successful re-ingestion, verify:
     - Run detection script again - should show 0 swapped geometries
     - Check specific problem CNNs (e.g., 1712000, 1263000) in database
     - Test map interface to ensure parking overlays display on correct side
     - Verify 32nd Avenue example shows blockface on west side as expected

## Example Problem Cases (Before Fix)

### CNN 1712000 (32nd Avenue)
- **Side L**: Detected as R (addresses 1700-1798, cardinal: East) ❌
- **Side R**: Detected as L (addresses 1701-1799, cardinal: West) ❌

### CNN 1263000 (23rd Street)
- **Side L**: Detected as R (addresses 3201-3249, cardinal: South) ❌
- **Side R**: Detected as L (addresses 3200-3248, cardinal: North) ❌

## Validation Commands

### Re-run Detection Script
```bash
cd backend && python detect_geometry_issues.py
```

Expected output after successful re-ingestion:
```
3. Swapped Geometry (blockface on wrong side): 0 segments  ✅
```

### Check Specific CNN in Database
```python
# MongoDB query to verify CNN 1712000
db.street_segments.find({"cnn": "1712000"})
# Should show:
# - Side L with East cardinal direction
# - Side R with West cardinal direction
```

### Test Map Interface
1. Navigate to 32nd Avenue in the map
2. Verify parking regulations display on correct side
3. Check that blockface geometries align with street sides

## Technical Details

### Cross Product Calculation
The 2D cross product determines which side of a directed line a point lies on:
```
cross = tangent[0] * to_point[1] - tangent[1] * to_point[0]
- Positive cross product → Point is on LEFT side
- Negative cross product → Point is on RIGHT side
```

### Why Multi-Point Sampling Works Better
- Single point can be misleading on curved streets
- Multiple samples provide statistical confidence
- Voting mechanism is robust to local anomalies
- Works well for both straight and curved geometries

## Files Modified

1. [`backend/ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py)
   - Enhanced `get_side_of_street()` function (lines 50-114)
   - Improved MongoDB connection with timeouts (lines 385-404)

2. [`backend/detect_geometry_issues.py`](backend/detect_geometry_issues.py)
   - Fixed output file path (line 284)

## MongoDB Timeout Issue & Solution

The original ingestion script times out when inserting 17,162 street records in a single batch. A new optimized script has been created:

**File**: [`backend/ingest_with_batching.py`](backend/ingest_with_batching.py)

This script:
- Inserts all collections in batches of 500 records
- Prevents MongoDB Atlas timeout errors
- Uses the same enhanced geometry assignment logic
- Provides progress feedback during ingestion

## Next Steps for User

1. **Run Optimized Ingestion Script**:
   ```bash
   cd backend && python ingest_with_batching.py 2>&1 | tee ingestion_with_fix.log
   ```
   This will:
   - Use batched inserts to avoid timeouts
   - Apply the enhanced geometry assignment algorithm
   - Save progress to a log file

2. **Validate Fix**:
   ```bash
   cd backend && python detect_geometry_issues.py
   ```
   Expected output:
   - `Swapped Geometry (blockface on wrong side): 0 segments` ✅

3. **Verify Specific Streets**:
   Check Bryant Street and other problem areas:
   ```bash
   cd backend && python -c "
   import asyncio
   import motor.motor_asyncio
   import os
   from dotenv import load_dotenv
   
   async def check():
       load_dotenv()
       client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
       db = client['curby']
       
       # Check Bryant Street
       segs = await db.street_segments.find({
           'streetName': {'$regex': 'BRYANT', '$options': 'i'},
           'fromAddress': {'$in': ['1900', '1901']}
       }).to_list(None)
       
       for s in segs:
           print(f\"{s['displayName']}: Side {s['side']}, Cardinal {s['cardinalDirection']}\")
       
       client.close()
   
   asyncio.run(check())
   "
   ```

4. **Test Map Interface**:
   - Open frontend application
   - Navigate to Bryant Street (1900-1999 block)
   - Verify both East and West sides display correctly
   - Check 32nd Avenue and 23rd Street as well

## References

- **Socrata API**: SFMTA Open Data Portal
- **Dataset ID**: `pep9-66vw` (Blockface Geometries)
- **Shapely Library**: Python geometric operations
- **MongoDB Atlas**: Cloud database hosting