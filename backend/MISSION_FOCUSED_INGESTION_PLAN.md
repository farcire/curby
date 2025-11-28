# Mission Neighborhood Focused Data Ingestion Plan

## Overview
This plan demonstrates how parking regulations, metered parking, and street cleaning data merge and overlay on active streets and blockfaces specifically for San Francisco's Mission neighborhood.

## Mission Neighborhood Boundaries
- **Primary Zip Code**: 94110
- **Secondary Zip Code**: 94103 (partial coverage)
- **Geographic Bounds**: Roughly 14th St to Cesar Chavez, Mission St to Potrero Ave
- **Characteristics**: Dense urban residential/commercial mix with complex parking rules

---

## Data Layer Architecture

### Layer 1: Active Streets (Foundation)
**Dataset**: `3psu-pn9h` (Active Streets)
**Role**: Primary backbone providing street network structure

```
Active Streets → Creates Base Segments
├── CNN (Centerline Network ID)
├── Street Name
├── Address Ranges (Left: lf_fadd-lf_toadd, Right: rt_fadd-rt_toadd)
├── Centerline Geometry (LineString)
└── Zip Code (for filtering)

Example:
CNN: 1046000
Street: "20TH ST"
Left Side: 3401-3449 (odd numbers)
Right Side: 3400-3448 (even numbers)
Geometry: LineString from Bryant to Florida
```

**Coverage**: 100% of all streets in Mission
**Expected**: ~2,000 CNNs → 4,000 segments (2 per CNN: Left & Right)

---

### Layer 2: Blockface Geometries (Enhancement)
**Dataset**: `pep9-66vw` (Blockface Geometries)
**Role**: Optional side-specific geometry enhancement

```
Blockface Geometries → Enhance Segments with Precise Boundaries
├── CNN_ID (links to Active Streets)
├── GlobalID (unique identifier)
├── Shape (LineString - offset from centerline)
└── Side determination (via geometric analysis)

Merge Logic:
1. Match by CNN_ID
2. Determine L/R side using cross-product analysis
3. Add blockface geometry to appropriate segment
4. Store GlobalID for reference

Example:
CNN: 1046000
GlobalID: {ABC-123-DEF}
Side: L (determined geometrically)
→ Merges into: 1046000-L segment
```

**Coverage**: ~50-60% of segments (optional enhancement)
**Benefit**: More precise curb-side geometry when available

---

### Layer 3: Street Cleaning (Direct Join)
**Dataset**: `yhqp-riqs` (Street Cleaning Schedules)
**Role**: Street sweeping schedules and restrictions

```
Street Cleaning → Direct CNN + Side Join (No Spatial Analysis Needed!)
├── CNN (matches Active Streets)
├── cnnrightleft (L or R - direct side match)
├── weekday (day of week)
├── fromhour / tohour (time window)
├── limits (from/to streets)
└── blockside (cardinal direction: N, S, E, W)

Merge Logic:
FOR EACH cleaning_schedule:
  segment = find_segment(cnn=schedule.cnn, side=schedule.cnnrightleft)
  segment.rules.append({
    type: "street-sweeping",
    day: schedule.weekday,
    startTime: schedule.fromhour,
    endTime: schedule.tohour,
    side: schedule.cnnrightleft
  })

Example:
CNN: 1046000, Side: L
Day: Tuesday
Hours: 8AM-10AM
→ Merges into: 1046000-L segment
→ Result: "No parking Tuesday 8AM-10AM (Street Cleaning)"
```

**Coverage**: ~80% of segments (where street cleaning applies)
**Join Method**: Direct match (CNN + Side) - 100% reliable
**Performance**: Fast - no geometric calculations needed

---

### Layer 4: Parking Regulations (Spatial Join)
**Dataset**: `hi6h-neyh` (Parking Regulations)
**Role**: Time limits, RPP zones, tow-away zones, loading zones

```
Parking Regulations → Spatial + Geometric Side Matching
├── Shape (LineString geometry)
├── regulation (type: "2 HR", "NO PARKING", etc.)
├── hrlimit (time limit in hours)
├── rpparea1/rpparea2 (RPP zone codes)
├── days (days of week)
├── hours (time range)
└── analysis_neighborhood (for filtering)

Merge Logic:
FOR EACH regulation:
  1. Find nearby segments (spatial query within ~50m)
  2. For each nearby segment:
     a. Get centerline geometry
     b. Determine which side regulation is on (geometric analysis)
     c. Match regulation side to segment side
  3. Attach regulation to matching segment

Example:
Regulation: "2 HR PARKING 9AM-6PM MON-SAT"
Location: Near 1046000 centerline
Geometric Analysis: Determines regulation is on LEFT side
→ Merges into: 1046000-L segment
→ Result: "2 hour parking limit Mon-Sat 9AM-6PM"
```

**Coverage**: Varies by area (dense in commercial, sparse in residential)
**Join Method**: Spatial proximity + geometric side determination
**Challenge**: Requires geometric analysis for side matching

---

### Layer 5: Parking Meters (CNN Join + Schedules)
**Dataset**: `8vzz-qzz9` (Parking Meters) + `6cqg-dxku` (Meter Schedules)
**Role**: Metered parking locations and rate schedules

```
Parking Meters → CNN Match + Schedule Lookup
├── street_seg_ctrln_id (CNN)
├── post_id (meter identifier)
├── active_meter_flag
└── location (point geometry)

Meter Schedules → Lookup by post_id
├── post_id (links to meter)
├── beg_time_dt / end_time_dt
├── rate (hourly rate)
└── days_applied

Merge Logic:
1. Build schedule lookup: schedules_by_post[post_id] = [schedules]
2. FOR EACH meter:
     segments = find_segments(cnn=meter.street_seg_ctrln_id)
     schedules = schedules_by_post[meter.post_id]
     FOR EACH segment:
       segment.schedules.append({
         type: "meter",
         postId: meter.post_id,
         active: meter.active_meter_flag,
         schedules: schedules
       })

Example:
Meter Post: MS-1234
CNN: 1046000
Schedules:
  - Mon-Fri 9AM-6PM: $3.00/hr
  - Sat 9AM-6PM: $2.00/hr
→ Merges into: Both 1046000-L and 1046000-R segments
→ Result: "Metered parking $3/hr Mon-Fri 9AM-6PM"
```

**Coverage**: Concentrated in commercial corridors (Mission St, Valencia St, 24th St)
**Join Method**: CNN match (applies to both sides unless meter location is precise)
**Note**: May need refinement for side-specific meter placement

---

## Complete Data Merge Example: 20th Street between Bryant & Florida

### Base Layer (Active Streets)
```
CNN: 1046000
Street: "20TH ST"
From: Bryant St
To: Florida St

LEFT SEGMENT (1046000-L):
  Address Range: 3401-3449 (odd)
  Centerline Geometry: [LineString coordinates]
  
RIGHT SEGMENT (1046000-R):
  Address Range: 3400-3448 (even)
  Centerline Geometry: [LineString coordinates]
```

### + Blockface Geometries (if available)
```
LEFT SEGMENT (1046000-L):
  + Blockface Geometry: [Offset LineString - north side]
  + GlobalID: {ABC-123}
  
RIGHT SEGMENT (1046000-R):
  + Blockface Geometry: [Offset LineString - south side]
  + GlobalID: {DEF-456}
```

### + Street Cleaning
```
LEFT SEGMENT (1046000-L):
  + Street Cleaning:
    - Day: Tuesday
    - Hours: 8AM-10AM
    - Cardinal: N (North side)
    
RIGHT SEGMENT (1046000-R):
  + Street Cleaning:
    - Day: Thursday
    - Hours: 8AM-10AM
    - Cardinal: S (South side)
```

### + Parking Regulations
```
LEFT SEGMENT (1046000-L):
  + Regulation 1:
    - Type: "2 HR PARKING"
    - Hours: 9AM-6PM
    - Days: Mon-Sat
    - Side: L
    
RIGHT SEGMENT (1046000-R):
  + Regulation 1:
    - Type: "2 HR PARKING"
    - Hours: 9AM-6PM
    - Days: Mon-Sat
    - Side: R
```

### + Parking Meters
```
BOTH SEGMENTS:
  + Meter Post: MS-5678
  + Active: Yes
  + Schedules:
    - Mon-Fri 9AM-6PM: $3.00/hr
    - Sat 9AM-6PM: $2.00/hr
    - Sun: Free
```

### Final Merged Result
```json
{
  "id": "1046000-L",
  "cnn": "1046000",
  "side": "L",
  "streetName": "20TH ST",
  "fromStreet": "BRYANT ST",
  "toStreet": "FLORIDA ST",
  "fromAddress": "3401",
  "toAddress": "3449",
  "centerlineGeometry": { "type": "LineString", "coordinates": [...] },
  "blockfaceGeometry": { "type": "LineString", "coordinates": [...] },
  "globalid": "{ABC-123}",
  "cardinalDirection": "N",
  "rules": [
    {
      "type": "street-sweeping",
      "day": "Tuesday",
      "startTime": "08:00",
      "endTime": "10:00",
      "description": "No parking Tuesday 8AM-10AM (Street Cleaning)"
    },
    {
      "type": "parking-regulation",
      "regulation": "2 HR PARKING",
      "timeLimit": "2",
      "days": "Mon-Sat",
      "hours": "9AM-6PM",
      "description": "2 hour parking limit Mon-Sat 9AM-6PM"
    }
  ],
  "schedules": [
    {
      "type": "meter",
      "postId": "MS-5678",
      "active": true,
      "schedules": [
        { "days": "Mon-Fri", "hours": "9AM-6PM", "rate": "$3.00/hr" },
        { "days": "Sat", "hours": "9AM-6PM", "rate": "$2.00/hr" },
        { "days": "Sun", "hours": "All Day", "rate": "Free" }
      ]
    }
  ]
}
```

---

## Visualization of Data Merging

### ASCII Diagram: How Layers Stack
```
Street: 20TH ST (CNN: 1046000)
From: Bryant St → To: Florida St

NORTH SIDE (LEFT - Odd Numbers)
═══════════════════════════════════════════════════════════════
Layer 1: Active Streets
         [3401────────────────────────────────────────3449]
         └─ Address Range (lf_fadd to lf_toadd)

Layer 2: Blockface Geometry (if available)
         [═══════════════════════════════════════════════]
         └─ Precise curb-side geometry (GlobalID: ABC-123)

Layer 3: Street Cleaning
         [TUESDAY 8AM-10AM NO PARKING]
         └─ Direct CNN+Side join (cnnrightleft='L')

Layer 4: Parking Regulations
         [2 HR PARKING MON-SAT 9AM-6PM]
         └─ Spatial join + geometric side match

Layer 5: Parking Meters
         [METER MS-5678: $3/hr Mon-Fri 9AM-6PM]
         └─ CNN match + schedule lookup

═══════════════════════════════════════════════════════════════

SOUTH SIDE (RIGHT - Even Numbers)
═══════════════════════════════════════════════════════════════
Layer 1: Active Streets
         [3400────────────────────────────────────────3448]
         └─ Address Range (rt_fadd to rt_toadd)

Layer 2: Blockface Geometry (if available)
         [═══════════════════════════════════════════════]
         └─ Precise curb-side geometry (GlobalID: DEF-456)

Layer 3: Street Cleaning
         [THURSDAY 8AM-10AM NO PARKING]
         └─ Direct CNN+Side join (cnnrightleft='R')

Layer 4: Parking Regulations
         [2 HR PARKING MON-SAT 9AM-6PM]
         └─ Spatial join + geometric side match

Layer 5: Parking Meters
         [METER MS-5678: $3/hr Mon-Fri 9AM-6PM]
         └─ CNN match + schedule lookup

═══════════════════════════════════════════════════════════════
```

---

## Expected Results for Mission Neighborhood

### Coverage Statistics
- **Total CNNs**: ~2,000
- **Total Segments**: ~4,000 (2 per CNN)
- **With Centerline Geometry**: 100% (4,000)
- **With Blockface Geometry**: ~50-60% (2,000-2,400)
- **With Street Cleaning**: ~80% (3,200)
- **With Parking Regulations**: Varies (dense in commercial areas)
- **With Meters**: Concentrated on major corridors

### Sample Streets Analysis

#### Valencia Street (Commercial Corridor)
- **Segments**: ~40 (20 blocks × 2 sides)
- **Street Cleaning**: 100% coverage
- **Parking Regulations**: Dense (multiple rules per segment)
- **Meters**: Heavy concentration
- **RPP**: Area W (residential sections)

#### Balmy Street (Residential)
- **Segments**: ~8 (4 blocks × 2 sides)
- **Street Cleaning**: 100% coverage
- **Parking Regulations**: Minimal (mostly RPP)
- **Meters**: None
- **RPP**: Area W

#### Mission Street (Major Corridor)
- **Segments**: ~80 (40 blocks × 2 sides)
- **Street Cleaning**: 100% coverage
- **Parking Regulations**: Very dense (commercial restrictions)
- **Meters**: Very heavy concentration
- **RPP**: Mixed (commercial/residential)

---

## Key Insights

### 1. Foundation is Critical
- Active Streets provides 100% coverage
- Without it, we'd have gaps in street network
- Address ranges enable deterministic lookups

### 2. Direct Joins are Reliable
- Street Cleaning: 100% reliable (CNN + Side)
- No geometric analysis needed
- Fast and accurate

### 3. Spatial Joins Require Care
- Parking Regulations: Need geometric side determination
- Tolerance settings matter (~50m works well)
- Side matching is critical for accuracy

### 4. Meters Need Refinement
- Currently apply to both sides of street
- Could be improved with precise meter locations
- Schedule lookup works well

### 5. Data Density Varies
- Commercial corridors: Very dense (all layers)
- Residential streets: Moderate (sweeping + some regs)
- Alleys: Sparse (may only have base layer)

---

## Next Steps

1. **Create Mission-specific ingestion script**
2. **Run ingestion for Mission neighborhood**
3. **Create visualization showing data layer merging**
4. **Generate analysis report with real examples**
5. **Validate data quality and coverage**

---

**Status**: Plan Complete - Ready for Implementation  
**Target**: Mission Neighborhood (Zip 94110, 94103)  
**Expected Duration**: 5-10 minutes for full ingestion  
**Output**: ~4,000 fully merged street segments