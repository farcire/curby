# CNN Master File Design - L/R Entry Architecture

## Executive Summary

Based on analysis of the Active Streets dataset (3psu-pn9h) conducted December 29, 2024, we have confirmed that **100% of active street segments contain address data for BOTH left (L) and right (R) sides**. This finding simplifies the master file design and ensures consistent data structure.

## Analysis Results

### Dataset: Active Streets (3psu-pn9h)
- **Filter Applied**: `active='True' OR active IS NULL`
- **Total Active Segments**: 16,374
- **Segments with BOTH L and R data**: 16,374 (100.0%)
- **Segments with ONLY L data**: 0 (0.0%)
- **Segments with ONLY R data**: 0 (0.0%)
- **Segments with NO address data**: 0 (0.0%)

### Key Finding
Every CNN in the Active Streets dataset has complete address range data for both sides:
- Left side: `lf_fadd` (from) and `lf_toadd` (to) - ODD numbers
- Right side: `rt_fadd` (from) and `rt_toadd` (to) - EVEN numbers

**Reference**: Analysis script at [`analyze_active_streets_sides.py`](analyze_active_streets_sides.py)

## Master File Design

### Structure
The master file will contain **TWO entries for every CNN** - one for the L side and one for the R side.

### Entry Format

```python
{
    # Primary Key
    'id': 'CNN_SIDE',  # e.g., "3285000_L" or "3285000_R"
    
    # CNN Information
    'cnn': 'CNN',      # Base CNN (e.g., "3285000")
    'side': 'L|R',     # Side indicator
    
    # Street Information (duplicated for both L and R)
    'streetname_gc': str,     # Geocoded street name
    'street': str,            # Street name
    'st_type': str,           # ST, AVE, BLVD, etc.
    'f_st': str,              # From cross street
    't_st': str,              # To cross street
    
    # Address Range (side-specific)
    'from_addr': int,         # lf_fadd for L, rt_fadd for R
    'to_addr': int,           # lf_toadd for L, rt_toadd for R
    
    # Geographic Information (duplicated for both L and R)
    'zip_code': str,
    'neighborhood': str,      # nhood field
    'analysis_neighborhood': str,
    'supervisor_district': int,
    
    # Spatial Data (duplicated for both L and R)
    'geometry': LineString,   # line field - CNN centerline geometry
    'length_meters': float,   # calculated from geometry
    
    # Blockface Geometry (NEW - Phase 2A)
    'blockface': {
        'geometry': LineString,  # Actual blockface edge (offset from centerline)
        'geometry_source': 'deterministic|meter_calibrated|synthetic',
        'geometry_confidence': float,  # 0.0-1.0
        'offset_meters': float,  # Distance from centerline (negative=L, positive=R)
        'offset_source': 'measured|calibrated|estimated',
        'blockface_id': str,  # If from pep9-66vw dataset (optional)
        'globalid': str,  # If from pep9-66vw dataset (optional)
        'calibration_meter_count': int,  # Number of meters used for calibration
        'created_at': timestamp,
        'updated_at': timestamp
    },
    
    # Metadata
    'source_dataset': 'active_streets',
    'created_at': timestamp,
    'updated_at': timestamp
}
```

### Example Entries

For CNN 3285000 (Mission St between 18th and 19th):

**Entry 1 - Left Side:**
```python
{
    'id': '3285000_L',
    'cnn': '3285000',
    'side': 'L',
    'streetname_gc': 'MISSION ST',
    'f_st': '18TH ST',
    't_st': '19TH ST',
    'from_addr': 2301,  # ODD numbers
    'to_addr': 2399,
    'zip_code': '94110',
    'neighborhood': 'Mission',
    'supervisor_district': 9,
    'geometry': <LineString>,
    # ... other fields
}
```

**Entry 2 - Right Side:**
```python
{
    'id': '3285000_R',
    'cnn': '3285000',
    'side': 'R',
    'streetname_gc': 'MISSION ST',
    'f_st': '18TH ST',
    't_st': '19TH ST',
    'from_addr': 2300,  # EVEN numbers
    'to_addr': 2398,
    'geometry': <LineString>,
    'zip_code': '94110',
    'neighborhood': 'Mission',
    'supervisor_district': 9,
    'geometry': <LineString>,
    # ... other fields
}
```

## Field Duplication Strategy

### CNN-Level Fields (Same for Both L and R)
These fields are duplicated identically for both sides:
- `streetname_gc`, `street`, `st_type`
- `f_st`, `t_st` (cross streets)
- `zip_code`
- `nhood`, `analysis_neighborhood`
- `supervisor_district`
- `line` (geometry) - LineString for entire segment
- `classcode`, `layer`, `oneway`
- `f_node_cnn`, `t_node_cnn`
- `accepted`, `active`
- `date_added`, `gds_chg_id_add`

### Side-Specific Fields (Different for L and R)
Only these fields differ between L and R entries:
- `from_addr` - `lf_fadd` for L, `rt_fadd` for R
- `to_addr` - `lf_toadd` for L, `rt_toadd` for R

## Implementation

### Generation Logic

```python
def create_master_file_entries(active_streets_record):
    """
    Create both L and R entries for a single CNN from Active Streets.
    Since 100% of records have both sides, always create 2 entries.
    """
    cnn = active_streets_record['cnn']
    
    # CNN-level fields (same for both sides)
    common_fields = {
        'streetname_gc': active_streets_record['streetname_gc'],
        'street': active_streets_record['street'],
        'st_type': active_streets_record['st_type'],
        'f_st': active_streets_record['f_st'],
        't_st': active_streets_record['t_st'],
        'zip_code': active_streets_record['zip_code'],
        'neighborhood': active_streets_record['nhood'],
        'analysis_neighborhood': active_streets_record['analysis_neighborhood'],
        'supervisor_district': active_streets_record['supervisor_district'],
        'geometry': active_streets_record['line'],
        'classcode': active_streets_record['classcode'],
        'layer': active_streets_record['layer'],
        'oneway': active_streets_record['oneway'],
        'f_node_cnn': active_streets_record['f_node_cnn'],
        't_node_cnn': active_streets_record['t_node_cnn'],
        'source_dataset': 'active_streets',
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    # Create L entry
    left_entry = {
        'id': f"{cnn}_L",
        'cnn': cnn,
        'side': 'L',
        'from_addr': active_streets_record['lf_fadd'],
        'to_addr': active_streets_record['lf_toadd'],
        **common_fields
    }
    
    # Create R entry
    right_entry = {
        'id': f"{cnn}_R",
        'cnn': cnn,
        'side': 'R',
        'from_addr': active_streets_record['rt_fadd'],
        'to_addr': active_streets_record['rt_toadd'],
        **common_fields
    }
    
    return [left_entry, right_entry]
```

### Database Schema

```sql
CREATE TABLE cnn_master_reference (
    -- Primary Key
    id VARCHAR PRIMARY KEY,  -- Format: "CNN_SIDE" e.g., "3285000_L"
    
    -- CNN Information
    cnn VARCHAR NOT NULL,
    side CHAR(1) NOT NULL CHECK (side IN ('L', 'R')),
    
    -- Street Information (CNN-level, duplicated)
    streetname_gc VARCHAR NOT NULL,
    street VARCHAR,
    st_type VARCHAR,
    f_st VARCHAR NOT NULL,
    t_st VARCHAR NOT NULL,
    
    -- Address Range (side-specific)
    from_addr INTEGER NOT NULL,
    to_addr INTEGER NOT NULL,
    
    -- Geographic Information (CNN-level, duplicated)
    zip_code VARCHAR,
    neighborhood VARCHAR,
    analysis_neighborhood VARCHAR,
    supervisor_district INTEGER,
    
    -- Spatial Data (CNN-level, duplicated)
    geometry GEOMETRY(LineString, 4326),
    length_meters FLOAT,
    
    -- Additional Attributes (CNN-level, duplicated)
    classcode INTEGER,
    layer VARCHAR,
    oneway CHAR(1),
    f_node_cnn VARCHAR,
    t_node_cnn VARCHAR,
    
    -- Metadata
    source_dataset VARCHAR DEFAULT 'active_streets',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_cnn (cnn),
    INDEX idx_street (streetname_gc),
    INDEX idx_address_range (from_addr, to_addr),
    INDEX idx_neighborhood (neighborhood),
    INDEX idx_supervisor_district (supervisor_district),
    SPATIAL INDEX idx_geometry (geometry)
);
```

## Expected Results

### Master File Statistics
- **Total Entries**: 32,748 (16,374 CNNs × 2 sides)
- **L Entries**: 16,374
- **R Entries**: 16,374
- **Data Completeness**: 100% (no NULL address ranges)
- **Data Consistency**: Perfect (every CNN has both sides)

### Benefits

1. **Simplified Logic**: No conditional entry creation needed
2. **Consistent Structure**: Always 2 entries per CNN
3. **Clean Queries**: No need to check for NULL sides
4. **Easy Validation**: Entry count = CNN count × 2
5. **Predictable Size**: Exact calculation of storage needs
6. **No Data Loss**: Complete representation of street network

## Important Note: One-Sided Data in Other Datasets

While Active Streets has 100% coverage for both sides, **other datasets may have one-sided data**:

### Street Cleaning Dataset
- **15.8% of CNNs** (1,933 out of 12,253) have cleaning schedules on only ONE side
- This is a **data quality issue** in the street cleaning dataset, NOT a structural issue
- The master file will have entries for both sides, but one side may lack cleaning regulations

### Handling One-Sided Regulations
When layering regulations onto the master file:
```python
# Master file always has both L and R entries
master_entry_L = get_master_entry(cnn, 'L')  # Always exists
master_entry_R = get_master_entry(cnn, 'R')  # Always exists

# But regulations may only exist for one side
cleaning_L = get_cleaning_schedule(cnn, 'L')  # May be None
cleaning_R = get_cleaning_schedule(cnn, 'R')  # May be None

# Result: Entry exists but regulation field is NULL/empty
```

## Migration Path - MongoDB Architecture

1. **Phase 1**: MongoDB Collection Setup - ✅ COMPLETE
   - ✅ Created `street_segments` collection (34,324 documents)
   - ✅ Implemented resumable ingestion with checkpoints
   - ✅ All 17,162 CNNs × 2 sides uploaded to MongoDB
   - **Implementation**: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py)
   - **Documentation**: [`MONGODB_COLLECTION_ARCHITECTURE.md`](MONGODB_COLLECTION_ARCHITECTURE.md)

2. **Phase 2A**: Add blockface geometries using meter-calibrated offsets - ✅ COMPLETE
   - ✅ Calibrate offsets from existing MongoDB blockfaces (34,324 samples)
   - ✅ Generate blockface geometries for all CNN L/R entries
   - ✅ Achieve 100% coverage with THREE-PRIORITY system
   - **Implementation**: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 2.5
   - **Documentation**: [`BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md`](BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md)

3. **Phase 2B**: Layer parking meters with base operating schedules - ✅ COMPLETE
   - ✅ Load Parking Meters (8vzz-qzz9) for physical attributes
   - ✅ Load Meter Operating Schedules (6cqg-dxku) for base schedules
   - ✅ Load Special Event Areas (itv4-r6g6) for spatial flagging
   - ✅ Match meters to CNN L/R entries (address-based PRIMARY, CNN fallback)
   - ✅ Attach base schedules to meter records with priority hierarchy
   - ✅ Flag special event meters (~2,400 meters)
   - ✅ Apply meter rates from fwjv-32uk dataset
   - ✅ **Exclude** Meter Policies (qq7v-hds4) - stored separately
   - **Implementation**: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 5.6
   - **Documentation**: [`METER_POLICIES_INTEGRATION_ARCHITECTURE.md`](METER_POLICIES_INTEGRATION_ARCHITECTURE.md)

4. **Phase 3**: Layer street cleaning schedules (handle missing sides gracefully) - ⏭️ PENDING
   - ⏭️ Implement STEP 5.7 in ingestion pipeline
   - ⏭️ Handle asymmetric coverage (15.8% one-sided)
   - ⏭️ Implement HOLIDAY override pattern
   - **Documentation**: [`STREET_CLEANING_INTEGRATION_GUIDE.md`](STREET_CLEANING_INTEGRATION_GUIDE.md)

5. **Phase 4**: Layer other regulations (RPP, time limits, etc.) - ⏭️ PENDING
   - ⏭️ Integrate parking regulations (hi6h-neyh)
   - ⏭️ Apply duration standardization
   - **Module**: [`regulation_normalizer.py`](regulation_normalizer.py)

6. **Phase 5**: Set up automated Meter Policies ingestion (separate collection) - ⏭️ PENDING
   - ⏭️ Create `meter_policies` collection
   - ⏭️ Implement cron job for 3-day updates
   - ⏭️ Filter for active policies only

7. **Phase 6**: Validate completeness and deploy - ⏭️ PENDING
   - ⏭️ Run comprehensive validation
   - ⏭️ Deploy to production

### Phase 2A Details: Blockface Geometry Integration - ✅ IMPLEMENTED

**Implementation Date**: December 30, 2024
**Scripts**:
- [`calibrate_blockface_offsets.py`](calibrate_blockface_offsets.py) - Offset calibration
- [`generate_blockface_geometries.py`](generate_blockface_geometries.py) - Geometry generation

**Approach**: Use parking meters as "ground truth" to learn typical offset distances from CNN centerlines to blockface edges.

**Data Sources**:
- **Metered Blockfaces** (mk27-a5x2) - Provides blockface_id → CNN + side mapping
- **Parking Meters** (8vzz-qzz9) - Provides exact coordinates for ~30,000 meters
- **Active Streets** (3psu-pn9h) - Provides CNN centerline geometries

**Process**:
1. **Calibration**: Calculate perpendicular distance from each meter to its CNN centerline
2. **Analysis**: Aggregate statistics by side (L/R) to learn typical offsets
3. **Generation**: Create parallel lines at calibrated offset for all CNN entries
4. **Validation**: Verify geometry validity and offset reasonableness

**Results**:
- **Calibration Samples**: ~28,000 meters analyzed
- **L Side Offset**: -10.12m median (negative = left of centerline)
- **R Side Offset**: +10.05m median (positive = right of centerline)
- **Coverage**: 99.7% of CNN entries have blockface geometry
- **Confidence**: 0.85 for meter-calibrated geometries

**Benefits**:
- Complete blockface coverage (vs 70-85% with deterministic matching only)
- High accuracy from real-world meter locations
- Enables precise spatial queries for parking edges
- Pre-computed geometries (no runtime calculation)

**Reference**: See [`BLOCKFACE_GEOMETRY_INTEGRATION_GUIDE.md`](BLOCKFACE_GEOMETRY_INTEGRATION_GUIDE.md) for complete implementation details.

### Phase 2B Details: Meter Integration with Base Schedules - ✅ IMPLEMENTED

**Implementation Date**: December 30, 2025
**Script**: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 5.6

**Data Sources**:
- **Primary**: Parking Meters (8vzz-qzz9) - 38,356 meters (30,797 active On Street)
  - Provides: `post_id`, `cap_color`, location, CNN
  - **Inclusion**: ✅ Included in CNN Master (static)
  - **Status**: ✅ IMPLEMENTED
  
- **Base Schedules**: Meter Operating Schedules (6cqg-dxku) - 29,371 postIDs, 72,365 schedules
  - Provides: Base operating schedules (permanent/stable)
  - Fields: `schedule_type`, `days_applied`, `from_time`, `to_time`, `time_limit`, `cap_color`
  - **No temporal fields** - represents baseline
  - **Inclusion**: ✅ Included in CNN Master (static)
  - **Status**: ✅ IMPLEMENTED
  - **Data Quality**: 21.5% of meters lack schedules (6,624 meters) - handled gracefully

- **Special Event Areas**: Special Event Areas (itv4-r6g6)
  - Provides: Geospatial boundaries for special event zones
  - Used for: Flagging meters with dynamic pricing during events
  - **Inclusion**: ✅ Spatial join performed
  - **Status**: ✅ IMPLEMENTED
  - **Result**: ~2,400 meters flagged (7.9% of total)

- **Temporal Modifications**: Meter Policies (qq7v-hds4) - 1,545 postIDs, 50,000 policies
  - Provides: Time-bounded policy modifications
  - Fields: `parkingspaceid`, `startdate`, `enddate`, `revisiondate`, schedules
  - **Current Status**: ALL policies future-dated (start: 2026-01-12)
  - **Inclusion**: ❌ Excluded from CNN Master, store in separate `meter_policies` collection
  - **Status**: ⏭️ PENDING (Phase 5)

**Integration Logic for MongoDB** - ✅ IMPLEMENTED:
```python
# In ingest_data_cnn_segments.py STEP 5.6
# 1. Load meters and match to CNN L/R entries (ADDRESS-BASED PRIMARY)
for meter in parking_meters:
    # Primary: Match by street_num + street_name
    cnn_lr_entry = match_meter_by_address(meter.street_num, meter.street_name)
    
    # Fallback: Match by CNN if address matching fails
    if not cnn_lr_entry:
        cnn_lr_entry = match_meter_by_cnn(meter.cnn)
    
    # 2. Get base operating schedules for this postID
    base_schedules = meter_operating_schedules.get(meter.post_id, [])
    
    # 3. Apply schedule priority hierarchy: TOW > ALTERNATE > OP/FREE/PRE
    prioritized_schedules = prioritize_schedules(base_schedules)
    
    # 4. Check if meter is in special event area (spatial join)
    is_special_event = check_special_event_area(meter.location, special_event_areas)
    
    # 5. Attach to MongoDB document (NO policies here)
    if 'meters' not in cnn_lr_entry:
        cnn_lr_entry['meters'] = []
    
    cnn_lr_entry['meters'].append({
        'postId': meter.post_id,
        'capColor': meter.cap_color,
        'location': meter.location,
        'isSpecialEvent': is_special_event,
        'schedules': [
            {
                'scheduleType': s.schedule_type,  # FREE, PRE, OP, TOW, ALTERNATE
                'daysApplied': s.days_applied,
                'fromTime': s.from_time,
                'toTime': s.to_time,
                'timeLimit': s.time_limit,
                'rate': s.rate,
                'capColor': s.cap_color,
                'priority': s.priority  # 1=TOW, 2=ALTERNATE, 3=OP/FREE/PRE
            }
            for s in prioritized_schedules
        ]
    })
    
    # DO NOT include Meter Policies here - they go in separate collection
```

**Matching Results**:
- Expected match rate: 97-98% (address-based + CNN fallback)
- Special event meters: ~2,400 flagged (7.9%)
- Meters without schedules: 6,624 (21.5%) - handled gracefully

### Phase 5 Details: Automated Meter Policies Ingestion

**Separate Collection Strategy**:
```python
# Automated cron job - runs every 3 days
def ingest_meter_policies_cron():
    """
    Fetch and store active meter policies in separate MongoDB collection.
    Filters for policies where startdate <= TODAY <= enddate.
    """
    all_policies = fetch_meter_policies()  # qq7v-hds4
    
    # Filter for active policies only
    today = datetime.now().date()
    active_policies = [p for p in all_policies
                      if p.startdate <= today <= p.enddate]
    
    # Store in separate collection
    db.meter_policies.delete_many({})
    if active_policies:
        db.meter_policies.insert_many(active_policies)
        db.meter_policies.create_index([("postid", ASCENDING)])
    
    # Currently returns 0 policies (all future-dated until 2026-01-12)
```

**Runtime Query Logic**:
```python
def get_parking_info(location, user_preferences):
    # 1. Always query street_segments collection for base data
    base_data = db.street_segments.find({"location": {"$near": location}})
    
    # 2. Conditional: Only query policies if needed
    has_meters = any(d.get('meter_post_id') for d in base_data)
    user_wants_metered = user_preferences.include_metered_parking
    
    if has_meters and user_wants_metered:
        # Query meter_policies collection
        meter_post_ids = [d['meter_post_id'] for d in base_data]
        active_policies = db.meter_policies.find({
            "postid": {"$in": meter_post_ids}
        })
        
        # Apply policy overrides to base schedules
        final_data = apply_policy_overrides(base_data, active_policies)
    else:
        final_data = base_data
    
    return final_data
```

**Key Points**:
- **street_segments Collection**: Contains meters + base schedules (static, stable)
- **meter_policies Collection**: Separate collection (dynamic, updated every 3 days)
- **Conditional Queries**: Only fetch policies when needed (performance optimization)
- **Zero Cost**: MongoDB free tier + Render cron jobs
- **Future-Ready**: System ready for Jan 2026 when policies activate
- **No Runtime API Calls**: All data in MongoDB

**Reference**: See [`METER_POLICIES_INTEGRATION_ARCHITECTURE.md`](METER_POLICIES_INTEGRATION_ARCHITECTURE.md)

## Validation Checklist

- [ ] Verify entry count = 32,748
- [ ] Verify every CNN has exactly 2 entries (L and R)
- [ ] Verify L entries have ODD address ranges
- [ ] Verify R entries have EVEN address ranges
- [ ] Verify all CNN-level fields are identical for L and R pairs
- [ ] Verify geometry is duplicated correctly
- [ ] Verify no NULL address ranges
- [ ] Verify all entries have source_dataset = 'active_streets'

---

**Document Version:** 1.0  
**Date:** December 29, 2024  
**Analysis Reference:** [`analyze_active_streets_sides.py`](analyze_active_streets_sides.py)  
**Status:** Approved for Implementation