# Geospatial Join Analysis: Regulation Side Assignment Issue

## Executive Summary

**Problem**: Parking regulations from dataset `hi6h-neyh` are NOT being joined to blockfaces during data ingestion. Street sweeping rules work partially, but both systems fail to reliably determine which side of the street (Left/Right) regulations apply to.

**Impact**: 
- Non-metered parking regulations (time limits, RPP zones) are stored separately and never attached to blockfaces
- Users cannot see accurate parking rules for specific blockfaces
- The system cannot distinguish between regulations on opposite sides of the same street

**Root Cause**: The geometric side determination logic exists but is incomplete and not applied to parking regulations.

---

## Current Architecture Analysis

### 1. Data Flow (from [`ingest_data.py`](backend/ingest_data.py))

```
Active Streets (3psu-pn9h)
    ↓ (provides CNN + centerline geometry)
Blockface Geometries (pep9-66vw)
    ↓ (creates blockfaces with side determination)
Blockfaces Collection
    ↓ (enrichment attempts)
Street Cleaning ✓ (partially working)
Parking Regulations ✗ (NOT JOINED)
Meters ✓ (working via CNN)
```

### 2. Side Determination Function

**Function**: [`get_side_of_street()`](backend/ingest_data.py:29-74)

**How it works**:
1. Takes centerline geometry and blockface geometry
2. Finds blockface midpoint
3. Projects midpoint onto centerline
4. Calculates tangent vector along centerline
5. Uses cross-product to determine if blockface is Left (L) or Right (R)

**Issues**:
- Returns `None` on any error (line 74)
- No logging when determination fails
- No fallback mechanism
- If this fails, blockfaces have `side = None`, breaking rule matching

### 3. Current Join Implementations

#### ✓ Street Cleaning (PARTIALLY WORKING)
**Location**: Lines 218-257 in [`ingest_data.py`](backend/ingest_data.py:218-257)

```python
for _, row in sweeping_df.iterrows():
    cnn = row.get("cnn")
    related_blockfaces = cnn_to_blockfaces_index.get(cnn, [])
    rule_side = row.get("cnnrightleft")  # 'L' or 'R'
    
    for bf in related_blockfaces:
        bf_side = bf.get("side")
        
        # CRITICAL: If both sides known, they MUST match
        if rule_side and bf_side:
            if rule_side != bf_side:
                continue  # Skip wrong side
        
        # Rule gets attached
        bf["rules"].append(rule)
```

**Problem**: If `bf_side` is `None` (side determination failed), rules still get skipped even though they might be valid.

#### ✗ Parking Regulations (NOT WORKING)
**Location**: Lines 259-280 in [`ingest_data.py`](backend/ingest_data.py:259-280)

```python
regulations_df = fetch_data_as_dataframe(PARKING_REGULATIONS_ID, ...)
if not regulations_df.empty:
    await db.parking_regulations.delete_many({})
    reg_records = regulations_df.to_dict('records')
    
    # ⚠️ ONLY STORES TO SEPARATE COLLECTION
    await db.parking_regulations.insert_many(reg_records)
    
    # Creates spatial index for "runtime joining" that never happens
    await db.parking_regulations.create_index([("geometry", "2dsphere")])
    
    print(f"Saved {len(reg_records)} parking regulations (to be spatially joined at runtime).")
```

**Critical Issues**:
1. Regulations are stored in a separate `parking_regulations` collection
2. They are NEVER joined to blockfaces during ingestion
3. Comment suggests "spatial join at runtime" but no runtime join code exists
4. The PRD states they should be "spatially joined and geometrically analyzed" but this never happens

#### ✓ Meters (WORKING)
**Location**: Lines 313-337 in [`ingest_data.py`](backend/ingest_data.py:313-337)

Works correctly because:
- Meters have explicit `street_seg_ctrln_id` field that maps to CNN
- Direct CNN-based join works without needing side determination
- All meters on a CNN get added to all related blockfaces

---

## What The PRD Says vs What Code Does

### PRD Requirements (from [`refined-prd.md`](refined-prd.md:39))

> "Non-metered regulations (RPP, Time Limits) are sourced from dataset `hi6h-neyh`. These records use spatially offset geometries (lines drawn on the side of the street) rather than explicit side codes. **The system uses geometric analysis (cross-product calculation relative to the street centerline) to accurately assign these regulations to the correct left or right blockface.**"

### What Code Actually Does

**Reality**: Parking regulations are:
1. ✗ NOT geometrically analyzed
2. ✗ NOT assigned to blockfaces  
3. ✗ NOT using cross-product calculation
4. ✓ ONLY stored in separate collection with spatial index

---

## Required Changes

### Change 1: Implement Geometric Side Determination for Parking Regulations

**Add to [`ingest_data.py`](backend/ingest_data.py) after line 280:**

```python
# Enrich Blockfaces with Parking Regulations via Geometric Analysis
count = 0
for _, row in regulations_df.iterrows():
    reg_geo = row.get("shape") or row.get("geometry")
    if not reg_geo:
        continue
    
    # Method A: Try CNN-based matching first
    cnn = row.get("cnn_id") or row.get("cnn")
    if cnn and cnn in cnn_to_blockfaces_index:
        centerline_geo = streets_metadata.get(cnn, {}).get("centerlineGeometry")
        
        if centerline_geo:
            # Determine which side this regulation applies to
            reg_side = get_side_of_street(centerline_geo, reg_geo)
            
            for bf in cnn_to_blockfaces_index[cnn]:
                bf_side = bf.get("side")
                
                # Match sides if both are known
                if reg_side and bf_side and reg_side != bf_side:
                    continue
                
                # Attach regulation
                bf["rules"].append({
                    "type": "parking-regulation",
                    "timeLimit": row.get("time_limit"),
                    "permitArea": row.get("rpp_area"),
                    "description": row.get("street_parking_description"),
                    "side": reg_side
                })
                count += 1
    
    # Method B: Spatial join for regulations without CNN
    else:
        # For regulations without CNN, do spatial intersection
        # Find all blockfaces whose geometry intersects with regulation geometry
        # Then use geometric analysis to determine side
        pass  # Implement if needed

print(f"Added {count} parking regulations to blockfaces.")
```

### Change 2: Improve Side Determination Robustness

**Modify [`get_side_of_street()`](backend/ingest_data.py:29-74):**

```python
def get_side_of_street(centerline_geo: Dict, blockface_geo: Dict, debug_info: str = "") -> str:
    """
    Determines if the blockface geometry is on the Left or Right side of the centerline.
    Returns 'L', 'R', or None if indeterminate.
    """
    try:
        cl_shape = shape(centerline_geo)
        bf_shape = shape(blockface_geo)
        
        if not isinstance(cl_shape, LineString) or not isinstance(bf_shape, LineString):
            print(f"⚠️ Side determination failed ({debug_info}): Invalid geometry types")
            return None
            
        # Get midpoint of blockface
        bf_mid = bf_shape.interpolate(0.5, normalized=True)
        
        # Project midpoint onto centerline
        projected_dist = cl_shape.project(bf_mid)
        projected_point = cl_shape.interpolate(projected_dist)
        
        # Get tangent vector
        delta = 0.001
        if projected_dist + delta > cl_shape.length:
             p1 = cl_shape.interpolate(projected_dist - delta)
             p2 = projected_point
        else:
             p1 = projected_point
             p2 = cl_shape.interpolate(projected_dist + delta)
             
        cl_vec = (p2.x - p1.x, p2.y - p1.y)
        to_bf_vec = (bf_mid.x - projected_point.x, bf_mid.y - projected_point.y)
        
        # Cross product
        cross_product = cl_vec[0] * to_bf_vec[1] - cl_vec[1] * to_bf_vec[0]
        
        result = 'L' if cross_product > 0 else 'R'
        return result
        
    except Exception as e:
        print(f"⚠️ Side determination failed ({debug_info}): {e}")
        return None
```

### Change 3: Add Validation and Reporting

**Add new validation script `backend/validate_side_assignments.py`:**

```python
import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio

async def validate_sides():
    """Validate that blockfaces have proper side assignments and rules."""
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.curby
    
    # Count blockfaces by side
    total = await db.blockfaces.count_documents({})
    with_side = await db.blockfaces.count_documents({"side": {"$ne": None}})
    without_side = total - with_side
    
    print(f"\n=== Side Assignment Stats ===")
    print(f"Total Blockfaces: {total}")
    print(f"With Side (L/R): {with_side} ({with_side/total*100:.1f}%)")
    print(f"Without Side: {without_side} ({without_side/total*100:.1f}%)")
    
    # Count rules by type
    pipeline = [
        {"$unwind": "$rules"},
        {"$group": {
            "_id": "$rules.type",
            "count": {"$sum": 1}
        }}
    ]
    rule_counts = await db.blockfaces.aggregate(pipeline).to_list(None)
    
    print(f"\n=== Rule Distribution ===")
    for item in rule_counts:
        print(f"{item['_id']}: {item['count']} rules")
    
    # Sample blockfaces without sides but with rules
    problematic = await db.blockfaces.find_one({
        "side": None,
        "rules": {"$ne": []}
    })
    
    if problematic:
        print(f"\n⚠️ WARNING: Found blockfaces without side assignment but with rules")
        print(f"Example: {problematic['id']} on {problematic.get('streetName')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(validate_sides())
```

### Change 4: Update Street Sweeping Logic to Handle Missing Sides

**Modify street cleaning join (lines 243-245):**

```python
# OLD (too strict):
if rule_side and bf_side:
    if rule_side != bf_side:
        continue

# NEW (more permissive):
if rule_side and bf_side:
    # Both known - must match
    if rule_side != bf_side:
        continue
elif rule_side and not bf_side:
    # Rule specifies side but blockface side unknown
    # Attach anyway but log warning
    print(f"⚠️ Attaching {rule_side} rule to blockface without side: {bf['id']}")
elif not rule_side:
    # Rule doesn't specify side - applies to both sides or entire segment
    pass  # Attach to this blockface
```

---

## Priority of Changes

1. **CRITICAL** - Implement Change 1 (parking regulations join)
2. **HIGH** - Implement Change 2 (improve side determination)  
3. **HIGH** - Implement Change 3 (validation script)
4. **MEDIUM** - Implement Change 4 (street sweeping fallback)

---

## Testing Strategy

After implementing changes:

1. Run ingestion: `bash backend/run_ingestion.sh`
2. Run validation: `python backend/validate_side_assignments.py`
3. Check specific blockface: `python backend/debug_bryant.py` (if it exists)
4. Verify in MongoDB:
   ```javascript
   db.blockfaces.findOne({rules: {$elemMatch: {type: "parking-regulation"}}})
   ```

---

## Additional Investigation Needed

1. **Check if parking regulations have CNN field**:
   - Run: `python backend/inspect_non_metered_regs.py`
   - Look for fields: `cnn`, `cnn_id`, `street_id`, etc.

2. **Verify blockface side distribution**:
   - How many blockfaces have `side: "L"` vs `side: "R"` vs `side: null`?
   - Are there CNN segments with only one blockface (should have two)?

3. **Understand regulation geometry structure**:
   - Are regulation geometries parallel to centerlines?
   - What is the typical offset distance?
   - Do they follow street curvature or are they simplified?

---

## Conclusion

The system has the geometric analysis capability ([`get_side_of_street()`](backend/ingest_data.py:29)) but it's not being applied to parking regulations. The PRD promises this functionality but the implementation is incomplete. By applying the same geometric side determination used for street cleaning to parking regulations during ingestion, we can properly assign regulations to the correct blockface (left or right side of the street).