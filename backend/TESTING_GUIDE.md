# Testing Guide: Database Join and Geospatial Side Assignment

This guide walks you through testing the current state, implementing fixes, and verifying the results.

---

## Phase 1: Verify Current State (Before Fixes)

### Step 1: Check if Database Has Data

```bash
cd backend
python verify_db.py
```

**Expected**: Should show count of street cleaning schedules.

### Step 2: Run Full Validation

```bash
python validate_side_assignments.py
```

**What to look for**:
- ✅ How many blockfaces have side assignments (L/R vs None)?
- ❌ **CRITICAL**: Should show NO 'parking-regulation' rules
- ℹ️ Should show regulations exist in separate `parking_regulations` collection
- ⚠️ May show blockfaces with rules but no side assignment

### Step 3: Inspect Parking Regulations Structure

```bash
python inspect_non_metered_regs.py
```

**What to check**:
- Does the dataset have a `cnn` or `cnn_id` field?
- Does it have `shape` or `geometry` field?
- Does it have side information like `cnnrightleft` or `blockside`?

### Step 4: Check Current Blockface Data

Run this Python snippet to see what's in blockfaces:

```bash
python3 << 'EOF'
import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
import json

async def check():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.get_default_database() if client.get_default_database() else client["curby"]
    
    # Get one blockface with rules
    bf = await db.blockfaces.find_one({"rules": {"$ne": []}})
    if bf:
        print("Sample Blockface with Rules:")
        print(json.dumps({
            "id": bf.get("id"),
            "streetName": bf.get("streetName"),
            "side": bf.get("side"),
            "rules": bf.get("rules", [])
        }, indent=2))
    else:
        print("No blockfaces with rules found")
    
    client.close()

asyncio.run(check())
EOF
```

**Expected**: Should show street-sweeping and meter rules, but NO parking-regulation rules.

---

## Phase 2: Understand the Problem

Review the analysis documents:

1. **Main Analysis**: Read [`GEOSPATIAL_JOIN_ANALYSIS.md`](GEOSPATIAL_JOIN_ANALYSIS.md)
2. **Key Issue**: Parking regulations are stored separately, never joined to blockfaces
3. **Root Cause**: Missing implementation of geometric side matching for regulations

---

## Phase 3: Implement the Fix

### Option A: Quick Test with Mock Data

Create a test script to verify the fix logic works:

```bash
cat > test_side_logic.py << 'EOF'
from shapely.geometry import shape, LineString

def get_side_of_street(centerline_geo, blockface_geo, debug_info=""):
    """Test the geometric side determination logic."""
    try:
        cl_shape = shape(centerline_geo)
        bf_shape = shape(blockface_geo)
        
        if not isinstance(cl_shape, LineString) or not isinstance(bf_shape, LineString):
            print(f"⚠️ Invalid geometry types ({debug_info})")
            return None
            
        bf_mid = bf_shape.interpolate(0.5, normalized=True)
        projected_dist = cl_shape.project(bf_mid)
        projected_point = cl_shape.interpolate(projected_dist)
        
        delta = 0.001
        if projected_dist + delta > cl_shape.length:
             p1 = cl_shape.interpolate(projected_dist - delta)
             p2 = projected_point
        else:
             p1 = projected_point
             p2 = cl_shape.interpolate(projected_dist + delta)
             
        cl_vec = (p2.x - p1.x, p2.y - p1.y)
        to_bf_vec = (bf_mid.x - projected_point.x, bf_mid.y - projected_point.y)
        
        cross_product = cl_vec[0] * to_bf_vec[1] - cl_vec[1] * to_bf_vec[0]
        
        result = 'L' if cross_product > 0 else 'R'
        print(f"✓ Side determined: {result} ({debug_info})")
        return result
        
    except Exception as e:
        print(f"⚠️ Side determination failed ({debug_info}): {e}")
        return None

# Test with mock data
centerline = {
    "type": "LineString",
    "coordinates": [[0, 0], [1, 0], [2, 0]]  # Horizontal line going east
}

left_blockface = {
    "type": "LineString", 
    "coordinates": [[0.5, 0.1], [1.5, 0.1]]  # Parallel line above (north/left)
}

right_blockface = {
    "type": "LineString",
    "coordinates": [[0.5, -0.1], [1.5, -0.1]]  # Parallel line below (south/right)
}

print("\n=== Testing Side Determination Logic ===")
print(f"Left blockface: {get_side_of_street(centerline, left_blockface, 'north side')}")
print(f"Right blockface: {get_side_of_street(centerline, right_blockface, 'south side')}")
EOF

python test_side_logic.py
```

**Expected Output**:
```
✓ Side determined: L (north side)
Left blockface: L
✓ Side determined: R (south side)  
Right blockface: R
```

### Option B: Full Implementation

Follow the implementation guide in [`GEOSPATIAL_JOIN_ANALYSIS.md`](GEOSPATIAL_JOIN_ANALYSIS.md), section "Required Changes".

The key changes needed in [`ingest_data.py`](ingest_data.py):

1. **After line 280**, add code to join parking regulations using geometric side matching
2. **Update `get_side_of_street()`** to add debug logging
3. **Update street cleaning join** (lines 243-245) to be more permissive

---

## Phase 4: Test After Implementing Fix

### Step 1: Re-run Data Ingestion

```bash
bash run_ingestion.sh
```

**What to watch for**:
- Messages about processing parking regulations
- Count of regulations added to blockfaces
- Any errors or warnings about side determination failures

### Step 2: Run Validation Again

```bash
python validate_side_assignments.py
```

**What should change**:
- ✅ **Should now show** 'parking-regulation' rules in the distribution
- ✅ Count of rules should increase significantly
- ✅ More blockfaces should have rules

### Step 3: Verify Specific Blockface

```bash
python3 << 'EOF'
import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
import json

async def check():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.get_default_database() if client.get_default_database() else client["curby"]
    
    # Find blockface with parking regulations
    bf = await db.blockfaces.find_one({
        "rules": {"$elemMatch": {"type": "parking-regulation"}}
    })
    
    if bf:
        print("✅ SUCCESS: Found blockface with parking regulations!")
        print(json.dumps({
            "id": bf.get("id"),
            "streetName": bf.get("streetName"), 
            "side": bf.get("side"),
            "rules": [r for r in bf.get("rules", []) if r.get("type") == "parking-regulation"]
        }, indent=2))
    else:
        print("❌ FAILED: No blockfaces with parking regulations found")
    
    client.close()

asyncio.run(check())
EOF
```

**Expected After Fix**: Should show a blockface with parking-regulation rules.

### Step 4: Compare Before/After Statistics

Create a comparison report:

```bash
cat > compare_results.py << 'EOF'
import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio

async def stats():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.get_default_database() if client.get_default_database() else client["curby"]
    
    print("\n=== DATA COMPLETENESS REPORT ===\n")
    
    total_blockfaces = await db.blockfaces.count_documents({})
    with_rules = await db.blockfaces.count_documents({"rules": {"$ne": []}})
    
    print(f"Total Blockfaces: {total_blockfaces}")
    print(f"Blockfaces with Rules: {with_rules} ({with_rules/total_blockfaces*100:.1f}%)")
    
    # Rules by type
    pipeline = [
        {"$unwind": "$rules"},
        {"$group": {"_id": "$rules.type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    rules = await db.blockfaces.aggregate(pipeline).to_list(None)
    
    print("\nRules by Type:")
    for r in rules:
        print(f"  {r['_id']}: {r['count']}")
    
    # Side coverage
    has_L = await db.blockfaces.count_documents({"side": "L"})
    has_R = await db.blockfaces.count_documents({"side": "R"})
    no_side = await db.blockfaces.count_documents({"side": None})
    
    print(f"\nSide Assignment:")
    print(f"  Left (L): {has_L}")
    print(f"  Right (R): {has_R}")
    print(f"  Unknown: {no_side}")
    
    client.close()

asyncio.run(stats())
EOF

python compare_results.py
```

---

## Phase 5: Integration Testing

### Test with Frontend

If you have the frontend running:

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open map and click on blockfaces
4. Verify parking regulations show up in the detail panel

### Test Specific Street

Query a known street to verify all rules are present:

```bash
python3 << 'EOF'
import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio

async def check_street():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.get_default_database() if client.get_default_database() else client["curby"]
    
    # Example: Find all blockfaces on "BRYANT ST"
    blockfaces = await db.blockfaces.find(
        {"streetName": {"$regex": "BRYANT", "$options": "i"}},
        {"id": 1, "streetName": 1, "side": 1, "rules": 1}
    ).limit(5).to_list(None)
    
    print(f"\n=== BRYANT STREET BLOCKFACES ===\n")
    for bf in blockfaces:
        print(f"{bf.get('streetName')} - Side {bf.get('side')}")
        print(f"  Rules: {[r.get('type') for r in bf.get('rules', [])]}")
        print()
    
    client.close()

asyncio.run(check_street())
EOF
```

---

## Success Criteria

After implementing and testing the fix, you should see:

- ✅ Parking regulations joined to blockfaces (not just in separate collection)
- ✅ Each blockface has proper side assignment (L or R)
- ✅ Rules correctly matched to the appropriate side
- ✅ Validation shows 'parking-regulation' in rule types
- ✅ Frontend displays complete parking rules for each blockface

---

## Troubleshooting

### Issue: No data in database
**Solution**: Run `bash run_ingestion.sh` first

### Issue: Side determination returning None
**Solution**: Check geometry validity and add debug logging to `get_side_of_street()`

### Issue: Regulations have no CNN field
**Solution**: Use spatial join instead of CNN-based join (see Change 1, Method B in analysis doc)

### Issue: Still no parking regulations after fix
**Solution**: 
1. Check if regulations were actually fetched (check count)
2. Verify geometric matching logic is being called
3. Add print statements to debug the join process

---

## Quick Reference Commands

```bash
# Run validation
python backend/validate_side_assignments.py

# Check regulations structure
python backend/inspect_non_metered_regs.py

# Re-run ingestion
bash backend/run_ingestion.sh

# Test side logic
python backend/test_side_logic.py