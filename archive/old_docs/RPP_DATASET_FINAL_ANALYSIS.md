# RPP Parcels Dataset: Final Analysis for Street-Level Permit Zones

## Executive Summary

**Question**: Can the Residential Parking Permit Eligibility Parcels dataset map RPP zones onto street-level views to show which permits apply to which streets and their L/R sides?

**Answer**: **NO - This dataset cannot directly serve that purpose.**

However, there IS a solution using your existing data.

---

## What We Discovered

### RPP Parcels Dataset (i886-hxz9) - Actual Fields

Based on API testing, this dataset contains:

```
Available Fields:
- mapblklot          (Parcel ID / APN)
- blklot             (Same as mapblklot)
- block_num          (Block number)
- lot_num            (Lot number)
- rppeligib          (RPP Area Code: Q, J, K, etc.)
- shape              (MultiPolygon geometry - building footprint)
- created_user
- created_date
- last_edited_user
- last_edited_date
```

### Critical Missing Fields

❌ **NO `street` field** - Cannot match by street name
❌ **NO `from_st` / `to_st` fields** - No address ranges
❌ **NO `odd_even` field** - No odd/even designation
❌ **NO `cnn` field** - Cannot link to your street segments

**The context description was incorrect** - those fields do not exist in the actual API response.

---

## Why This Dataset Won't Work for Your Use Case

### 1. Wrong Granularity
- **Parcels** = Individual building footprints
- **Your Need** = Street segment sides (L/R)
- One street segment can have dozens of parcels
- One parcel can front multiple streets

### 2. No Direct Street Connection
- Parcels are identified by APN (Assessor Parcel Number)
- No way to match "Parcel 1222047" to "20th Street, Left Side"
- Would require complex spatial joins

### 3. Geometry Mismatch
- Parcel geometries are **polygons** (building footprints)
- Your blockfaces are **lines** (street edges)
- Different geometric primitives

---

## THE SOLUTION: You Already Have RPP Data!

### Your Parking Regulations Dataset ALREADY Contains RPP Information

Looking at your [`ingest_data.py`](backend/ingest_data.py:262), you're already ingesting the Parking Regulations dataset (`hi6h-neyh`) which includes:

```python
{
    "cnn": "1046000",              # ✅ Links to your street segments
    "streetname": "20TH ST",       # ✅ Street name
    "rpparea1": "Q",               # ✅ RPP Area Code!
    "rpparea2": "J",               # ✅ Secondary RPP Area
    "regulation": "...",
    "side": "R",                   # ✅ L/R side information
    "geometry": {...}              # ✅ Line geometry
}
```

### This Is Already Being Processed

In your [`ingest_data.py:344-356`](backend/ingest_data.py:344), you're already attaching these regulations to blockfaces:

```python
bf["rules"].append({
    "type": "parking-regulation",
    "regulation": row.get("regulation"),
    "timeLimit": row.get("hrlimit"),
    "permitArea": row.get("rpparea1") or row.get("rpparea2"),  # ← RPP AREA!
    "days": row.get("days"),
    "hours": row.get("hours"),
    "fromTime": row.get("from_time"),
    "toTime": row.get("to_time"),
    "details": row.get("regdetails"),
    "exceptions": row.get("exceptions"),
    "side": reg_side
})
```

---

## What You Need to Do

### Option 1: Extract RPP Zones from Existing Regulations (RECOMMENDED)

Your parking regulations already have RPP area codes. You just need to:

1. **Query regulations with RPP areas**:
```python
# In your ingestion or as a post-processing step
rpp_regulations = await db.parking_regulations.find({
    "$or": [
        {"rpparea1": {"$exists": True, "$ne": None}},
        {"rpparea2": {"$exists": True, "$ne": None}}
    ]
}).to_list(length=None)
```

2. **Create RPP zone overlays**:
```python
# Group by CNN + Side + RPP Area
rpp_zones = {}
for reg in rpp_regulations:
    cnn = reg.get("cnn")
    side = reg.get("side")  # or determine from geometry
    rpp_area = reg.get("rpparea1") or reg.get("rpparea2")
    
    key = f"{cnn}_{side}"
    if key not in rpp_zones:
        rpp_zones[key] = {
            "cnn": cnn,
            "side": side,
            "rpp_areas": set(),
            "geometry": reg.get("geometry")
        }
    rpp_zones[key]["rpp_areas"].add(rpp_area)
```

3. **Add to your street segments**:
```python
# During ingestion, add RPP zone info to each segment
for segment in street_segments:
    cnn = segment["cnn"]
    side = segment["side"]
    key = f"{cnn}_{side}"
    
    if key in rpp_zones:
        segment["rpp_zone"] = list(rpp_zones[key]["rpp_areas"])
```

### Option 2: Create Dedicated RPP Zone Layer

If you want a separate RPP zone visualization:

```python
# backend/create_rpp_zones.py
async def create_rpp_zone_layer():
    """
    Extract RPP zones from parking regulations and create
    a dedicated collection for map overlay
    """
    
    # Query all regulations with RPP areas
    regulations = await db.parking_regulations.find({
        "$or": [
            {"rpparea1": {"$exists": True}},
            {"rpparea2": {"$exists": True}}
        ]
    }).to_list(length=None)
    
    # Group by RPP area
    zones_by_area = {}
    for reg in regulations:
        for area_field in ["rpparea1", "rpparea2"]:
            area = reg.get(area_field)
            if area:
                if area not in zones_by_area:
                    zones_by_area[area] = []
                zones_by_area[area].append({
                    "cnn": reg.get("cnn"),
                    "street": reg.get("streetname"),
                    "geometry": reg.get("geometry"),
                    "side": determine_side(reg)
                })
    
    # Save as RPP zones collection
    rpp_zones = []
    for area, segments in zones_by_area.items():
        rpp_zones.append({
            "rpp_area": area,
            "segments": segments,
            "segment_count": len(segments)
        })
    
    await db.rpp_zones.delete_many({})
    await db.rpp_zones.insert_many(rpp_zones)
```

---

## Comparison: What You Have vs What You Thought You Needed

| Aspect | RPP Parcels (i886-hxz9) | Parking Regulations (hi6h-neyh) |
|--------|-------------------------|----------------------------------|
| **RPP Area Code** | ✅ rppeligib | ✅ rpparea1, rpparea2 |
| **Street Name** | ❌ None | ✅ streetname |
| **CNN Reference** | ❌ None | ✅ cnn |
| **Side (L/R)** | ❌ None | ✅ Can be determined |
| **Geometry Type** | Polygon (building) | LineString (street) |
| **Links to Your Data** | ❌ No | ✅ Yes (via CNN) |
| **Already Ingested** | ❌ No | ✅ Yes! |

---

## Implementation Plan

### Step 1: Verify RPP Data in Your Database

```bash
cd backend && python3 << 'EOF'
import asyncio
import motor.motor_asyncio
import os
from dotenv import load_dotenv

async def check_rpp_data():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.curby
    
    # Count regulations with RPP areas
    count = await db.parking_regulations.count_documents({
        "$or": [
            {"rpparea1": {"$exists": True, "$ne": None}},
            {"rpparea2": {"$exists": True, "$ne": None}}
        ]
    })
    
    print(f"Found {count} parking regulations with RPP area codes")
    
    # Sample
    sample = await db.parking_regulations.find_one({
        "rpparea1": {"$exists": True}
    })
    
    if sample:
        print(f"\nSample regulation:")
        print(f"  CNN: {sample.get('cnn')}")
        print(f"  Street: {sample.get('streetname')}")
        print(f"  RPP Area 1: {sample.get('rpparea1')}")
        print(f"  RPP Area 2: {sample.get('rpparea2')}")
    
    client.close()

asyncio.run(check_rpp_data())
EOF
```

### Step 2: Add RPP Zone to Street Segments Model

Update [`models.py`](backend/models.py:26):

```python
class StreetSegment(BaseModel):
    cnn: str
    side: str
    streetName: str
    fromStreet: Optional[str] = None
    toStreet: Optional[str] = None
    
    # Geometries
    centerlineGeometry: Dict
    blockfaceGeometry: Optional[Dict] = None
    
    # Rules and schedules
    rules: List[Dict] = []
    schedules: List[Schedule] = []
    
    # NEW: RPP Zone information
    rpp_zones: List[str] = []  # e.g., ["Q", "J"]
    
    # Metadata
    zip_code: Optional[str] = None
    layer: Optional[str] = None
```

### Step 3: Extract RPP Zones During Ingestion

Add to [`ingest_data.py`](backend/ingest_data.py) after regulations are processed:

```python
# After line 365, add:
print("\n--- Extracting RPP Zones for Street Segments ---")
for bf in all_blockfaces:
    rpp_zones = set()
    for rule in bf.get("rules", []):
        if rule.get("type") == "parking-regulation":
            permit_area = rule.get("permitArea")
            if permit_area:
                rpp_zones.add(permit_area)
    
    if rpp_zones:
        bf["rpp_zones"] = list(rpp_zones)
        
print(f"Added RPP zone information to blockfaces")
```

### Step 4: Update Frontend to Display RPP Zones

In your [`MapView.tsx`](frontend/src/components/MapView.tsx) or [`BlockfaceDetail.tsx`](frontend/src/components/BlockfaceDetail.tsx):

```typescript
// Display RPP zones for each blockface
{blockface.rpp_zones && blockface.rpp_zones.length > 0 && (
  <div className="rpp-zones">
    <h4>Residential Parking Permit Zones:</h4>
    {blockface.rpp_zones.map(zone => (
      <Badge key={zone} variant="secondary">
        Area {zone}
      </Badge>
    ))}
  </div>
)}
```

---

## Conclusion

### The RPP Parcels Dataset is NOT the Solution

- ❌ No street/address fields
- ❌ No CNN references
- ❌ Wrong granularity (buildings vs streets)
- ❌ Cannot map to L/R sides

### You Already Have the Solution!

✅ **Parking Regulations dataset** contains:
- RPP area codes (`rpparea1`, `rpparea2`)
- CNN references (links to your streets)
- Side information (can be determined)
- Already being ingested

✅ **You just need to**:
1. Extract RPP zones from existing regulations
2. Add `rpp_zones` field to your street segments
3. Display on map as color-coded overlays

### Next Steps

1. Run the verification script (Step 1 above)
2. Confirm you have RPP data in your regulations
3. Implement the extraction logic (Step 3)
4. Update your models and frontend

**You don't need the RPP Parcels dataset at all** - you already have everything you need in your existing parking regulations data!