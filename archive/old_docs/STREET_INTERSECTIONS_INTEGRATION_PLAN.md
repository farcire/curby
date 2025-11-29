# Street Intersections Dataset Integration Plan

## Executive Summary

The Street Intersections dataset (pu5n-qu5c) provides **address range information** that enables precise mapping of CNN segments to their left (L) and right (R) sides. This is critical for:
1. Handling user queries with street intersections (e.g., "20th & Bryant")
2. Creating unique CNN L and CNN R identifiers with address ranges
3. Joining Active Streets data with EAS (Enterprise Addressing System) block numbers
4. Achieving comprehensive geospatial accuracy for parking regulations

---

## Dataset Overview

**API Endpoint**: `https://data.sfgov.org/resource/pu5n-qu5c.json`  
**Documentation**: https://dev.socrata.com/foundry/data.sfgov.org/pu5n-qu5c  
**Total Records**: ~35,167 intersection records  
**Unique CNNs**: ~26,249

---

## Critical Dataset Fields

### Address Range Fields (KEY DISCOVERY)

| Field | Description | Maps To |
|-------|-------------|---------|
| `lf_fadd` | Left From Address (starting point) | **CNN L** start address |
| `lf_tadd` | Left To Address (ending point) | **CNN L** end address |
| `rt_fadd` | Right From Address (starting point) | **CNN R** start address |
| `rt_tadd` | Right To Address (ending point) | **CNN R** end address |

### Other Fields

| Field | Description |
|-------|-------------|
| `cnn` | CNN segment identifier |
| `street` | Street name |
| `from_st` | Intersecting street name |
| `streetname` | Alternative street name field |
| `limits` | Intersection description |

---

## Data Model: CNN L and CNN R with Address Ranges

### Concept

Each CNN segment has TWO sides, each with its own address range:

```
CNN 10048000 (20TH ST between BRYANT and FLORIDA)
├── CNN 10048000-L (Left side)
│   ├── Address Range: 900-998 (even numbers)
│   ├── From Intersection: BRYANT ST
│   └── To Intersection: FLORIDA ST
│
└── CNN 10048000-R (Right side)
    ├── Address Range: 901-999 (odd numbers)
    ├── From Intersection: BRYANT ST
    └── To Intersection: FLORIDA ST
```

### Unique Identifier Format

**CNN L**: `{cnn}-L` with address range `[lf_fadd, lf_tadd]`  
**CNN R**: `{cnn}-R` with address range `[rt_fadd, rt_tadd]`

Example:
- `10048000-L` → addresses 900-998
- `10048000-R` → addresses 901-999

---

## Integration Benefits

### 1. Precise Address-to-Segment Mapping

**Current Problem**: When a user provides an address like "950 20th St", we can find the CNN but not definitively determine which side (L or R).

**Solution with Address Ranges**:
```python
def find_segment_by_address(street_name: str, address_number: int) -> StreetSegment:
    """
    Find the exact segment (CNN L or CNN R) for a given address
    
    Example: "950 20th St" → CNN 10048000-L (because 950 is in range 900-998)
    """
    # Find CNN by street name
    cnn = find_cnn_by_street(street_name)
    
    # Get intersection data with address ranges
    intersection = get_intersection_data(cnn)
    
    # Determine side based on address number
    if intersection.lf_fadd <= address_number <= intersection.lf_tadd:
        return get_segment(cnn, "L")
    elif intersection.rt_fadd <= address_number <= intersection.rt_tadd:
        return get_segment(cnn, "R")
    else:
        raise ValueError(f"Address {address_number} not in range for CNN {cnn}")
```

### 2. Intersection Query Resolution

**User Query**: "20th & Bryant"

**Resolution Process**:
```
1. Query intersection dataset:
   WHERE (street='20TH ST' AND from_st='BRYANT ST')
      OR (street='BRYANT ST' AND from_st='20TH ST')

2. Extract intersection data:
   {
     cnn: "10048000",
     street: "20TH ST",
     from_st: "BRYANT ST",
     lf_fadd: 900, lf_tadd: 998,  // Left side range
     rt_fadd: 901, rt_tadd: 999   // Right side range
   }

3. Return BOTH segments:
   - CNN 10048000-L (addresses 900-998)
   - CNN 10048000-R (addresses 901-999)

4. User sees parking regulations for BOTH sides of the street at that intersection
```

### 3. EAS (Enterprise Addressing System) Integration

**Benefit**: Join with EAS block numbers for comprehensive address validation

```sql
-- Conceptual join
SELECT 
    active_streets.cnn,
    intersections.lf_fadd, intersections.lf_tadd,  -- Left range
    intersections.rt_fadd, intersections.rt_tadd,  -- Right range
    eas.block_number,
    eas.lot_number
FROM active_streets
JOIN intersections ON active_streets.cnn = intersections.cnn
JOIN eas ON eas.address BETWEEN intersections.lf_fadd AND intersections.lf_tadd
         OR eas.address BETWEEN intersections.rt_fadd AND intersections.rt_tadd
```

### 4. Comprehensive CNN L and CNN R Coverage

**Current State**: We have CNN + side ("L" or "R") but no address ranges

**Enhanced State**: CNN + side + address range
```javascript
{
  cnn: "10048000",
  side: "L",
  addressRange: {
    from: 900,
    to: 998
  },
  fromIntersection: "BRYANT ST",
  toIntersection: "FLORIDA ST"
}
```

---

## Updated Data Models

### Enhanced StreetSegment Model

```python
class AddressRange(BaseModel):
    """Address range for one side of a street segment"""
    fromAddress: int          # Starting address number
    toAddress: int            # Ending address number
    
class StreetSegment(BaseModel):
    """
    Represents one side of one CNN street segment with address range
    Primary key: (cnn, side)
    Unique identifier: f"{cnn}-{side}"
    """
    cnn: str                                    # e.g., "10048000"
    side: str                                   # "L" or "R"
    streetName: str                             # e.g., "20TH ST"
    
    # Address range for this side (from intersection dataset)
    addressRange: Optional[AddressRange] = None # e.g., {from: 900, to: 998}
    
    # Intersection boundaries
    fromIntersection: Optional[str] = None      # e.g., "BRYANT ST"
    toIntersection: Optional[str] = None        # e.g., "FLORIDA ST"
    
    # Geometries
    centerlineGeometry: Dict                    # GeoJSON from Active Streets
    blockfaceGeometry: Optional[Dict] = None    # GeoJSON from pep9 (optional)
    
    # Rules and schedules
    rules: List[Dict] = []
    schedules: List[Schedule] = []
    
    # Metadata
    zip_code: Optional[str] = None
    layer: Optional[str] = None
```

### New Intersection Model

```python
class Intersection(BaseModel):
    """
    Represents a street intersection with address range information
    """
    cnn: str                          # CNN of main street
    street: str                       # Main street name
    fromStreet: str                   # Intersecting street name
    
    # Left side address range (maps to CNN L)
    lfFromAddress: Optional[int] = None  # lf_fadd
    lfToAddress: Optional[int] = None    # lf_tadd
    
    # Right side address range (maps to CNN R)
    rtFromAddress: Optional[int] = None  # rt_fadd
    rtToAddress: Optional[int] = None    # rt_tadd
    
    # Optional fields
    limits: Optional[str] = None
    geometry: Optional[Dict] = None      # Point geometry if available
```

---

## Implementation Strategy

### Phase 1: Data Ingestion

**Ingest intersection data with address ranges:**

```python
async def ingest_intersections():
    """
    Ingest intersection dataset and populate address ranges
    """
    # Fetch from Socrata API
    intersections = fetch_all_intersections()
    
    for intersection in intersections:
        doc = {
            "cnn": intersection["cnn"],
            "street": intersection.get("street", intersection.get("streetname")),
            "fromStreet": intersection.get("from_st"),
            "limits": intersection.get("limits"),
            
            # Address ranges
            "lfFromAddress": parse_int(intersection.get("lf_fadd")),
            "lfToAddress": parse_int(intersection.get("lf_tadd")),
            "rtFromAddress": parse_int(intersection.get("rt_fadd")),
            "rtToAddress": parse_int(intersection.get("rt_tadd")),
        }
        
        await db.intersections.insert_one(doc)
    
    # Create indexes
    await db.intersections.create_index([("cnn", 1)])
    await db.intersections.create_index([("street", 1), ("fromStreet", 1)])
```

### Phase 2: Enhance Street Segments with Address Ranges

**Update existing street_segments with address range data:**

```python
async def enhance_segments_with_address_ranges():
    """
    Add address range information to existing street segments
    """
    async for segment in db.street_segments.find():
        cnn = segment["cnn"]
        side = segment["side"]
        
        # Find intersection data for this CNN
        intersections = await db.intersections.find({"cnn": cnn}).to_list(length=10)
        
        if intersections:
            # Use first intersection (they should all have same address ranges for a CNN)
            intersection = intersections[0]
            
            # Determine address range based on side
            if side == "L":
                address_range = {
                    "fromAddress": intersection.get("lfFromAddress"),
                    "toAddress": intersection.get("lfToAddress")
                }
                from_intersection = intersection.get("fromStreet")
            else:  # side == "R"
                address_range = {
                    "fromAddress": intersection.get("rtFromAddress"),
                    "toAddress": intersection.get("rtToAddress")
                }
                from_intersection = intersection.get("fromStreet")
            
            # Update segment
            await db.street_segments.update_one(
                {"_id": segment["_id"]},
                {"$set": {
                    "addressRange": address_range,
                    "fromIntersection": from_intersection
                }}
            )
```

### Phase 3: API Endpoints

#### 3.1 Search by Intersection

```python
@app.get("/api/v1/intersections/search")
async def search_intersection(street1: str, street2: str):
    """
    Find segments at a street intersection
    
    Example: /api/v1/intersections/search?street1=20TH%20ST&street2=BRYANT%20ST
    
    Returns both CNN L and CNN R segments with their address ranges
    """
    # Normalize street names
    street1_norm = normalize_street_name(street1)
    street2_norm = normalize_street_name(street2)
    
    # Query intersections (bidirectional)
    query = {
        "$or": [
            {"street": street1_norm, "fromStreet": street2_norm},
            {"street": street2_norm, "fromStreet": street1_norm}
        ]
    }
    
    intersections = await db.intersections.find(query).to_list(length=100)
    
    if not intersections:
        raise HTTPException(status_code=404, detail="Intersection not found")
    
    # Extract unique CNNs
    cnns = list(set([i["cnn"] for i in intersections]))
    
    # Fetch all segments (both L and R) for these CNNs
    segments = await db.street_segments.find({"cnn": {"$in": cnns}}).to_list(length=100)
    
    return {
        "intersection": f"{street1} & {street2}",
        "cnns": cnns,
        "segments": segments  # Includes address ranges for each side
    }
```

#### 3.2 Search by Address

```python
@app.get("/api/v1/segments/by-address")
async def get_segment_by_address(street: str, number: int):
    """
    Find the exact segment (CNN L or CNN R) for a specific address
    
    Example: /api/v1/segments/by-address?street=20TH%20ST&number=950
    
    Returns the specific side (L or R) that contains this address
    """
    street_norm = normalize_street_name(street)
    
    # Find segments on this street
    segments = await db.street_segments.find({"streetName": street_norm}).to_list(length=1000)
    
    # Filter by address range
    matching_segment = None
    for segment in segments:
        addr_range = segment.get("addressRange")
        if addr_range:
            from_addr = addr_range.get("fromAddress")
            to_addr = addr_range.get("toAddress")
            
            if from_addr and to_addr and from_addr <= number <= to_addr:
                matching_segment = segment
                break
    
    if not matching_segment:
        raise HTTPException(status_code=404, detail=f"No segment found for {number} {street}")
    
    return matching_segment
```

### Phase 4: Frontend Integration

**Enhanced search with address range display:**

```typescript
interface SegmentWithAddressRange extends Segment {
  addressRange?: {
    fromAddress: number;
    toAddress: number;
  };
  fromIntersection?: string;
  toIntersection?: string;
}

// Display address range in UI
function SegmentCard({ segment }: { segment: SegmentWithAddressRange }) {
  return (
    <div>
      <h3>{segment.streetName} ({segment.side} side)</h3>
      
      {segment.addressRange && (
        <p>
          Addresses: {segment.addressRange.fromAddress} - {segment.addressRange.toAddress}
        </p>
      )}
      
      {segment.fromIntersection && segment.toIntersection && (
        <p>
          Between {segment.fromIntersection} and {segment.toIntersection}
        </p>
      )}
      
      {/* Parking regulations */}
    </div>
  );
}
```

---

## Implementation Checklist

- [ ] **Data Ingestion**
  - [ ] Fetch intersection dataset from Socrata API
  - [ ] Parse address range fields (lf_fadd, lf_tadd, rt_fadd, rt_tadd)
  - [ ] Store in MongoDB intersections collection
  - [ ] Create appropriate indexes
  
- [ ] **Segment Enhancement**
  - [ ] Update existing street_segments with address ranges
  - [ ] Add fromIntersection and toIntersection fields
  - [ ] Validate address range coverage
  
- [ ] **API Development**
  - [ ] Create `/api/v1/intersections/search` endpoint
  - [ ] Create `/api/v1/segments/by-address` endpoint
  - [ ] Implement street name normalization
  - [ ] Add comprehensive error handling
  
- [ ] **Frontend Updates**
  - [ ] Update search to detect intersection format
  - [ ] Display address ranges in segment cards
  - [ ] Show intersection boundaries
  - [ ] Add address-based search
  
- [ ] **Testing & Validation**
  - [ ] Test intersection queries
  - [ ] Validate address range accuracy
  - [ ] Test edge cases (missing data, invalid addresses)
  - [ ] Performance testing

---

## Key Benefits Summary

1. **Precise Address Mapping**: Determine exact side (L or R) from address number
2. **Intersection Queries**: Handle "20th & Bryant" style user input
3. **EAS Integration**: Join with Enterprise Addressing System for block/lot data
4. **Complete Coverage**: CNN L and CNN R with full address range information
5. **Better UX**: Show users exactly which side of the street and address range
6. **Data Validation**: Cross-reference address ranges across datasets

---

## Next Steps

1. **Immediate**: Verify intersection dataset fields via API
2. **Short-term**: Implement data ingestion script
3. **Medium-term**: Enhance segments and create API endpoints
4. **Long-term**: Full EAS integration for comprehensive address system

---

**Last Updated**: November 28, 2024  
**Status**: Architecture Defined - Ready for Implementation