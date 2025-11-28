# Residential Parking Permit Eligibility Parcels Dataset Analysis

## Executive Summary

**Can this dataset serve as the missing link between streets, blockfaces, and L/R side information?**

**Answer: NO - But it serves a DIFFERENT, complementary purpose.**

This dataset is **NOT** a replacement for your current street-level data architecture. Instead, it provides **building-level validation** that operates at a different granularity than your street segments.

---

## Dataset Structure

### API Details
- **Endpoint**: `https://data.sfgov.org/resource/i886-hxz9.json`
- **Dataset ID**: `i886-hxz9`
- **Documentation**: https://dev.socrata.com/foundry/data.sfgov.org/i886-hxz9

### Available Fields
```json
{
  "mapblklot": "1292030",        // Assessor Parcel Number (APN) - Primary Key
  "blklot": "1292030",           // Same as mapblklot
  "block_num": "1292",           // Block number
  "lot_num": "031",              // Lot number
  "rppeligib": "J",              // RPP Area Code (THE KEY FIELD)
  "created_user": "...",
  "created_date": "...",
  "last_edited_user": "...",
  "last_edited_date": "...",
  "shape": {                     // MultiPolygon geometry
    "type": "MultiPolygon",
    "coordinates": [...]
  }
}
```

### Key Characteristics
1. **Granularity**: PARCEL-level (individual building footprints)
2. **Geometry**: MultiPolygon representing exact building boundaries
3. **Coverage**: City-wide, all parcels with RPP eligibility
4. **Primary Value**: `rppeligib` field contains the RPP Area Code (Q, J, K, etc.)

---

## Critical Gap Analysis

### What This Dataset LACKS

❌ **No CNN (Centerline Network) Reference**
- Cannot directly link to your street segments
- No `cnn` or `street_seg_ctrln_id` field

❌ **No Street Name Field**
- Cannot match by street name
- Would require reverse geocoding

❌ **No Address Range Information**
- The context mentioned `from_st` / `to_st` fields, but these **DO NOT EXIST** in the actual API
- No `odd_even` field either

❌ **No Side-of-Street Information**
- Parcels don't have L/R designation
- Buildings can span multiple street frontages

### What Your Current Architecture HAS

✅ **CNN-based Street Segments** (from Active Streets)
- Direct link to all other datasets
- Centerline geometries

✅ **Blockface Geometries** (from pep9-66vw)
- Side-specific (L/R) geometries
- Already linked to CNN

✅ **Side Determination Logic**
- Your [`get_side_of_street()`](backend/ingest_data.py:29) function
- Cross-product calculation for L/R assignment

✅ **Parking Regulations** (from hi6h-neyh)
- Already spatially joined to blockfaces
- Side-aware rules

---

## Where This Dataset DOES Add Value

### 1. Address-Level Validation Feature

**Use Case**: "Check My Address" functionality

```python
# User enters: "123 Valencia St"
# Your app can:
1. Geocode address → lat/lng
2. Query RPP Parcels dataset → Find parcel at that location
3. Return: "Your building is in RPP Area J"
4. Cross-reference with parking regulations on that street
```

**Implementation**:
```python
async def check_address_rpp_eligibility(address: str):
    # Geocode address
    lat, lng = geocode(address)
    
    # Query parcels dataset with point-in-polygon
    parcel = await query_rpp_parcels_at_point(lat, lng)
    
    if parcel:
        return {
            "eligible": True,
            "rpp_area": parcel["rppeligib"],
            "parcel_id": parcel["mapblklot"]
        }
    return {"eligible": False}
```

### 2. Visual Context Layer

**Use Case**: Show building footprints on map

- Overlay parcel polygons on your map
- Color-code by RPP area
- Help users understand zone boundaries at building level

### 3. Resident Verification

**Use Case**: Validate permit applications

- User claims to live at address X
- Check if that parcel is in the claimed RPP area
- Prevent fraudulent permit requests

---

## Integration Strategy

### Option A: Supplementary Validation Layer (RECOMMENDED)

**Keep your current architecture**, add parcels as a separate collection:

```python
# Current flow (unchanged):
1. User searches location
2. Query street_segments by geo proximity
3. Return blockfaces with parking rules

# New validation flow (optional):
4. User clicks "Check My Building"
5. Query rpp_parcels by point-in-polygon
6. Show building-specific RPP eligibility
```

**Database Structure**:
```
Collections:
- street_segments (primary - unchanged)
- parking_regulations (unchanged)
- rpp_parcels (NEW - for validation only)
```

### Option B: Spatial Join to Blockfaces (NOT RECOMMENDED)

**Why NOT recommended**:
- Parcels and blockfaces operate at different granularities
- One blockface can have multiple parcels
- One parcel can front multiple blockfaces
- Complex many-to-many relationship
- Your current CNN-based joins are more reliable

---

## Comparison: Your Current Data vs RPP Parcels

| Aspect | Your Current Architecture | RPP Parcels Dataset |
|--------|---------------------------|---------------------|
| **Primary Key** | CNN + Side | Parcel APN (mapblklot) |
| **Geometry** | Street centerlines & blockfaces | Building footprints |
| **Granularity** | Street segment (one side) | Individual building |
| **Link to Regulations** | ✅ Direct via CNN | ❌ None |
| **Side Information** | ✅ L/R explicit | ❌ Not applicable |
| **Address Validation** | ❌ Indirect | ✅ Direct |
| **Coverage** | Street-level complete | Building-level complete |

---

## Recommended Implementation

### Phase 1: Add as Validation Layer

```python
# backend/models.py
class RPPParcel(BaseModel):
    mapblklot: str
    rpp_area: str  # rppeligib field
    geometry: Dict  # MultiPolygon
    block_num: str
    lot_num: str

# backend/main.py
@app.get("/api/v1/check-address-rpp")
async def check_address_rpp(lat: float, lng: float):
    """Check RPP eligibility for a specific address/building"""
    point = {"type": "Point", "coordinates": [lng, lat]}
    
    parcel = await db.rpp_parcels.find_one({
        "geometry": {
            "$geoIntersects": {
                "$geometry": point
            }
        }
    })
    
    if parcel:
        return {
            "eligible": True,
            "rpp_area": parcel["rpp_area"],
            "parcel_id": parcel["mapblklot"]
        }
    return {"eligible": False}
```

### Phase 2: Ingest Script

```python
# backend/ingest_rpp_parcels.py
async def ingest_rpp_parcels():
    """Ingest RPP Parcels as supplementary data"""
    
    # Fetch from Socrata
    parcels_df = fetch_data_as_dataframe("i886-hxz9", app_token)
    
    # Transform
    parcels = []
    for _, row in parcels_df.iterrows():
        parcels.append({
            "mapblklot": row.get("mapblklot"),
            "rpp_area": row.get("rppeligib"),
            "geometry": row.get("shape"),
            "block_num": row.get("block_num"),
            "lot_num": row.get("lot_num")
        })
    
    # Save to MongoDB
    await db.rpp_parcels.delete_many({})
    await db.rpp_parcels.insert_many(parcels)
    
    # Create geospatial index
    await db.rpp_parcels.create_index([("geometry", "2dsphere")])
```

---

## Conclusion

### The Missing Link Question

**Is this the missing link between streets, blockfaces, and L/R sides?**

**NO.** This dataset:
- ❌ Does NOT connect to CNN (your backbone)
- ❌ Does NOT have street names or address ranges
- ❌ Does NOT provide L/R side information
- ❌ Does NOT replace or improve your current street-level architecture

### What It Actually Provides

**Building-Level Validation** - A complementary layer that:
- ✅ Validates specific addresses/buildings
- ✅ Shows exact building footprints
- ✅ Provides definitive RPP area codes at parcel level
- ✅ Enables "Check My Address" features

### Your Current Architecture is Sound

Your existing approach using:
1. **Active Streets (CNN)** as the backbone
2. **Blockface Geometries (pep9)** for side-specific shapes
3. **Geometric side determination** for L/R assignment
4. **Spatial joins** for regulations

...is the **correct architecture** for street-level parking data.

### Recommendation

**Add RPP Parcels as a supplementary validation layer**, but do NOT attempt to use it as a replacement for your CNN-based street segment architecture. They serve different purposes at different granularities.

---

## Sample Query Examples

### Find all parcels in RPP Area Q
```
https://data.sfgov.org/resource/i886-hxz9.json?rppeligib=Q&$limit=100
```

### Find parcel by APN
```
https://data.sfgov.org/resource/i886-hxz9.json?mapblklot=1292030
```

### Spatial query (point in polygon)
```
https://data.sfgov.org/resource/i886-hxz9.json?
  $where=within_polygon(shape, 'POINT(-122.447395 37.761622)')