# Master CNN Join Database Design

## Overview
A comprehensive master join database that maps CNN (Centerline Network) identifiers to all related street segment information, enabling fast lookups and eliminating the need for repeated spatial joins.

## Problem Statement
Currently, we need to:
1. Query multiple datasets to get complete street segment information
2. Perform spatial joins at runtime to determine cardinal directions
3. Map L/R designations to user-friendly labels (cardinal directions or address ranges)
4. Join across multiple collections for each API request

## Solution: Master CNN Join Database

### Collection Name
`cnn_master_join`

### Purpose
- **Single source of truth** for all CNN-related metadata
- **Pre-computed joins** from all SFMTA datasets
- **Fast lookups** by CNN, address, location, or geometry
- **Cached static data** that rarely changes

## Schema Design

```javascript
{
  // Primary Identifiers
  "_id": ObjectId,
  "cnn": "1234000",                    // Primary CNN identifier
  "cnn_left": "1234000_L",             // Composite key for left side
  "cnn_right": "1234000_R",            // Composite key for right side
  
  // Street Information
  "street_name": "18TH ST",
  "from_street": "York St",
  "to_street": "Bryant St",
  "street_type": "ST",                 // ST, AVE, BLVD, etc.
  "zip_code": "94110",
  
  // Left Side (Odd Addresses)
  "left_side": {
    "side_code": "L",
    "cardinal_direction": "N",         // N, S, E, W, NE, NW, SE, SW
    "from_address": "3401",            // Starting odd address
    "to_address": "3449",              // Ending odd address
    "blockface_id": "GlobalID-123",    // From blockface geometries
    "geometry": {                      // GeoJSON LineString
      "type": "LineString",
      "coordinates": [[lng, lat], ...]
    },
    "centroid": {
      "type": "Point",
      "coordinates": [lng, lat]
    }
  },
  
  // Right Side (Even Addresses)
  "right_side": {
    "side_code": "R",
    "cardinal_direction": "S",         // Opposite of left side typically
    "from_address": "3400",            // Starting even address
    "to_address": "3448",              // Ending even address
    "blockface_id": "GlobalID-456",
    "geometry": {
      "type": "LineString",
      "coordinates": [[lng, lat], ...]
    },
    "centroid": {
      "type": "Point",
      "coordinates": [lng, lat]
    }
  },
  
  // Centerline (Reference)
  "centerline_geometry": {
    "type": "LineString",
    "coordinates": [[lng, lat], ...]
  },
  
  // Administrative Boundaries
  "neighborhood": "Mission",
  "analysis_neighborhood": "Mission",
  "supervisor_district": "9",
  "block_id": "0123",
  
  // Metadata
  "data_sources": [
    "active_streets",
    "blockface_geometries", 
    "street_cleaning"
  ],
  "created_at": ISODate("2025-11-28T00:00:00Z"),
  "updated_at": ISODate("2025-11-28T00:00:00Z"),
  "version": 1
}
```

## Data Sources & Mapping

### 1. Active Streets (3psu-pn9h) - Foundation
**Provides:**
- CNN identifier
- Street name
- From/To streets
- Address ranges (lf_fadd, lf_toadd, rt_fadd, rt_toadd)
- Centerline geometry
- Zip code

**Mapping:**
```python
{
  "cnn": row["cnn"],
  "street_name": row["streetname"],
  "from_street": row["from_street"],
  "to_street": row["to_street"],
  "left_side.from_address": row["lf_fadd"],
  "left_side.to_address": row["lf_toadd"],
  "right_side.from_address": row["rt_fadd"],
  "right_side.to_address": row["rt_toadd"],
  "centerline_geometry": row["line"],
  "zip_code": row["zip_code"]
}
```

### 2. Blockface Geometries (pep9-66vw) - Precise Geometry
**Provides:**
- GlobalID for each blockface
- Precise curb-side geometry (offset from centerline)
- Side determination via geometric analysis

**Mapping:**
```python
# Determine side using geometric cross product
side = get_side_of_street(centerline_geo, blockface_geo)

if side == 'L':
  "left_side.blockface_id": row["globalid"]
  "left_side.geometry": row["shape"]
elif side == 'R':
  "right_side.blockface_id": row["globalid"]
  "right_side.geometry": row["shape"]
```

### 3. Street Cleaning (yhqp-riqs) - Cardinal Directions
**Provides:**
- Cardinal direction (blockside field: N, S, E, W, NE, NW, SE, SW)
- Side indicator (cnnrightleft: L or R)

**Mapping:**
```python
side = row["cnnrightleft"]  # L or R
cardinal = row["blockside"]  # N, S, E, W, etc.

if side == 'L':
  "left_side.cardinal_direction": cardinal
elif side == 'R':
  "right_side.cardinal_direction": cardinal
```

### 4. Additional Datasets (Optional Enhancement)
- **EAS Addresses (dxjs-vqsy)**: Additional address validation
- **Street Intersections (fqt9-tat9)**: Intersection metadata
- **Supervisor Districts**: Administrative boundaries

## Indexes

```javascript
// Primary lookup by CNN
db.cnn_master_join.createIndex({ "cnn": 1 }, { unique: true })

// Lookup by composite keys
db.cnn_master_join.createIndex({ "cnn_left": 1 })
db.cnn_master_join.createIndex({ "cnn_right": 1 })

// Geospatial indexes for proximity queries
db.cnn_master_join.createIndex({ "left_side.geometry": "2dsphere" })
db.cnn_master_join.createIndex({ "right_side.geometry": "2dsphere" })
db.cnn_master_join.createIndex({ "left_side.centroid": "2dsphere" })
db.cnn_master_join.createIndex({ "right_side.centroid": "2dsphere" })

// Text search
db.cnn_master_join.createIndex({ 
  "street_name": "text",
  "from_street": "text",
  "to_street": "text"
})

// Administrative lookups
db.cnn_master_join.createIndex({ "neighborhood": 1 })
db.cnn_master_join.createIndex({ "zip_code": 1 })
db.cnn_master_join.createIndex({ "supervisor_district": 1 })

// Address range lookups
db.cnn_master_join.createIndex({ "left_side.from_address": 1 })
db.cnn_master_join.createIndex({ "right_side.from_address": 1 })
```

## Query Examples

### 1. Lookup by CNN
```javascript
db.cnn_master_join.findOne({ cnn: "1234000" })
```

### 2. Lookup by CNN + Side
```javascript
db.cnn_master_join.findOne({ cnn_left: "1234000_L" })
```

### 3. Find by Address
```javascript
db.cnn_master_join.find({
  street_name: "18TH ST",
  $or: [
    { "left_side.from_address": { $lte: "3425" }, "left_side.to_address": { $gte: "3425" } },
    { "right_side.from_address": { $lte: "3424" }, "right_side.to_address": { $gte: "3424" } }
  ]
})
```

### 4. Geospatial Proximity
```javascript
db.cnn_master_join.find({
  "left_side.centroid": {
    $near: {
      $geometry: { type: "Point", coordinates: [-122.4087, 37.7604] },
      $maxDistance: 100
    }
  }
})
```

### 5. Find by Neighborhood
```javascript
db.cnn_master_join.find({ neighborhood: "Mission" })
```

## Benefits

### 1. Performance
- **Single query** instead of multiple joins
- **Pre-computed** cardinal directions
- **Indexed lookups** for all common access patterns
- **Cached data** reduces API calls to SFMTA

### 2. User Experience
- Display **"18TH ST (N side)"** instead of **"18TH ST (L)"**
- Show **address ranges**: **"18TH ST (3401-3449)"**
- Combined display: **"18TH ST (N side, 3401-3449)"**

### 3. Maintainability
- **Single source of truth** for CNN metadata
- **Version tracking** for data updates
- **Easy to update** when SFMTA data changes
- **Consistent** across all API endpoints

### 4. Flexibility
- Query by **any field**: CNN, address, location, geometry
- Support **multiple display formats**
- Enable **advanced filtering** and search
- **Extensible** for future data sources

## Implementation Strategy

### Phase 1: Build Master Database
1. Fetch all Active Streets data
2. Fetch all Blockface Geometries
3. Fetch all Street Cleaning data
4. Perform joins and create master records
5. Insert into `cnn_master_join` collection
6. Create indexes

### Phase 2: Update API
1. Modify `/api/v1/blockfaces` to query `cnn_master_join`
2. Return cardinal directions and address ranges
3. Update response format

### Phase 3: Update Frontend
1. Display cardinal directions instead of L/R
2. Show address ranges in popups
3. Update street segment labels

### Phase 4: Caching & Updates
1. Cache master database in memory (Redis optional)
2. Schedule periodic updates (weekly/monthly)
3. Implement version tracking
4. Add data freshness indicators

## Caching Strategy

### Static Data Characteristics
- SFMTA street data changes **infrequently** (quarterly at most)
- CNN identifiers are **stable**
- Address ranges are **fixed**
- Cardinal directions are **permanent**

### Caching Approach

#### 1. Database-Level Caching
```javascript
// MongoDB automatically caches frequently accessed documents
// Our indexes ensure hot data stays in memory
```

#### 2. Application-Level Caching (Optional)
```python
# In-memory cache for most frequently accessed CNNs
from functools import lru_cache

@lru_cache(maxsize=10000)
def get_cnn_data(cnn: str):
    return db.cnn_master_join.find_one({"cnn": cnn})
```

#### 3. CDN/Edge Caching (Future)
```
# Cache API responses at CDN level
Cache-Control: public, max-age=86400  # 24 hours
```

### Update Strategy
1. **Weekly check** for SFMTA data updates
2. **Incremental updates** for changed CNNs only
3. **Version tracking** to detect changes
4. **Graceful rollover** to new data version

## File Structure

```
backend/
├── create_master_cnn_join.py      # Build master database
├── update_master_cnn_join.py      # Incremental updates
├── verify_master_cnn_join.py      # Data quality checks
└── MASTER_CNN_JOIN_DATABASE_DESIGN.md  # This file
```

## Next Steps

1. ✅ Design master database schema
2. ⏭️ Implement `create_master_cnn_join.py`
3. ⏭️ Build and populate master database
4. ⏭️ Update API to use master database
5. ⏭️ Update frontend to display cardinal directions
6. ⏭️ Implement caching strategy
7. ⏭️ Add monitoring and update automation