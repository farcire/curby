# CNN Master Dataset Ingestion Progress Guide

## Current Status (as of last check)

✓ **34,324 street segments created** (~98% of Step 1-2)
⏳ **0 meters** (Step 4 not started yet)
⏳ **0 rules** (Steps 3 & 5 not started yet)

## Ingestion Pipeline Stages

### Stage 1: Create CNN Segments (CURRENT)
- **Status**: ~98% complete (34,324 / ~35,000)
- **What it does**: Creates L/R entries for each CNN from Active Streets dataset
- **Expected time**: 2-5 minutes
- **Progress indicator**: "Processed X/17,500 records..."

### Stage 2: Add Blockface Geometries
- **Status**: Not started
- **What it does**: Links actual blockface geometry data to segments
- **Expected time**: 1-2 minutes

### Stage 3: Match Parking Regulations
- **Status**: Not started
- **What it does**: Spatially matches non-metered regulations (time limits, RPP zones)
- **Expected time**: 5-10 minutes
- **Progress indicator**: "Processed X/50,000 regulations..."

### Stage 4: Match Parking Meters
- **Status**: Not started
- **What it does**: Matches ~28,000 meters to segments with schedules
- **Expected time**: 3-5 minutes
- **Progress indicator**: "Processed X/28,000 meters..."

### Stage 5: Match Street Sweeping
- **Status**: Not started
- **What it does**: Direct CNN+side matching for street cleaning schedules
- **Expected time**: 2-3 minutes
- **Progress indicator**: "Processed X/37,000 schedules..."

### Stage 6: Aggregate & Finalize
- **Status**: Not started
- **What it does**: 
  - Aggregates meter rules (TOW schedules, cap colors)
  - Generates display strings
  - Pre-computes modal content
- **Expected time**: 2-3 minutes

### Stage 7: Save to MongoDB
- **Status**: Not started
- **What it does**: Batch inserts all segments with indexes
- **Expected time**: 2-3 minutes
- **Progress indicator**: "Inserted segments 0 to 1000..."

## Total Expected Runtime

**15-30 minutes** depending on:
- Network speed to SFMTA API
- MongoDB Atlas connection speed
- System resources

## How to Monitor Progress

### Option 1: Watch the main terminal
The ingestion script prints progress every 500-1000 records

### Option 2: Check database periodically
```bash
cd backend && python check_ingestion_status.py
```

### Option 3: Check terminal output
Look for these key messages:
- "✓ Created X street segments"
- "✓ Matched X parking regulations"
- "✓ Mapped X meters"
- "✓ Matched X street sweeping schedules"
- "✓ Saved X street segments to database"

## Signs of Success

When complete, you should see:
- ✓ Total segments: ~35,000
- ✓ Segments with meters: ~5,000-7,000
- ✓ Segments with rules: ~25,000-30,000
- ✓ Segments with street sweeping: ~12,000-15,000

## What If It Hangs?

### Check if it's actually hung:
1. Look at CPU usage (should be 20-50% if running)
2. Check if progress messages stopped for >5 minutes
3. Check MongoDB connection (network issues?)

### If truly hung:
1. Press Ctrl+C to stop
2. Check error messages
3. Verify MongoDB connection
4. Verify SFMTA API token
5. Try running again

## After Completion

### Verify the data:
```bash
cd backend && python -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

async def verify():
    load_dotenv()
    client = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = client.get_default_database() if hasattr(client, 'get_default_database') else client['curby']
    
    total = await db.street_segments.count_documents({})
    with_meters = await db.street_segments.count_documents({'meters': {'\$ne': []}})
    with_rules = await db.street_segments.count_documents({'rules': {'\$ne': []}})
    
    print(f'Total segments: {total:,}')
    print(f'With meters: {with_meters:,}')
    print(f'With rules: {with_rules:,}')
    
    # Get sample
    sample = await db.street_segments.find_one({'meters': {'\$ne': []}})
    if sample:
        print(f\"\\nSample: {sample.get('displayName')}\")
        print(f\"  Meters: {len(sample.get('meters', []))}\")
        print(f\"  Rules: {len(sample.get('rules', []))}\")
        print(f\"  Modal content: {'✓' if 'modalContent' in sample else '✗'}\")
    
    client.close()

asyncio.run(verify())
"
```

### Test queries:
```python
# By CNN + side
segment = await db.street_segments.find_one({'cnn': '123456', 'side': 'L'})

# By meter ID
segment = await db.street_segments.find_one({'meters.post_id': '12345-M'})

# By address
segment = await db.street_segments.find_one({
    'streetName': 'MISSION ST',
    'fromAddress': {'$lte': '1234'},
    'toAddress': {'$gte': '1234'}
})
```

## Next Steps After Ingestion

1. ✓ Verify data completeness
2. ✓ Test query performance
3. ✓ Check pre-computed display strings
4. ✓ Validate modal content
5. ✓ Build API endpoints to query this data
6. ✓ Connect frontend to query by address/location

## Files Created

- `street_segments` collection in MongoDB (main dataset)
- `streets` collection (raw Active Streets data)
- `parking_regulations` collection (raw regulations)
- `street_cleaning_schedules` collection (raw schedules)
- `intersections` collection (intersection data)
- `intersection_permutations` collection (CNN-to-intersection mapping)

## Architecture Benefits

✓ **Unified dataset** - All parking data in one place
✓ **Pre-computed** - No processing at query time
✓ **Indexed** - Fast queries by CNN, address, meter ID
✓ **Complete** - Meters, regulations, street cleaning all included
✓ **Display-ready** - All text pre-formatted for UI
✓ **Refactored logic** - Uses regulation_normalizer.py for consistency