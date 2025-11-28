# Street Intersection Datasets - Final Summary

## Executive Summary

San Francisco provides two complementary datasets for robust intersection handling:

1. **Street Intersections** (pu5n-qu5c): Address ranges for CNN L and CNN R
2. **Intersection Permutations** (jfxm-zeee): All string permutations of intersection names with lat/long

---

## Critical Understanding: Intersection Permutations

### The Same Intersection, Multiple String Representations

**Key Insight**: "20th & Bryant" and "Bryant & 20th" are the **SAME intersection** with the **SAME CNNs**.

The permutations dataset provides **minimum 2 string variations** per intersection:

```javascript
// Permutation 1
{
  streets: "20TH ST & BRYANT ST",
  cnn: ["10048000", "10049000"],  // CNNs for BOTH streets
  lat: 37.xxxx,
  lng: -122.xxxx
}

// Permutation 2 (SAME intersection, different string)
{
  streets: "BRYANT ST & 20TH ST",
  cnn: ["10048000", "10049000"],  // SAME CNNs
  lat: 37.xxxx,                   // SAME coordinates
  lng: -122.xxxx
}
```

### Why This Matters

Users can input intersection in ANY order:
- "20th & Bryant" → finds permutation 1
- "Bryant & 20th" → finds permutation 2
- **Both return the SAME CNNs and location**

---

## Complete Data Architecture

### Dataset 1: Intersection Permutations (jfxm-zeee)

**Purpose**: Handle flexible user input with geolocation

**Fields**:
- `streets`: String representation (e.g., "20TH ST & BRYANT ST")
- `cnn`: Array of CNNs for all streets at this intersection
- `lat`, `lng`: Precise intersection point coordinates

**Coverage**: Minimum 2 permutations per intersection (more if 3+ streets)

### Dataset 2: Street Intersections (pu5n-qu5c)

**Purpose**: Provide address ranges for each CNN

**Fields**:
- `cnn`: CNN identifier
- `street`, `from_st`: Street names
- `lf_fadd`, `lf_tadd`: Left side address range (CNN L)
- `rt_fadd`, `rt_tadd`: Right side address range (CNN R)

---

## Integration Flow

```
User Input: "Bryant and 20th"
    ↓
Step 1: Query Intersection Permutations
    Search for: streets containing "BRYANT" and "20TH"
    Find: {streets: "BRYANT ST & 20TH ST", cnn: ["10048000", "10049000"], lat: 37.xxx, lng: -122.xxx}
    ↓
Step 2: Extract CNNs
    CNNs: ["10048000", "10049000"]
    Location: (37.xxx, -122.xxx)
    ↓
Step 3: Get Address Ranges (from pu5n-qu5c)
    CNN 10048000 (20TH ST):
      - L: 900-998
      - R: 901-999
    CNN 10049000 (BRYANT ST):
      - L: 1200-1298
      - R: 1201-1299
    ↓
Step 4: Query Street Segments
    Find segments with cnn IN ["10048000", "10049000"]
    Returns 4 segments:
      - 10048000-L (20TH ST left)
      - 10048000-R (20TH ST right)
      - 10049000-L (BRYANT ST left)
      - 10049000-R (BRYANT ST right)
    ↓
Step 5: Return Complete Data
    - All 4 segments with parking regulations
    - Address ranges for each
    - Intersection coordinates for mapping
```

---

## Key Benefits

### 1. Order-Independent Search
- "20th & Bryant" = "Bryant & 20th"
- Same CNNs, same results

### 2. Precise Geolocation
- Intersection lat/long for high-fidelity spatial joins
- Improves CNN-to-parking regulation overlay accuracy

### 3. Complete Address Context
- Know exact address ranges for each side
- Can determine which corner user is asking about

### 4. Comprehensive Coverage
- All streets at intersection (typically 2, sometimes 3+)
- Both sides (L and R) of each street

---

## Implementation Summary

### Data Model

```javascript
// Collection: intersection_permutations
{
  _id: ObjectId,
  streets: "20TH ST & BRYANT ST",
  cnns: ["10048000", "10049000"],  // All CNNs at this intersection
  location: {
    type: "Point",
    coordinates: [-122.xxx, 37.xxx]  // Intersection point
  },
  normalized: "20TH_BRYANT"  // For fast lookup
}

// Collection: intersections (address ranges)
{
  _id: ObjectId,
  cnn: "10048000",
  street: "20TH ST",
  fromStreet: "BRYANT ST",
  lfFromAddress: 900,   // CNN L start
  lfToAddress: 998,     // CNN L end
  rtFromAddress: 901,   // CNN R start
  rtToAddress: 999      // CNN R end
}

// Collection: street_segments (enhanced)
{
  _id: ObjectId,
  cnn: "10048000",
  side: "L",
  streetName: "20TH ST",
  addressRange: {
    fromAddress: 900,
    toAddress: 998
  },
  fromIntersection: "BRYANT ST",
  toIntersection: "FLORIDA ST",
  centerlineGeometry: {...},
  rules: [...],
  schedules: [...]
}
```

### API Endpoint

```python
@app.get("/api/v1/intersections/search")
async def search_intersection(query: str):
    """
    Search for intersection using flexible input
    Returns all segments at that intersection
    """
    # Find permutation (any string variation works)
    permutation = await db.intersection_permutations.find_one({
        "$text": {"$search": query}
    })
    
    if not permutation:
        raise HTTPException(status_code=404, detail="Intersection not found")
    
    # Get CNNs (all streets at this intersection)
    cnns = permutation["cnns"]
    location = permutation["location"]
    
    # Get address ranges for each CNN
    intersections = await db.intersections.find({
        "cnn": {"$in": cnns}
    }).to_list(length=100)
    
    # Get all segments (both L and R for each CNN)
    segments = await db.street_segments.find({
        "cnn": {"$in": cnns}
    }).to_list(length=100)
    
    # Enhance with address ranges
    for segment in segments:
        intersection = next((i for i in intersections if i["cnn"] == segment["cnn"]), None)
        if intersection:
            if segment["side"] == "L":
                segment["addressRange"] = {
                    "fromAddress": intersection["lfFromAddress"],
                    "toAddress": intersection["lfToAddress"]
                }
            else:
                segment["addressRange"] = {
                    "fromAddress": intersection["rtFromAddress"],
                    "toAddress": intersection["rtToAddress"]
                }
    
    return {
        "query": query,
        "location": location,  # Intersection coordinates
        "cnns": cnns,
        "segments": segments
    }
```

---

## Spatial Join Enhancement

### Using Intersection Coordinates

The lat/long from intersection permutations provides:

1. **Precise Intersection Points**: Exact location where streets meet
2. **Better Spatial Joins**: More accurate CNN-to-parking regulation overlay
3. **Improved Geometry**: Can validate and enhance blockface geometries
4. **Network Topology**: Understand street connectivity

### Example Use Case

```python
# Use intersection coordinates for spatial validation
intersection_point = {
    "type": "Point",
    "coordinates": [lng, lat]  # From permutations dataset
}

# Find nearby parking regulations
nearby_regs = await db.parking_regulations.find({
    "geometry": {
        "$near": {
            "$geometry": intersection_point,
            "$maxDistance": 50  # meters
        }
    }
}).to_list(length=100)

# Validate they match the CNNs at this intersection
for reg in nearby_regs:
    if reg["cnn"] in intersection_cnns:
        # High confidence match
        pass
```

---

## Final Implementation Checklist

- [ ] Ingest intersection permutations with lat/long
- [ ] Ingest street intersections with address ranges
- [ ] Create 2dsphere index on intersection locations
- [ ] Enhance street_segments with address ranges
- [ ] Implement flexible intersection search API
- [ ] Use intersection coordinates for spatial joins
- [ ] Test with various input formats
- [ ] Validate address range accuracy

---

**Status**: Architecture Complete - Ready for Implementation  
**Last Updated**: November 28, 2024