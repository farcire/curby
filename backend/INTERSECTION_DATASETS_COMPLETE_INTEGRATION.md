# Complete Intersection Datasets Integration Plan

## Executive Summary

San Francisco provides **two complementary datasets** for handling street intersection queries:

1. **Street Intersections** (pu5n-qu5c): Provides address ranges and CNN mapping
2. **Intersection Permutations** (jfxm-zeee): Provides CNN for EACH street at every intersection permutation

Together, these enable robust handling of user queries like "20th & Bryant", "Bryant and 20th", "20th/Bryant", etc.

---

## Dataset 1: Street Intersections (pu5n-qu5c)

**Purpose**: Primary intersection data with address ranges

**API**: `https://data.sfgov.org/resource/pu5n-qu5c.json`  
**Docs**: https://dev.socrata.com/foundry/data.sfgov.org/pu5n-qu5c

### Key Fields

| Field | Description | Purpose |
|-------|-------------|---------|
| `cnn` | CNN segment identifier | Links to street segments |
| `street` | Main street name | Primary street |
| `from_st` | Intersecting street | Cross street |
| `lf_fadd` | Left from address | CNN L start address |
| `lf_tadd` | Left to address | CNN L end address |
| `rt_fadd` | Right from address | CNN R start address |
| `rt_tadd` | Right to address | CNN R end address |

---

## Dataset 2: Intersection Permutations (jfxm-zeee)

**Purpose**: Provides CNN for EACH street at every intersection permutation

**API**: `https://data.sfgov.org/resource/jfxm-zeee.json`  
**Docs**: https://dev.socrata.com/foundry/data.sfgov.org/jfxm-zeee

### Critical Understanding

**Each intersection has MINIMUM 2 entries** (one per street):

```
Intersection: "20th & Bryant"

Entry 1:
  streets: "20TH ST & BRYANT ST"
  cnn: "10048000"  ← CNN for 20TH ST segment

Entry 2:
  streets: "20TH ST & BRYANT ST"  
  cnn: "10049000"  ← CNN for BRYANT ST segment

(Same permutation string, different CNNs)
```

### Why This Matters

When user searches "20th & Bryant", we get:
- CNN for the 20th St segment at that intersection
- CNN for the Bryant St segment at that intersection
- Can show parking on BOTH streets at that corner

---

## Data Model

### Intersection Permutation Record

```javascript
{
  _id: ObjectId,
  streets: "20TH ST & BRYANT ST",    // Permutation string
  cnn: "10048000",                   // CNN for ONE street at this intersection
  normalized: "20TH_BRYANT",         // For fast lookup
}
```

**Key Insight**: Multiple records with same `streets` value but different `cnn` values.

### Example: "20th & Bryant" Intersection

```javascript
// Record 1 - 20th St segment
{
  streets: "20TH ST & BRYANT ST",
  cnn: "10048000",  // 20TH ST
  normalized: "20TH_BRYANT"
}

// Record 2 - Bryant St segment  
{
  streets: "20TH ST & BRYANT ST",
  cnn: "10049000",  // BRYANT ST
  normalized: "20TH_BRYANT"
}

// Record 3 - Alternative permutation
{
  streets: "BRYANT ST & 20TH ST",
  cnn: "10048000",  // 20TH ST
  normalized: "20TH_BRYANT"
}

// Record 4 - Alternative permutation
{
  streets: "BRYANT ST & 20TH ST",
  cnn: "10049000",  // BRYANT ST
  normalized: "20TH_BRYANT"
}
```

---

## Integration Architecture

### Data Flow for Intersection Query

```
User Input: "Bryant and 20th"
    ↓
Step 1: Normalize Query
    "Bryant and 20th" → "20TH_BRYANT"
    ↓
Step 2: Query Intersection Permutations (jfxm-zeee)
    Find ALL records with normalized = "20TH_BRYANT"
    Extract ALL unique CNNs:
      - "10048000" (20TH ST segment)
      - "10049000" (BRYANT ST segment)
    ↓
Step 3: Query Street Intersections (pu5n-qu5c)
    For each CNN, get address ranges:
      - CNN 10048000: lf_fadd=900, lf_tadd=998, rt_fadd=901, rt_tadd=999
      - CNN 10049000: lf_fadd=1200, lf_tadd=1298, rt_fadd=1201, rt_tadd=1299
    ↓
Step 4: Query Street Segments (street_segments collection)
    Find segments for ALL CNNs (both L and R sides):
      - 10048000-L (20TH ST, left side, addresses 900-998)
      - 10048000-R (20TH ST, right side, addresses 901-999)
      - 10049000-L (BRYANT ST, left side, addresses 1200-1298)
      - 10049000-R (BRYANT ST, right side, addresses 1201-1299)
    ↓
Step 5: Return to User
    ALL segments at that intersection:
      - Both sides of 20th St
      - Both sides of Bryant St
      - Complete parking regulations for all 4 segments
      - Address ranges for context
```

---

## API Implementation

### Endpoint: Flexible Intersection Search

```python
@app.get("/api/v1/intersections/search")
async def search_intersection(query: str):
    """
    Search for intersection using flexible input
    
    Examples:
      /api/v1/intersections/search?query=20th%20and%20Bryant
      /api/v1/intersections/search?query=Bryant%20%26%2020th
    
    Returns segments for ALL streets at that intersection (both sides each)
    """
    # Step 1: Normalize query
    normalized = normalize_intersection_query(query)
    # e.g., "20th and Bryant" → "20TH_BRYANT"
    
    # Step 2: Find ALL permutation records with this normalized key
    # IMPORTANT: There will be multiple records (one per street)
    permutations = await db.intersection_permutations.find({
        "normalized": normalized
    }).to_list(length=100)
    
    if not permutations:
        # Try fuzzy matching
        permutations = await find_permutations_fuzzy(query)
    
    if not permutations:
        raise HTTPException(status_code=404, detail="Intersection not found")
    
    # Step 3: Extract ALL unique CNNs (one per street at intersection)
    cnns = list(set([p["cnn"] for p in permutations]))
    # e.g., ["10048000", "10049000"]
    
    # Step 4: Get intersection details with address ranges for each CNN
    intersections = await db.intersections.find({
        "cnn": {"$in": cnns}
    }).to_list(length=100)
    
    # Step 5: Get ALL street segments (both L and R for each CNN)
    segments = await db.street_segments.find({
        "cnn": {"$in": cnns}
    }).to_list(length=100)
    
    # Step 6: Enhance segments with address ranges
    for segment in segments:
        cnn = segment["cnn"]
        side = segment["side"]
        
        # Find matching intersection data
        intersection = next((i for i in intersections if i["cnn"] == cnn), None)
        
        if intersection:
            if side == "L":
                segment["addressRange"] = {
                    "fromAddress": intersection.get("lfFromAddress"),
                    "toAddress": intersection.get("lfToAddress")
                }
            else:
                segment["addressRange"] = {
                    "fromAddress": intersection.get("rtFromAddress"),
                    "toAddress": intersection.get("rtToAddress")
                }
            
            segment["fromIntersection"] = intersection.get("fromStreet")
    
    return {
        "query": query,
        "normalized": normalized,
        "cnns": cnns,  # All CNNs at this intersection
        "segments": segments,  # All segments (typically 4: 2 streets × 2 sides)
        "streetCount": len(cnns)  # Number of streets at intersection
    }


def normalize_intersection_query(query: str) -> str:
    """
    Normalize intersection query for consistent matching
    
    Examples:
      "20th and Bryant" → "20TH_BRYANT"
      "Bryant & 20th" → "20TH_BRYANT"  (same result!)
      "20TH ST / BRYANT ST" → "20TH_BRYANT"
    
    Key: Sort alphabetically so order doesn't matter
    """
    # Remove common separators and normalize
    query = query.upper()
    query = re.sub(r'\s+(AND|&|/)\s+', '_', query)
    query = re.sub(r'\s+ST(REET)?\b', '', query)
    query = re.sub(r'\s+AVE(NUE)?\b', '', query)
    query = re.sub(r'\s+BLVD\b', '', query)
    query = re.sub(r'\s+', '_', query)
    
    # Sort alphabetically for consistent ordering
    # This ensures "20TH_BRYANT" == "BRYANT_20TH"
    parts = query.split('_')
    parts.sort()
    
    return '_'.join(parts)
```

---

## Data Ingestion Strategy

### Phase 1: Ingest Intersection Permutations

```python
async def ingest_intersection_permutations():
    """
    Ingest all permutations from jfxm-zeee dataset
    
    IMPORTANT: Each intersection will have multiple records
    (minimum 2, one per street)
    """
    url = "https://data.sfgov.org/resource/jfxm-zeee.json"
    offset = 0
    limit = 1000
    
    while True:
        params = {"$limit": limit, "$offset": offset}
        response = requests.get(url, params=params)
        data = response.json()
        
        if not data:
            break
        
        for record in data:
            streets = record.get("streets", "")
            cnn = record.get("cnn")
            
            # Create normalized key (order-independent)
            normalized = normalize_intersection_query(streets)
            
            doc = {
                "streets": streets,
                "cnn": cnn,  # Single CNN for one street at this intersection
                "normalized": normalized
            }
            
            # Insert (will have multiple docs with same normalized key)
            await db.intersection_permutations.insert_one(doc)
        
        offset += limit
    
    # Create indexes
    await db.intersection_permutations.create_index([("normalized", 1)])
    await db.intersection_permutations.create_index([("cnn", 1)])
    await db.intersection_permutations.create_index([("streets", "text")])
```

### Phase 2: Ingest Street Intersections

```python
async def ingest_street_intersections():
    """
    Ingest intersection data with address ranges from pu5n-qu5c
    """
    url = "https://data.sfgov.org/resource/pu5n-qu5c.json"
    offset = 0
    limit = 1000
    
    while True:
        params = {"$limit": limit, "$offset": offset}
        response = requests.get(url, params=params)
        data = response.json()
        
        if not data:
            break
        
        for record in data:
            doc = {
                "cnn": record.get("cnn"),
                "street": record.get("street", record.get("streetname")),
                "fromStreet": record.get("from_st"),
                "limits": record.get("limits"),
                
                # Address ranges for CNN L and CNN R
                "lfFromAddress": parse_int(record.get("lf_fadd")),
                "lfToAddress": parse_int(record.get("lf_tadd")),
                "rtFromAddress": parse_int(record.get("rt_fadd")),
                "rtToAddress": parse_int(record.get("rt_tadd")),
            }
            
            await db.intersections.insert_one(doc)
        
        offset += limit
    
    # Create indexes
    await db.intersections.create_index([("cnn", 1)])
    await db.intersections.create_index([("street", 1), ("fromStreet", 1)])
```

---

## Example User Flows

### Flow 1: "20th and Bryant"

```
User Input: "20th and Bryant"
    ↓
Normalized: "20TH_BRYANT"
    ↓
Query Permutations:
  Found 4+ records:
    - {streets: "20TH ST & BRYANT ST", cnn: "10048000"}
    - {streets: "20TH ST & BRYANT ST", cnn: "10049000"}
    - {streets: "BRYANT ST & 20TH ST", cnn: "10048000"}
    - {streets: "BRYANT ST & 20TH ST", cnn: "10049000"}
    ↓
Extract Unique CNNs: ["10048000", "10049000"]
    ↓
Get Address Ranges:
  CNN 10048000 (20TH ST):
    - L: 900-998
    - R: 901-999
  CNN 10049000 (BRYANT ST):
    - L: 1200-1298
    - R: 1201-1299
    ↓
Return 4 Segments:
  1. 20TH ST (L side): 900-998 + parking regs
  2. 20TH ST (R side): 901-999 + parking regs
  3. BRYANT ST (L side): 1200-1298 + parking regs
  4. BRYANT ST (R side): 1201-1299 + parking regs
```

### Flow 2: "Bryant & 20th" (Different Order)

```
User Input: "Bryant & 20th"
    ↓
Normalized: "20TH_BRYANT"  ← Same as above!
    ↓
(Rest of flow identical - order doesn't matter)
```

---

## Benefits Summary

### 1. Complete Intersection Coverage
- Get ALL streets at an intersection
- Both sides (L and R) of each street
- Typically 4 segments per intersection (2 streets × 2 sides)

### 2. Order-Independent Matching
- "20th & Bryant" = "Bryant & 20th"
- Normalization ensures consistent results

### 3. Multiple Streets Support
- Handles complex intersections (3+ streets)
- Each street has its own CNN in the permutations

### 4. Precise Address Ranges
- Know exact address numbers for each side
- Can determine which corner user is asking about

### 5. Comprehensive Parking Info
- Show regulations for all approaches to intersection
- User sees complete picture of parking at that corner

---

## Implementation Checklist

- [ ] **Data Ingestion**
  - [ ] Ingest intersection permutations (jfxm-zeee)
    - [ ] Handle multiple records per intersection
    - [ ] Extract all CNNs
  - [ ] Ingest street intersections (pu5n-qu5c)
    - [ ] Parse address ranges
  - [ ] Create MongoDB collections and indexes
  - [ ] Validate data quality

- [ ] **Segment Enhancement**
  - [ ] Add address ranges to street_segments
  - [ ] Add intersection boundaries
  - [ ] Validate coverage

- [ ] **API Development**
  - [ ] Implement flexible intersection search
    - [ ] Handle multiple CNNs per intersection
    - [ ] Return all segments (all streets, both sides)
  - [ ] Implement normalization (order-independent)
  - [ ] Add error handling

- [ ] **Frontend Integration**
  - [ ] Update search UI
  - [ ] Display all segments at intersection
  - [ ] Show address ranges
  - [ ] Group by street name

- [ ] **Testing**
  - [ ] Test various input formats
  - [ ] Verify all CNNs returned
  - [ ] Test 3+ street intersections
  - [ ] Performance testing

---

**Last Updated**: November 28, 2024  
**Status**: Complete Architecture - Ready for Implementation