# RPP Zone Implementation Plan - Four-Method Strategy

## Executive Summary

This plan implements a **four-method validation approach** for accurate RPP (Residential Parking Permit) zone assignments in the street-level parking application.

### The Complete Solution

**Problem:** Determining which side of a street (L vs R) has which RPP zone when geometric offset analysis can be ambiguous.

**Solution:** Layer four complementary methods for maximum accuracy:

1. **Parking Regulations (hi6h-neyh)** - Current geometric method ✅
2. **Address Range Matching (3psu-pn9h + i886-hxz9)** - Direct address-based mapping ⭐⭐⭐
3. **Parcels with Overlay Attributes (9grn-xjpx)** - Boundary resolution ⭐⭐
4. **RPP Eligibility Parcels (i886-hxz9)** - Ground truth validation ⭐

---

## Four-Method Approach

### 1. Parking Regulations (hi6h-neyh) - CURRENT ✅

**Status:** Already implemented in [`ingest_data.py`](backend/ingest_data.py:263-365)

**Contains:**
- RPP codes (rpparea1, rpparea2)
- Offset geometries (lines on side of street)
- Time limits, days, hours
- Complete rule details

**Current Method:**
- Geometric cross-product analysis via [`get_side_of_street()`](backend/ingest_data.py:29-74)
- Spatial intersection with blockfaces
- Works for most cases (e.g., CNN 1046000)

**Limitations:**
- Offset geometries can be ambiguous
- Cross-product calculations depend on coordinate precision
### 2. Address Range Matching (3psu-pn9h + i886-hxz9) - NEW ⭐⭐⭐

**Purpose:** Direct address-based mapping of parcels to L/R sides

**Key Insight:** Active Streets contains address ranges for each side of every street segment!

**Active Streets Fields:**
- `lf_fadd`: Left side FROM address (low number)
- `lf_toadd`: Left side TO address (high number)
- `rt_fadd`: Right side FROM address (low number)
- `rt_toadd`: Right side TO address (high number)
- `cnn`: Street segment identifier
- `streetname`: Street name

**RPP Parcels Fields:**
- `from_st`: Street address number
- `street`: Street name
- `rppeligib`: RPP area code (W, I, J, K, Q, etc.)
- `mapblklot`: Parcel ID

**How It Works:**

```python
# Example for 20th Street, CNN 1046000
Active Streets record:
  cnn: "1046000"
  streetname: "20TH ST"
  lf_fadd: "3200"  # Left side starts at 3200
  lf_toadd: "3298"  # Left side ends at 3298
  rt_fadd: "3201"  # Right side starts at 3201
  rt_toadd: "3299"  # Right side ends at 3299

RPP Parcel record:
  from_st: "3250"
  street: "20TH ST"
  rppeligib: "W"

# Match logic:
if 3200 <= 3250 <= 3298:
    side = "L"  # Address 3250 falls in left range
    rpp_area = "W"
```

**Critical Value:**
- ✅ **Most direct method** - No geometric calculations needed
- ✅ **Deterministic** - Address either falls in range or doesn't
- ✅ **Fast** - Simple numeric comparison
- ✅ **Accurate** - Based on official address assignments

**Use Cases:**
- Primary method for RPP assignment
- Validating geometric methods
- Resolving ambiguous cases
- Providing building-level precision

**Advantages over Geometric Methods:**
1. No dependency on coordinate precision
2. No cross-product calculations
3. No spatial queries needed
4. Works even with imperfect geometries
5. Matches how humans think about addresses

**Dataset IDs:**
- Active Streets: `3psu-pn9h`
- RPP Parcels: `i886-hxz9`

- Street curves create edge cases

### 2. Parcels with Overlay Attributes (9grn-xjpx) - NEW ⭐⭐

**Purpose:** Definitive boundary resolution

**Key Feature:** "Boundaries run along streets and are non-overlapping"

**Contains:**
- Parcel geometries (MultiPolygon)
- Analysis Neighborhood assignments
- Pre-processed spatial joins
- District boundaries

**Critical Value:**
- ✅ **Non-overlapping boundaries** = No ambiguity
- ✅ When a parcel is assigned to a neighborhood, that assignment is definitive
- ✅ Boundaries follow street centerlines exactly

**Use Cases:**
- Resolving geographic ambiguity
- Determining which side of a street boundary a point/parcel falls on
- Providing authoritative "this parcel is in Mission" assignments

**Dataset ID:** `9grn-xjpx`

### 3. RPP Eligibility Parcels (i886-hxz9) - NEW ⭐

**Purpose:** Ground truth for RPP zone assignments

**Contains:**
- Parcel ID (mapblklot)
- RPP area code (rppeligib): Q, J, K, W, I, etc.
- Building footprint geometry (MultiPolygon)

**Use Cases:**
- Determining which physical side of street is residential
- Validating geometric join results
- Resolving ambiguous cases
- Providing building-level precision

**Dataset ID:** `i886-hxz9`

---

## Why This Four-Method Approach Works

### Layered Validation Strategy

```
┌─────────────────────────────────────────────────────────────┐
│ Method 1: Address Range Matching (PRIMARY) ⭐⭐⭐            │
│ - Direct numeric comparison of parcel address to ranges     │
│ - Most deterministic and reliable                           │
│ - No geometric calculations needed                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Method 2: Geometric Analysis (FALLBACK)                     │
│ - Cross-product of regulation offset vs street centerline   │
│ - Works when address data unavailable                       │
│ - Fast and efficient                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Method 3: Overlay Parcels (BOUNDARY RESOLUTION)             │
│ - Non-overlapping boundaries eliminate ambiguity            │
│ - Street-aligned boundaries provide definitive side         │
│ - Resolves edge cases                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Method 4: Spatial Parcel Matching (VALIDATION)              │
│ - Actual RPP codes from building footprints                 │
│ - Validates assignments                                      │
│ - Flags discrepancies for review                            │
└─────────────────────────────────────────────────────────────┘
```

### Confidence Scoring

Each assignment gets a confidence score based on agreement:

- **VERY HIGH**: Address method + 2+ other methods agree
- **HIGH**: Address method + 1 other method agree, or 3+ methods agree
- **MEDIUM**: Two methods agree, others differ
- **LOW**: Methods disagree, manual review needed

---

## Implementation Plan

### Phase 1: Data Ingestion (Priority: HIGH)


### Practical Implementation Example

Here's how the address-based method works in practice:

```python
# Example: Determining RPP zone for 3250 20th Street

# Step 1: Get Active Streets data for 20th Street
active_streets = {
    'cnn': '1046000',
    'streetname': '20TH ST',
    'lf_fadd': '3200',  # Left side: 3200-3298 (even numbers)
    'lf_toadd': '3298',
    'rt_fadd': '3201',  # Right side: 3201-3299 (odd numbers)
    'rt_toadd': '3299'
}

# Step 2: Get RPP Parcel data
rpp_parcel = {
    'from_st': '3250',
    'street': '20TH ST',
    'rppeligib': 'W',
    'mapblklot': '3634001'
}

# Step 3: Match address to side
address = 3250
if 3200 <= address <= 3298:
    side = 'L'  # ✓ Match!
    rpp_zone = 'W'

# Result: Left side of 20th St (CNN 1046000) = RPP Area W
```

**Why This Works Better Than Geometric Methods:**

1. **Deterministic**: 3250 is either in range [3200-3298] or it isn't
2. **No Ambiguity**: No need to calculate which side of a line a point falls on
3. **Fast**: Simple integer comparison vs complex geometric calculations
4. **Robust**: Works even if geometries are slightly misaligned
5. **Intuitive**: Matches how addresses actually work in the real world

#### Task 1.1: Ingest RPP Eligibility Parcels

**Objective:** Load building footprints with RPP codes

```python
# Add to ingest_data.py

RPP_PARCELS_ID = "i886-hxz9"

async def ingest_rpp_parcels():
    """
    Ingest RPP Eligibility Parcels for Mission/SOMA
    """
    print("\n--- Ingesting RPP Eligibility Parcels ---")
    
    # Fetch parcels (filter by Mission RPP areas: W, I, J, K, Q, etc.)
    parcels_df = fetch_data_as_dataframe(
        RPP_PARCELS_ID, 
        app_token,
        where="rppeligib IN ('W', 'I', 'J', 'K', 'Q', 'R', 'S', 'T', 'U', 'V', 'X', 'Y', 'Z')"
    )
    
    if not parcels_df.empty:
        # Save to MongoDB
        await db.rpp_parcels.delete_many({})
        await db.rpp_parcels.insert_many(parcels_df.to_dict('records'))
        
        # Create geospatial index
        await db.rpp_parcels.create_index([("shape", "2dsphere")])
        
        print(f"Saved {len(parcels_df)} RPP parcels")
        
        # Log sample
        sample = parcels_df.head(3)
        print("\nSample RPP Parcels:")
        for _, row in sample.iterrows():
            print(f"  Parcel {row.get('mapblklot')}: RPP Area {row.get('rppeligib')}")
```

#### Task 1.2: Ingest Parcels with Overlay Attributes

**Objective:** Load boundary parcels for definitive side determination

```python
# Add to ingest_data.py

OVERLAY_PARCELS_ID = "9grn-xjpx"

async def ingest_overlay_parcels():
    """
    Ingest Parcels with Overlay Attributes for Mission
    """
    print("\n--- Ingesting Overlay Parcels ---")
    
    # Fetch Mission parcels
    parcels_df = fetch_data_as_dataframe(
        OVERLAY_PARCELS_ID,
        app_token,
        where="analysis_neighborhood='Mission'"
    )
    
    if not parcels_df.empty:
        await db.overlay_parcels.delete_many({})
        await db.overlay_parcels.insert_many(parcels_df.to_dict('records'))
        
        # Create geospatial index
        await db.overlay_parcels.create_index([("the_geom", "2dsphere")])
        
        print(f"Saved {len(parcels_df)} overlay parcels")
        
        # Log sample
        sample = parcels_df.head(3)
        print("\nSample Overlay Parcels:")
        for _, row in sample.iterrows():
            print(f"  Parcel {row.get('mapblklot')}: Neighborhood {row.get('analysis_neighborhood')}")
```

**Acceptance Criteria:**
- [ ] RPP parcels collection created with 2dsphere index
- [ ] Overlay parcels collection created with 2dsphere index
- [ ] Verify data in MongoDB Atlas
- [ ] Confirm geometries are valid GeoJSON
- [ ] Test spatial queries work correctly

---

### Phase 2: Enhanced Side Determination (Priority: HIGH)

#### Task 2.1: Create Side Determination Module

**Objective:** Implement three-layer validation logic

```python
# Create backend/side_determination.py

from shapely.geometry import shape, Point, LineString
from typing import Dict, Optional, List, Tuple

def determine_side_by_address(
    parcel_address: int,
    street_name: str,
    street_segments: List[Dict]
) -> Optional[str]:
    """
    Method 1: Address range matching (PRIMARY METHOD)
    
    Args:
        parcel_address: Street address number (e.g., 3250)
        street_name: Street name (e.g., "20TH ST")
        street_segments: List of Active Streets records for this street
    
    Returns: 'L', 'R', or None
    
    Example:
        parcel_address = 3250
        street_name = "20TH ST"
        segment = {
            'cnn': '1046000',
            'streetname': '20TH ST',
            'lf_fadd': '3200',  # Left from
            'lf_toadd': '3298',  # Left to
            'rt_fadd': '3201',  # Right from
            'rt_toadd': '3299'   # Right to
        }
        
        Result: 'L' (because 3200 <= 3250 <= 3298)
    """
    try:
        for segment in street_segments:
            # Normalize street names for comparison
            seg_street = segment.get('streetname', '').upper().strip()
            if seg_street != street_name.upper().strip():
                continue
            
            # Get address ranges
            lf_from = int(segment.get('lf_fadd', 0) or 0)
            lf_to = int(segment.get('lf_toadd', 0) or 0)
            rt_from = int(segment.get('rt_fadd', 0) or 0)
            rt_to = int(segment.get('rt_toadd', 0) or 0)
            
            # Check if address falls in left range
            if lf_from and lf_to and lf_from <= parcel_address <= lf_to:
                return 'L'
            
            # Check if address falls in right range
            if rt_from and rt_to and rt_from <= parcel_address <= rt_to:
                return 'R'
        
        return None
        
    except (ValueError, TypeError):
        return None


def determine_side_geometric(regulation_geo: Dict, centerline_geo: Dict) -> Optional[str]:
    """
    Method 2: Current geometric cross-product method (FALLBACK)
    
    Returns: 'L', 'R', or None
    """
    try:
        cl_shape = shape(centerline_geo)
        reg_shape = shape(regulation_geo)
        
        if not isinstance(cl_shape, LineString):
            return None
            
        # Get midpoint of regulation
        reg_mid = reg_shape.interpolate(0.5, normalized=True) if hasattr(reg_shape, 'interpolate') else reg_shape.centroid
        
        # Project onto centerline
        projected_dist = cl_shape.project(reg_mid)
        projected_point = cl_shape.interpolate(projected_dist)
        
        # Get tangent vector
        delta = 0.001
        if projected_dist + delta > cl_shape.length:
            p1 = cl_shape.interpolate(projected_dist - delta)
            p2 = projected_point
        else:
            p1 = projected_point
            p2 = cl_shape.interpolate(projected_dist + delta)
        
        # Cross product
        cl_vec = (p2.x - p1.x, p2.y - p1.y)
        to_reg_vec = (reg_mid.x - projected_point.x, reg_mid.y - projected_point.y)
        cross_product = cl_vec[0] * to_reg_vec[1] - cl_vec[1] * to_reg_vec[0]
        
        return 'L' if cross_product > 0 else 'R'
        
    except Exception as e:
        return None


def determine_cardinal_side(point: Point, centerline: LineString) -> str:
    """
    Determine N/S/E/W position relative to centerline
    
    Used by Layer 2 (Overlay Parcels) for boundary resolution
    """
    # Project point onto centerline
    projected_dist = centerline.project(point)
    projected_point = centerline.interpolate(projected_dist)
    
    # Get tangent vector
    delta = 0.001
    if projected_dist + delta > centerline.length:
        p1 = centerline.interpolate(projected_dist - delta)
        p2 = projected_point
    else:
        p1 = projected_point
        p2 = centerline.interpolate(projected_dist + delta)
    
    # Vector from centerline to point
    to_point = (point.x - projected_point.x, point.y - projected_point.y)
    tangent = (p2.x - p1.x, p2.y - p1.y)
    
    # Cross product determines side
    cross = tangent[0] * to_point[1] - tangent[1] * to_point[0]
    
    # Determine if street runs E-W or N-S
    if abs(tangent[0]) > abs(tangent[1]):
        # Street runs E-W
        return 'N' if cross > 0 else 'S'
    else:
        # Street runs N-S
        return 'E' if cross > 0 else 'W'


def map_cardinal_to_lr(cardinal: str, block_side_mapping: Dict[str, str]) -> Optional[str]:
    """
    Map cardinal direction (N/S/E/W) to L/R using BlockSide mapping
    
    Args:
        cardinal: 'N', 'S', 'E', or 'W'
        block_side_mapping: {'L': 'South', 'R': 'North'} from street cleaning
    
    Returns: 'L' or 'R' or None
    """
    if not block_side_mapping:
        return None
    
    # Reverse the mapping to go from cardinal -> L/R
    for lr, card in block_side_mapping.items():
        if card.lower().startswith(cardinal.lower()):
            return lr
    
    return None


def determine_side_with_parcels(
    street_segment: Dict,
    rpp_parcels: List[Dict],
    overlay_parcels: List[Dict]
) -> Dict[str, Tuple[Optional[str], str]]:
    """
    Layer 2 & 3: Use parcels to validate/determine sides
    
    Returns: {
        'L': ('W', 'high'),  # (RPP area, confidence)
        'R': (None, 'low')
    }
    """
    centerline = shape(street_segment['centerlineGeometry'])
    block_side_mapping = street_segment.get('block_side_mapping', {})
    
    # Get nearby RPP parcels (within ~50 meters)
    nearby_rpp = [p for p in rpp_parcels 
                  if shape(p['shape']).distance(centerline) < 0.0005]
    
    # Determine which side each parcel is on
    side_assignments = {'L': [], 'R': []}
    
    for parcel in nearby_rpp:
        parcel_shape = shape(parcel['shape'])
        parcel_centroid = parcel_shape.centroid
        
        # Use cardinal direction determination
        cardinal = determine_cardinal_side(parcel_centroid, centerline)
        
        # Map to L/R using BlockSide
        lr_side = map_cardinal_to_lr(cardinal, block_side_mapping)
        
        if lr_side:
            rpp_area = parcel.get('rppeligib')
            side_assignments[lr_side].append(rpp_area)
    
    # Return dominant RPP area for each side with confidence
    result = {}
    for side in ['L', 'R']:
        areas = side_assignments[side]
        if areas:
            # Get most common area
            from collections import Counter
            area_counts = Counter(areas)
            dominant_area = area_counts.most_common(1)[0][0]
            confidence = 'high' if len(areas) > 2 else 'medium'
            result[side] = (dominant_area, confidence)
        else:
            result[side] = (None, 'low')
    
    return result


def assign_rpp_with_validation(
    street_segment: Dict,
    regulations: List[Dict],
    rpp_parcels: List[Dict],
    overlay_parcels: List[Dict],
    all_street_segments: List[Dict]
) -> Dict[str, Dict]:
    """
    Four-method validation for RPP assignment
    
    Returns: {
        'L': {
            'rpp_area': 'W',
            'confidence': 'very_high',
            'source': 'address_validated',
            'methods': {
                'address': 'W',
                'geometric': 'W',
                'parcel': 'W',
                'overlay': 'W'
            }
        },
        'R': {...}
    }
    """
    centerline_geo = street_segment['centerlineGeometry']
    street_name = street_segment.get('streetName', '')
    cnn = street_segment.get('cnn')
    
    # Method 1: Address range matching (PRIMARY)
    address_assignments = {}
    for parcel in rpp_parcels:
        parcel_address = parcel.get('from_st')
        parcel_street = parcel.get('street', '')
        rpp_area = parcel.get('rppeligib')
        
        if parcel_address and rpp_area:
            try:
                address_num = int(parcel_address)
                side = determine_side_by_address(
                    address_num,
                    parcel_street or street_name,
                    all_street_segments
                )
                if side:
                    if side not in address_assignments:
                        address_assignments[side] = []
                    address_assignments[side].append(rpp_area)
            except (ValueError, TypeError):
                continue
    
    # Get dominant RPP area for each side from address method
    address_rpp = {}
    for side in ['L', 'R']:
        if side in address_assignments and address_assignments[side]:
            from collections import Counter
            area_counts = Counter(address_assignments[side])
            address_rpp[side] = area_counts.most_common(1)[0][0]
    
    # Method 2: Geometric analysis (FALLBACK)
    geometric_assignments = {}
    for reg in regulations:
        reg_geo = reg.get('shape') or reg.get('geometry')
        if reg_geo:
            side = determine_side_geometric(reg_geo, centerline_geo)
            rpp_area = reg.get('rpparea1') or reg.get('rpparea2')
            if side and rpp_area:
                geometric_assignments[side] = rpp_area
    
    # Method 3 & 4: Parcel-based validation
    parcel_assignments = determine_side_with_parcels(
        street_segment, rpp_parcels, overlay_parcels
    )
    
    # Resolve conflicts and assign confidence
    final_assignments = {}
    for side in ['L', 'R']:
        address_rpp_val = address_rpp.get(side)
        geometric_rpp = geometric_assignments.get(side)
        parcel_rpp, parcel_conf = parcel_assignments.get(side, (None, 'low'))
        
        methods = {
            'address': address_rpp_val,
            'geometric': geometric_rpp,
            'parcel': parcel_rpp
        }
        
        # Count agreements
        values = [v for v in methods.values() if v]
        agreement_count = len(set(values))
        
        # Determine final assignment and confidence
        if address_rpp_val:
            # Address method is primary - check for validation
            if geometric_rpp == address_rpp_val or parcel_rpp == address_rpp_val:
                # Address + at least one other method agree
                final_assignments[side] = {
                    'rpp_area': address_rpp_val,
                    'confidence': 'very_high',
                    'source': 'address_validated',
                    'methods': methods
                }
            else:
                # Address method alone
                final_assignments[side] = {
                    'rpp_area': address_rpp_val,
                    'confidence': 'high',
                    'source': 'address_primary',
                    'methods': methods
                }
        elif agreement_count == 1 and len(values) >= 2:
            # No address, but other methods agree
            agreed_value = values[0]
            final_assignments[side] = {
                'rpp_area': agreed_value,
                'confidence': 'high',
                'source': 'methods_agree',
                'methods': methods
            }
        elif geometric_rpp:
            # Fallback to geometric
            final_assignments[side] = {
                'rpp_area': geometric_rpp,
                'confidence': 'medium',
                'source': 'geometric_only',
                'methods': methods
            }
        elif parcel_rpp:
            # Fallback to parcel
            final_assignments[side] = {
                'rpp_area': parcel_rpp,
                'confidence': parcel_conf,
                'source': 'parcel_only',
                'methods': methods
            }
        else:
            # No data
            final_assignments[side] = {
                'rpp_area': None,
                'confidence': 'low',
                'source': 'no_data',
                'methods': methods
            }
    
    return final_assignments
```

#### Task 2.2: Add BlockSide Mapping to Street Segments

**Objective:** Enrich segments with L/R → N/S/E/W mapping from street cleaning

```python
# Add to ingest_data.py

async def enrich_with_block_side_mapping():
    """
    Add BlockSide mapping from street cleaning data
    
    This provides the authoritative L/R → N/S/E/W mapping needed
    for parcel-based side determination.
    """
    print("\n--- Adding BlockSide Mappings ---")
    
    # Get all street cleaning records
    sweeping = await db.street_cleaning_schedules.find({}).to_list(length=10000)
    
    # Build mapping: {cnn: {'L': 'South', 'R': 'North'}}
    block_side_map = {}
    for record in sweeping:
        cnn = record.get('cnn')
        lr = record.get('cnnrightleft')  # 'L' or 'R'
        cardinal = record.get('blockside')  # 'North', 'South', 'East', 'West'
        
        if cnn and lr and cardinal:
            if cnn not in block_side_map:
                block_side_map[cnn] = {}
            block_side_map[cnn][lr] = cardinal
    
    # Update blockfaces with mapping
    updated_count = 0
    for cnn, mapping in block_side_map.items():
        result = await db.blockfaces.update_many(
            {'cnn': cnn},
            {'$set': {'block_side_mapping': mapping}}
        )
        updated_count += result.modified_count
    
    print(f"Added BlockSide mappings for {len(block_side_map)} CNNs")
    print(f"Updated {updated_count} blockfaces")
    
    # Log sample
    sample_cnn = list(block_side_map.keys())[0] if block_side_map else None
    if sample_cnn:
        print(f"\nSample mapping for CNN {sample_cnn}: {block_side_map[sample_cnn]}")
```

**Acceptance Criteria:**
- [ ] side_determination.py module created
- [ ] All three determination methods implemented
- [ ] BlockSide mappings added to blockfaces
- [ ] Test with CNN 1046000 (should return L=South, R=North)
- [ ] Validate RPP assignments match expected values

---

### Phase 3: Validation & Testing (Priority: MEDIUM)

#### Task 3.1: Create Validation Script

**Objective:** Compare geometric vs parcel-based RPP assignments

```python
# Create backend/validate_rpp_assignments.py

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from side_determination import assign_rpp_with_validation

async def validate_mission_rpp():
    """
    Compare geometric vs parcel-based RPP assignments
    """
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(mongodb_uri)
    db = client.get_default_database()
    
    print("Loading data...")
    blockfaces = await db.blockfaces.find({}).to_list(length=5000)
    rpp_parcels = await db.rpp_parcels.find({}).to_list(length=10000)
    overlay_parcels = await db.overlay_parcels.find({}).to_list(length=10000)
    regulations = await db.parking_regulations.find({}).to_list(length=10000)
    
    print(f"Loaded {len(blockfaces)} blockfaces")
    print(f"Loaded {len(rpp_parcels)} RPP parcels")
    print(f"Loaded {len(overlay_parcels)} overlay parcels")
    print(f"Loaded {len(regulations)} regulations")
    
    discrepancies = []
    high_confidence = 0
    medium_confidence = 0
    low_confidence = 0
    
    for bf in blockfaces:
        cnn = bf.get('cnn')
        if not cnn:
            continue
        
        # Get current RPP from rules
        current_rpp = None
        for rule in bf.get('rules', []):
            if rule.get('type') == 'parking-regulation':
                current_rpp = rule.get('permitArea')
                break
        
        # Get enhanced assignment
        street_segment = {
            'centerlineGeometry': bf.get('geometry'),  # Using blockface geo as proxy
            'block_side_mapping': bf.get('block_side_mapping', {})
        }
        
        # Filter regulations for this CNN
        cnn_regulations = [r for r in regulations if r.get('cnn') == cnn]
        
        enhanced = assign_rpp_with_validation(
            street_segment, cnn_regulations, rpp_parcels, overlay_parcels
        )
        
        side = bf.get('side', 'L')
        enhanced_assignment = enhanced.get(side, {})
        enhanced_rpp = enhanced_assignment.get('rpp_area')
        confidence = enhanced_assignment.get('confidence', 'low')
        
        # Track confidence distribution
        if confidence == 'high':
            high_confidence += 1
        elif confidence == 'medium':
            medium_confidence += 1
        else:
            low_confidence += 1
        
        # Check for discrepancies
        if current_rpp != enhanced_rpp:
            discrepancies.append({
                'cnn': cnn,
                'side': side,
                'street': bf.get('streetName'),
                'current': current_rpp,
                'enhanced': enhanced_rpp,
                'confidence': confidence,
                'methods': enhanced_assignment.get('methods', {})
            })
    
    # Report
    total = len(blockfaces)
    print(f"\n=== Validation Results ===")
    print(f"Total blockfaces: {total}")
    print(f"High confidence: {high_confidence} ({high_confidence/total*100:.1f}%)")
    print(f"Medium confidence: {medium_confidence} ({medium_confidence/total*100:.1f}%)")
    print(f"Low confidence: {low_confidence} ({low_confidence/total*100:.1f}%)")
    print(f"\nDiscrepancies found: {len(discrepancies)} ({len(discrepancies)/total*100:.1f}%)")
    
    if discrepancies:
        print("\nTop 10 Discrepancies:")
        for d in discrepancies[:10]:
            print(f"\n  CNN {d['cnn']} ({d['street']}) - Side {d['side']}")
            print(f"    Current: {d['current']}")
            print(f"    Enhanced: {d['enhanced']} (confidence: {d['confidence']})")
            print(f"    Methods: {d['methods']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(validate_mission_rpp())
```

#### Task 3.2: Spot Check Known Streets

**Test Cases:**
- [ ] CNN 1046000 (20th St between Bryant and York): L=Area W, R=None
- [ ] 5 other Mission streets with known RPP zones
- [ ] Streets on neighborhood boundaries
- [ ] Streets with mixed RPP zones

**Acceptance Criteria:**
- [ ] Validation script runs successfully
- [ ] <5% discrepancy rate
- [ ] >80% high confidence assignments
- [ ] All discrepancies documented and explained

---

### Phase 4: Integration & Deployment (Priority: LOW)

#### Task 4.1: Update Main Ingestion Pipeline

```python
# Update ingest_data.py main()

async def main():
    # ... existing ingestion ...
    
    # NEW: Ingest parcel data
    await ingest_rpp_parcels()
    await ingest_overlay_parcels()
    
    # NEW: Add BlockSide mappings
    await enrich_with_block_side_mapping()
    
    # NEW: Re-process RPP assignments with enhanced logic
    await reprocess_rpp_assignments_with_validation()
```

#### Task 4.2: Update Data Models

```python
# Update backend/models.py

class Blockface(BaseModel):
    id: str
    cnn: Optional[str] = None
    streetName: Optional[str] = None
    side: Optional[str] = None
    geometry: Geometry
    rules: List[Any] = []
    schedules: List[Schedule] = []
    
    # NEW: RPP validation fields
    block_side_mapping: Optional[Dict[str, str]] = None  # {'L': 'South', 'R': 'North'}
    rpp_confidence: Optional[str] = None  # 'high', 'medium', 'low'
    rpp_source: Optional[str] = None  # 'all_agree', 'parcel_validated', 'geometric_only'
    rpp_methods: Optional[Dict[str, str]] = None  # {'geometric': 'W', 'parcel': 'W'}
```

**Acceptance Criteria:**
- [ ] Full re-ingestion completes successfully
- [ ] All blockfaces have confidence scores
- [ ] Frontend displays RPP zones correctly
- [ ] API returns enhanced RPP data

---

## Testing Checklist

### Unit Tests
- [ ] Test [`determine_side_geometric()`](backend/side_determination.py) with known cases
- [ ] Test [`determine_cardinal_side()`](backend/side_determination.py) with N/S/E/W streets
- [ ] Test [`map_cardinal_to_lr()`](backend/side_determination.py) with BlockSide mappings
- [ ] Test [`determine_side_with_parcels()`](backend/side_determination.py) with sample data
- [ ] Test [`assign_rpp_with_validation()`](backend/side_determination.py) with all scenarios

### Integration Tests
- [ ] Test full ingestion pipeline with all three datasets
- [ ] Test validation script on Mission neighborhood
- [ ] Test API returns correct RPP zones with confidence scores
- [ ] Test spatial queries perform efficiently

### Manual Verification
- [ ] Check CNN 1046000 in database (20th St)
- [ ] Verify 10 random Mission streets
- [ ] Test in frontend map view
- [ ] Verify RPP zones display correctly on both sides

---

## Success Metrics

- **Accuracy**: >95% of RPP assignments match ground truth
- **Coverage**: 100% of Mission/SOMA streets have RPP data
- **Confidence**: >80% of assignments have "high" confidence
- **Performance**: Ingestion completes in <5 minutes
- **Discrepancy Rate**: <5% between geometric and parcel methods

---

## Rollback Plan

If issues arise:
1. Revert to geometric-only method (current implementation)
2. Keep parcel data for manual validation
3. Gradually enable parcel validation per neighborhood
4. Use confidence scores to filter out low-quality assignments

---

## Future Enhancements

- [ ] Expand to other SF neighborhoods (Richmond, Sunset, etc.)
- [ ] Add real-time parcel data updates
- [ ] Machine learning for ambiguous cases
- [ ] User feedback integration for corrections
- [ ] Visual overlay showing RPP zone boundaries
- [ ] Confidence score visualization in frontend

---

## Dataset References

### Primary Datasets

1. **Active Streets** (3psu-pn9h) ⭐⭐⭐ **PRIMARY FOR ADDRESS METHOD**
   - Current implementation: [`ingest_data.py:119-139`](backend/ingest_data.py:119-139)
   - **Key Fields for RPP:**
     - `lf_fadd`, `lf_toadd`: Left side address range
     - `rt_fadd`, `rt_toadd`: Right side address range
     - `cnn`: Street segment identifier
     - `streetname`: Street name
   - Purpose: Address range matching (most reliable method)

2. **RPP Eligibility Parcels** (i886-hxz9) ⭐⭐⭐ **PRIMARY FOR ADDRESS METHOD**
   - Status: Not yet implemented
   - **Key Fields:**
     - `from_st`: Street address number
     - `street`: Street name
     - `rppeligib`: RPP area code (W, I, J, K, Q, etc.)
     - `mapblklot`: Parcel ID
   - Purpose: Ground truth RPP codes + address matching

3. **Parking Regulations** (hi6h-neyh) ⭐⭐ **FALLBACK METHOD**
   - Current implementation: [`ingest_data.py:263-365`](backend/ingest_data.py:263-365)
   - Side determination: [`get_side_of_street()`](backend/ingest_data.py:29-74)
   - Purpose: Geometric method when address data unavailable

4. **Parcels with Overlay Attributes** (9grn-xjpx) ⭐ **VALIDATION**
   - Status: Not yet implemented
   - Purpose: Boundary resolution for edge cases

### Supporting Datasets
- **Street Cleaning Schedules** (yhqp-riqs) - BlockSide mappings (L/R → N/S/E/W)
- **Blockface Geometries** (pep9-66vw) - Side-specific geometries

### Method Priority

**Recommended Order:**
1. **Address Range Matching** (Active Streets + RPP Parcels) - Use first
2. **Geometric Analysis** (Parking Regulations) - Use if address unavailable
3. **Overlay Boundaries** (Overlay Parcels) - Use for validation
4. **Spatial Matching** (RPP Parcels + geometry) - Use for validation

---

## Implementation Timeline

### Week 1: Data Ingestion
- Day 1-2: Implement RPP parcels ingestion
- Day 3-4: Implement overlay parcels ingestion
- Day 5: Test and verify data quality

### Week 2: Side Determination
- Day 1-2: Create side_determination.py module
- Day 3-4: Add BlockSide mapping enrichment
- Day 5: Unit testing

### Week 3: Validation & Testing
- Day 1-2: Create validation script
- Day 3-4: Run validation on Mission neighborhood
- Day 5: Document findings and discrepancies

### Week 4: Integration & Deployment
- Day 1-2: Update main ingestion pipeline
- Day 3-4: Update data models and API
- Day 5: Final testing and deployment

---

## Notes

- This plan builds on the existing implementation in [`ingest_data.py`](backend/ingest_data.py)
- **The address-based method is the primary approach** - most direct and reliable
- The current geometric method works well and should be preserved as fallback
- The four-method approach adds validation layers without replacing existing logic
- Confidence scores allow gradual rollout and quality monitoring
- Address matching eliminates geometric ambiguity by using official address assignments