# Ingestion Architecture Specification

## Core Principle
**Every dataset item must be matched to one or more CNN L/R segments** using deterministic and geospatial matching.

## Ingestion Order & Matching Logic

### 1. Active Streets (3psu-pn9h) - Foundation
**Creates**: CNN segments (L/R pairs)
**Fields to Keep**:
- CNN (primary key)
- lf_fadd, lf_toadd (left side address range)
- rt_fadd, rt_toadd (right side address range)
- street, st_type
- f_st, t_st (from/to streets)
- f_node_cnn, t_node_cnn
- streetname, streetname_gc
- analysis_neighborhood
- supervisor_district
- Geospatial data (centerline geometry)

**Output**: 34,324 segments (2 per CNN)

---

### 2. Intersections & Permutations
**Datasets**:
- List of Streets and Intersections (pu5n-qu5c)
- Intersection Permutations (jfxm-zeee)

**Matching**: CNN + street_name_1 + street_name_2 + geospatial
**Purpose**: Enable search/navigation with any street order combination
**Fields to Keep**: All intersection data, street name variations

---

### 3. Parking Meters (8vzz-qzz9) - FIRST METER DATASET
**Matching Logic**:
1. Match to CNN via `street_seg_ctrln_id` = Active Streets CNN
2. Determine L/R side using:
   - `street_num` + address ranges (lf_fadd/lf_toadd vs rt_fadd/rt_toadd)
   - `street_name` matched to Active Streets `streetname`

**Fields to Keep**:
- post_id (unique meter identifier)
- on_offstreet_type (filter: ON street only)
- active_meter_flag (filter: M, T, P types only)
- cap_color
- street_name, street_num
- longitude, latitude
- analysis_neighborhood
- supervisor_district
- Geospatial data

**Output**: Each meter now has CNN+side and street address

---

### 4. Blockfaces with Meters (mk27-a5x2)
**Purpose**: Metadata for metered blockfaces
**Matching**:
1. To meters via `blockface_id` (exists in both datasets)
2. To meters via address range: fm_addr_no, to_addr_no, street_name

**Fields to Keep**:
- blockface_id
- fm_addr_no, to_addr_no
- street_name
- analysis_neighborhood
- supervisor_district
- Geospatial data

---

### 5. Blockfaces (pep9-66vw) - Deterministic Match
**Matching**:
1. `sfpark_id` = meter `post_id`
2. `blockface_id` = Blockfaces with Meters `blockface_id`
3. CNN match

**Purpose**: Get actual blockface geometries where available

---

### 6. Synthetic Blockface Generation
**After deterministic matching**:
1. Calculate typical distance from centerline to curb using:
   - Blockfaces with Meters geospatial data
   - Parking Meter centerline data
   - **Result**: 5.55 meters from centerline to curb

2. Generate synthetic blockface for every CNN+side without deterministic match
3. **Output**: Every CNN+side now has:
   - Street number range (to/from)
   - Street name
   - CNN+side
   - Geospatial data (real or synthetic)

---

### 7. Meter Operating Schedules (6cqg-dxku)
**Matching**: `post_id` to meters
**Logic**: Apply existing cap_color + schedule_type logic
**Filter**: Active meters only (T, P, M status)
**Output**: Meters now have operating schedules

---

### 8. Meter Rates (fwjv-32uk)
**Matching**: `post_id` to meters
**Logic**: Apply existing cap_color + schedule_type logic
**Output**: Complete metered parking rules (schedules + rates)

---

### 9. Non-Parking Regulations (hi6h-neyh)
**Matching**: Geospatial matching
**Additional Logic**:
- Synthetically generate RPP Areas based on:
  - RPP fields
  - District fields
  - Neighborhood fields
- Apply fallback matching for unmatched regulations
- Some fallback logic relies on RPP areas

**Output**: Non-metered parking rules attached to CNN+side

---

### 10. Street Sweeping
**Matching**: CNN + side (deterministic)
**Cardinal Direction Sources** (in priority order):
1. Blockfaces with Meters
2. Blockfaces
3. Street Sweeping data
4. Default: L or R if none available

---

### 11. Final street_segments Collection Schema

Each CNN+side document contains:
```javascript
{
  cnn: String,
  side: "L" | "R",
  
  // Geometry
  centerlineGeometry: GeoJSON,
  blockfaceGeometry: GeoJSON,  // real or synthetic
  
  // Address & Location
  fromAddress: String,
  toAddress: String,
  streetName: String,
  streetname_gc: String,
  cardinalDirection: String,  // or "L"/"R" fallback
  
  // Intersections
  fromStreet: String,
  toStreet: String,
  intersections: [{
    street_name_1: String,
    street_name_2: String,
    permutations: [String]  // all valid orderings
  }],
  
  // Administrative
  supervisor_district: [String],  // can be multiple
  analysis_neighborhood: [String],  // can be multiple
  rpp_areas: [String],  // can be multiple, synthetic
  
  // Meters (many per segment)
  meters: [{
    post_id: String,
    cap_color: String,
    active_meter_flag: String,
    street_num: String,
    location: GeoJSON Point,
    schedules: [{  // from operating schedules
      schedule_type: String,
      beginTime: String,
      endTime: String
    }],
    rates: [{  // from meter rates
      rate: Number,
      schedule_type: String
    }]
  }],
  
  // Street Cleaning (many per segment)
  streetCleaningSchedules: [{
    day: String,
    startTime: String,
    endTime: String,
    cardinal: String
  }],
  
  // Non-Meter Parking Rules (many per segment)
  parkingRegulations: [{
    regulation: String,
    type: String,
    days: String,
    hours: String,
    timeLimit: Number,
    permitArea: String
  }]
}
```

## Current Implementation Gaps

1. ❌ Missing: Intersection permutations ingestion
2. ❌ Missing: Meter rates dataset (fwjv-32uk)
3. ❌ Missing: Multiple supervisor_districts/neighborhoods per segment
4. ❌ Missing: Synthetic RPP area generation
5. ❌ Incomplete: Fallback matching for regulations
6. ⚠️  Issue: Meter schedule matching (100% NULL)
7. ⚠️  Issue: Cardinal direction fallback logic

## Priority Fixes

1. **IMMEDIATE**: Fix meter schedule matching (diagnostic run needed)
2. **HIGH**: Add meter rates dataset
3. **HIGH**: Implement intersection permutations
4. **MEDIUM**: Synthetic RPP area generation
5. **MEDIUM**: Multiple district/neighborhood support
6. **LOW**: Enhanced fallback matching