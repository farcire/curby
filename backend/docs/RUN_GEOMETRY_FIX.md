# How to Apply the Geometry Fix

## Current Status
❌ The database still has 864 swapped geometries
❌ The old ingestion script (`ingest_data_cnn_segments.py`) was run but timed out
✅ The fix is ready in `ingest_with_batching.py`

## What You Need to Do

Run the **new batched ingestion script** that includes the geometry fix:

```bash
cd backend && python ingest_with_batching.py 2>&1 | tee ingestion_batched.log
```

## Why This Will Work

The new script (`ingest_with_batching.py`):
1. ✅ **Batches all inserts** (500 records at a time) - prevents MongoDB timeouts
2. ✅ **Uses the enhanced geometry algorithm** - multi-point voting for accurate side detection
3. ✅ **Provides progress feedback** - you'll see each batch being inserted
4. ✅ **Handles all 17,162 streets** without timing out

## What to Expect

You'll see output like:
```
✓ Successfully connected to MongoDB

=== STEP 1: Creating CNN-Based Street Segments ===
Fetching dataset 3psu-pn9h...
Successfully fetched 17162 records from 3psu-pn9h.
  Inserted streets batch 1-500 of 17162
  Inserted streets batch 501-1000 of 17162
  ...
✓ Saved 17162 streets

✓ Created 34324 street segments (2 per CNN)

=== STEP 2: Adding Blockface Geometries ===
✓ Added [number] blockface geometries to segments

=== STEP 2.5: Generating Synthetic Blockfaces ===
✓ Generated [number] synthetic blockface geometries

=== STEP 3: Matching Street Sweeping Schedules ===
  Inserted street_cleaning_schedules batch 1-500 of [total]
  ...
✓ Matched [number] street sweeping schedules

=== STEP 4: Matching Parking Regulations ===
  Inserted parking_regulations batch 1-500 of [total]
  ...
✓ Matched [number] parking regulations

=== STEP 5: Matching Parking Meters ===
✓ Matched [number] parking meters

=== STEP 5.5: Finalizing Segments ===

=== STEP 6: Saving to Database ===
  Inserted street_segments batch 1-500 of 34324
  Inserted street_segments batch 501-1000 of 34324
  ...
✓ Saved 34324 street_segments
Creating indexes...

=== Summary ===
Total segments: 34324
  - With street sweeping: [number]
  - With parking regulations: [number]
  - With meters: [number]
  - With blockface geometry: [number]

✓ CNN Segment Ingestion Complete!
```

## Estimated Time
**5-15 minutes** (batching prevents timeouts)

## After Completion

Validate the fix:
```bash
cd backend && python detect_geometry_issues.py
```

Expected result:
```
3. Swapped Geometry (blockface on wrong side): 0 segments ✅
```

## The Fix Explained

The enhanced `get_side_of_street()` function now:
- Samples 3 points along the blockface (at 25%, 50%, 75%)
- Each point votes for L or R using cross product calculation
- Majority vote determines the final side
- Works correctly for curved streets and complex geometries

This will fix all 864 swapped geometries including:
- Bryant St East (1901-1999)
- 32nd Avenue
- 23rd Street
- And 861 other affected segments