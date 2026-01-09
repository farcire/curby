# Data Architecture: Updated Understanding (December 2025)

## Executive Summary

This document reflects our **updated understanding** of how San Francisco parking data is structured, based on investigation of the pep9-66vw (Blockface) and 3psu-pn9h (Active Streets) datasets.

**Key Discovery**: The pep9-66vw dataset contains **side-specific geometries** where each CNN segment is represented by **two separate records** (one for each side of the street), each with its own unique GlobalID and parallel geometry.

**⚠️ Data Quality Alert**: Investigation has revealed missing records in the Street Cleaning dataset. See [DATA_QUALITY_ISSUES.md](DATA_QUALITY_ISSUES.md) for details.

---

## Dataset Relationships

### 1. Active Streets (3psu-pn9h) - The Backbone

**Purpose**: Authoritative street centerline network maintained by SFMTA

**Key Fields**:
- `cnn`: Unique street segment identifier (e.g., "1046000")
- `street_name`: Street name
- `from_street`, `to_street`: Intersection boundaries
- `geometry`: Street centerline (LineString)

**Coverage**: ~2,007 CNN segments covering all of San Francisco

**Role**: Provides the foundational street network and CNN identifiers that other datasets reference.

---

### 2. Blockface Geometries (pep9-66vw) - Side-Specific Segments

**Purpose**: Provides side-specific geometries for parking regulation boundaries

**Critical Discovery**: This dataset does NOT provide one geometry per CNN. Instead:
- **One CNN → Two GlobalIDs** (one for left side, one for right side)
- Each GlobalID has its own parallel geometry
- Geometries are offset from the centerline to represent each side

**Key Fields**:
- `globalid`: **Unique identifier** (GUID format, e.g., {102E3CBB-E7F4-4B47-8B4C-6B8B4159DFDC})
- `cnn_id`: References Active Streets CNN (but NOT unique - shared by both sides)
- `shape`: LineString geometry (2 points: start and end)
- `lf_fadd`, `lf_toadd`: Left side address range
- `rt_fadd`, `rt_toadd`: Right side address range

**Structure Example** (CNN 10048000):
```
CNN 10048000 (20th Street segment)
├── GlobalID {102E3CBB...}
│   ├── Geometry: [-122.420306, 37.770354] to [-122.420419, 37.771583]
│   └── Side: LEFT (determined geometrically)
│
└── GlobalID {6EEEBD30...}
    ├── Geometry: [-122.420094, 37.770407] to [-122.420202, 37.771593]
    └── Side: RIGHT (determined geometrically)
```

**Coverage**: ~50-60% of CNNs have blockface geometries
- Records WITH cnn_id: Have both GlobalIDs (left and right)
- Records WITHOUT cnn_id: Orphaned geometries (legacy data)

**Coordinate System**: WGS84 (EPSG:4326) - standard latitude/longitude

---

### 3. How Sides Are Determined

#### Method 1: Geometric Analysis (Cross-Product)

For records with both centerline and blockface geometries:

```python
def determine_side(centerline, blockface):
    """
    Uses cross-product to determine if blockface is on left or right
    
    1. Find midpoint of blockface geometry
    2. Project midpoint onto centerline
    3. Calculate tangent vector along centerline
    4. Calculate vector from centerline to blockface
    5. Cross product determines side:
       - Positive = LEFT
       - Negative = RIGHT
    """
    # Implementation in get_side_of_street()
```

#### Method 2: Address Range Analysis

For records with address data:
- Left side: `lf_fadd` to `lf_toadd`
- Right side: `rt_fadd` to `rt_toadd`
- Can infer which GlobalID represents which side

#### Method 3: Multiple GlobalIDs per CNN

**Key Insight**: When a CNN has multiple GlobalIDs in pep9-66vw:
- They represent the LEFT and RIGHT sides
- Geometries are parallel, offset from centerline
- Typical offset: ~10-20 meters

---

## Join Strategies

### Strategy 1: CNN-Based Join (Primary)

**When to use**: When both datasets have CNN identifiers

```
Active Streets (CNN 1046000)
    ↓ (join on cnn_id)
Blockface Geometries
    ├── GlobalID A (Left side)
    └── GlobalID B (Right side)
```

**Process**:
1. Match on `cnn` = `cnn_id`
2. Get both GlobalIDs for that CNN
3. Use geometric analysis to determine which is left/right
4. Create two segments: (CNN, "L") and (CNN, "R")

### Strategy 2: Spatial Join (Fallback)

**When to use**: When blockface has no cnn_id

```
Active Streets (centerline geometry)
    ↓ (spatial intersection)
Blockface Geometries (orphaned records)
    ↓ (geometric analysis)
Determine side and attach
```

**Process**:
1. Find centerlines that intersect blockface geometry
2. Use cross-product to determine side
3. Attach to appropriate segment

### Strategy 3: GlobalID as Primary Key

**New Understanding**: GlobalID should be treated as the primary key for blockface data

```
street_segments collection:
{
  _id: ObjectId,
  cnn: "1046000",
  side: "L",
  globalid: "{102E3CBB-E7F4-4B47-8B4C-6B8B4159DFDC}",
  centerlineGeometry: {...},  // from Active Streets
  blockfaceGeometry: {...},   // from pep9-66vw (optional)
  ...
}
```

---

## Updated Data Model

### StreetSegment (Revised)

```typescript
interface StreetSegment {
  // Identity
  cnn: string;                    // From Active Streets
  side: "L" | "R";                // Determined geometrically
  globalid?: string;              // From pep9-66vw (if available)
  
  // Geometries
  centerlineGeometry: LineString; // ALWAYS present (from Active Streets)
  blockfaceGeometry?: LineString; // OPTIONAL (from pep9-66vw)
  
  // Boundaries
  fromStreet: string;
  toStreet: string;
  
  // Address Ranges (if available)
  addressRangeStart?: number;
  addressRangeEnd?: number;
  
  // Rules (attached during ingestion)
  parkingRegulations: ParkingRegulation[];
  streetCleaning: StreetCleaningSchedule[];
  meters: ParkingMeter[];
}
```

### Key Changes from Previous Understanding

**Before**:
- Assumed one blockface geometry per CNN
- Used blockface geometry as primary
- Missing geometries = no data

**After**:
- Two blockface geometries per CNN (left and right)
- Use centerline geometry as primary (always available)
- Blockface geometries are optional enhancements
- GlobalID is the unique identifier for each side

---

## Coverage Analysis

### Current State

**Active Streets**: 2,007 CNNs × 2 sides = **4,014 potential segments**

**Blockface Geometries**:
- Records with cnn_id: ~1,000-1,200 CNNs
- Each CNN typically has 2 GlobalIDs (left and right)
- Total blockface geometries: ~2,000-2,400 records
- **Coverage**: ~50-60% of CNNs have blockface geometries

**Impact**:
- 100% coverage using centerline geometries
- 50-60% have enhanced blockface geometries
- All segments can display and function

### What This Means

**For Display**:
- Can show all streets using centerline geometry
- Can enhance ~50% with more precise blockface geometry
- No gaps in coverage

**For Rules**:
- All segments can have rules attached
- Side determination works for all segments
- Blockface geometry improves precision but isn't required

---

## Parking Regulation Joins

### Street Sweeping (yhqp-riqs)

**Join Method**: Direct CNN + Side match

```python
# Street sweeping has explicit side field
sweeping.cnn == segment.cnn AND sweeping.side == segment.side
```

**Coverage**: High - most sweeping records have CNN and side

**⚠️ Known Data Quality Issue**: Some street cleaning records are missing from the dataset despite existing physically.
- Example: CNN 961000R (19th St, North side) - Missing Thursday 12AM-6AM schedule
- Impact: Incomplete parking restriction information for users
- See [DATA_QUALITY_ISSUES.md](DATA_QUALITY_ISSUES.md#issue-1-missing-street-cleaning-records) for details
- Workaround: Implement cardinal direction inference from geometry

### Parking Regulations (hi6h-neyh)

**Join Method**: Geometric analysis required

**Process**:
1. Match on CNN (if available)
2. Use regulation geometry to determine side
3. Apply cross-product calculation
4. Attach to matching segment

**Challenge**: Regulation geometries are offset lines, need geometric analysis to determine which side they apply to.

### Parking Meters (sfmta-parking-meters)

**Join Method**: CNN-based

```python
# Meters have street_seg_ctrln_id field
meter.street_seg_ctrln_id == segment.cnn
```

**Note**: Meters typically apply to both sides, so attach to both L and R segments.

---

## Implementation Implications

### 1. Segment Generation

**New Approach**:
```python
for cnn in active_streets:
    # Create both sides
    left_segment = create_segment(cnn, "L")
    right_segment = create_segment(cnn, "R")
    
    # Add centerline geometry (always available)
    left_segment.centerlineGeometry = cnn.geometry
    right_segment.centerlineGeometry = cnn.geometry
    
    # Add blockface geometries if available
    blockfaces = get_blockfaces_for_cnn(cnn)
    for bf in blockfaces:
        side = determine_side(cnn.geometry, bf.shape)
        if side == "L":
            left_segment.blockfaceGeometry = bf.shape
            left_segment.globalid = bf.globalid
        else:
            right_segment.blockfaceGeometry = bf.shape
            right_segment.globalid = bf.globalid
```

### 2. Querying

**Spatial Queries**:
```javascript
// Use centerline geometry for queries (always available)
db.street_segments.find({
  centerlineGeometry: {
    $near: {
      $geometry: { type: "Point", coordinates: [lng, lat] },
      $maxDistance: 50
    }
  }
})
```

**By GlobalID** (when available):
```javascript
db.street_segments.findOne({ globalid: "{102E3CBB...}" })
```

### 3. Display

**Frontend Rendering**:
```typescript
// Prefer blockface geometry if available, fall back to centerline
const geometry = segment.blockfaceGeometry || segment.centerlineGeometry;

// Show side indicator
const sideLabel = segment.side === "L" ? "Left" : "Right";
```

---

## Migration Path

### Phase 1: Update Data Model ✓
- Add `globalid` field to StreetSegment
- Make `blockfaceGeometry` optional
- Ensure `centerlineGeometry` is always present

### Phase 2: Update Ingestion ✓
- Generate 2 segments per CNN
- Match blockface geometries by CNN + geometric analysis
- Store GlobalID when available

### Phase 3: Update Queries
- Use centerline geometry for spatial queries
- Support GlobalID lookups
- Handle optional blockface geometry

### Phase 4: Update Frontend
- Render centerline geometry
- Show side indicators (L/R)
- Display blockface geometry when available (as enhancement)

---

## Key Takeaways

1. **GlobalID is unique** - can be used as primary key for blockface data
2. **One CNN = Two GlobalIDs** - representing left and right sides
3. **Geometries are parallel** - offset from centerline to show each side
4. **Coverage is partial** - only ~50-60% of CNNs have blockface geometries
5. **Centerline is authoritative** - use Active Streets as backbone
6. **Blockface is enhancement** - provides more precise boundaries when available
7. **Side determination is geometric** - use cross-product calculation
8. **All segments can function** - even without blockface geometry
9. **⚠️ Data quality varies** - some source datasets have missing records (see [DATA_QUALITY_ISSUES.md](DATA_QUALITY_ISSUES.md))

---

## Data Quality

### Known Issues

The system has identified data quality issues in source datasets that affect completeness and accuracy:

1. **Missing Street Cleaning Records** (HIGH severity)
   - Some CNN segments missing cleaning schedules despite physical existence
   - Example: CNN 961000R missing Thursday 12AM-6AM schedule
   - Impact: Users won't see these restrictions
   - See [DATA_QUALITY_ISSUES.md](DATA_QUALITY_ISSUES.md) for full details

2. **Missing Cardinal Directions** (MEDIUM severity)
   - Segments without street cleaning lack cardinal direction metadata
   - Affects display name generation
   - Workaround: Implement geometric inference

3. **Missing From/To Streets** (LOW severity)
   - Segments without street cleaning lack boundary street names
   - Workaround: Use Active Streets f_st/t_st fields

### Investigation Tools

- [`inspect_cnn_961000.py`](inspect_cnn_961000.py) - Template for investigating specific CNNs
- [`cnn_961000_investigation/`](cnn_961000_investigation/) - Example investigation with findings

## References

- [`pep9_globalid_shape_analysis.txt`](backend/pep9_globalid_shape_analysis.txt) - Detailed investigation
- [`CNN_SEGMENT_IMPLEMENTATION_COMPLETE.md`](backend/CNN_SEGMENT_IMPLEMENTATION_COMPLETE.md) - Implementation details
- [`models.py`](backend/models.py) - Data model definitions
- [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py) - Ingestion logic
- [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md) - Known data quality issues and workarounds

---

**Last Updated**: December 4, 2025
**Status**: Current understanding based on dataset investigation + data quality findings