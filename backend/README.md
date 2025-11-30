# Curby Backend - Parking Regulation System

## Overview

Backend system for managing San Francisco parking regulations, street sweeping schedules, and meter data using CNN-based street segments.

## Recent Investigation & Architecture Change

### Summary of Investigation (Nov 2024)

**Problem Identified**: Parking regulations were not being joined to blockfaces during data ingestion.

**Root Causes Found**:
1. Parking regulations lack CNN fields → Required spatial join instead of direct CNN matching
2. Function call bug in side determination (line 324)
3. Incorrect field mapping for regulation data
4. **Critical**: Only 7.4% of streets have blockface geometries from pep9-66vw dataset

**Fixes Implemented**:
- ✅ Spatial join for parking regulations using geometric distance matching
- ✅ Fixed `get_side_of_street()` function call
- ✅ Corrected field mappings (hrlimit, rpparea1, regulation, etc.)
- ✅ Result: 136 parking regulations successfully attached

**Architecture Decision**: 
Migrating from blockface-based to **CNN-based street segment architecture** to achieve 100% coverage.

### Key Documents

1. **[INVESTIGATION_SUMMARY.md](INVESTIGATION_SUMMARY.md)** - Complete investigation findings
2. **[ARCHITECTURE_COMPARISON.md](ARCHITECTURE_COMPARISON.md)** - Synthetic vs CNN-based comparison
3. **[CNN_SEGMENT_IMPLEMENTATION_PLAN.md](CNN_SEGMENT_IMPLEMENTATION_PLAN.md)** - Implementation roadmap
4. **[GEOSPATIAL_JOIN_ANALYSIS.md](GEOSPATIAL_JOIN_ANALYSIS.md)** - Spatial join technical details

## Current Status

- ✅ **Technical Fixes**: Complete
- ✅ **Architecture Planning**: Complete
- ✅ **CNN Segment Implementation**: Phase 1 Complete!
- ✅ **Database Backup**: Complete (pre_cnn_migration_20251127_161321)
- ✅ **Migration Scripts**: Ready to execute
- ⏳ **API Updates**: Pending
- ✅ **Frontend Updates**: Complete (Navigation & Zoom Overhaul)

## Data Sources

- **Active Streets** (3psu-pn9h): Street centerlines with CNN identifiers **+ Address Ranges** (lf_fadd, lf_toadd, rt_fadd, rt_toadd)
  - ✅ **Address ranges now stored in StreetSegment model** (fromAddress, toAddress fields)
  - Enables direct address-based queries and conflict resolution
- **Parking Regulations** (hi6h-neyh): Regulations with geometry and RPP codes (`rpparea1` field) - **PRIMARY source for RPP zones**
- **Street Cleaning** (yhqp-riqs): Sweeping schedules by CNN + side + cardinal directions
- **Parcel Overlay** (9grn-xjpx): Administrative boundaries for conflict resolution (boundary cases only)
- **Blockface Geometries** (pep9-66vw): Side-specific geometries (7.4% coverage)
- **Meters** (8vzz-qzz9, 6cqg-dxku): Parking meter locations and schedules

## Architecture

### Current (Blockface-Based)
```
Blockface {
    cnn: String
    side: "L" | "R"
    geometry: LineString  // Only 7.4% have this
    rules: [...]
}
```

**Problem**: Only 148 of 2,007 CNNs have blockface geometries

### New (CNN-Based Street Segments)
```
StreetSegment {
    cnn: String           // Primary identifier
    side: "L" | "R"       // Which side of street
    streetName: String
    fromStreet: String    // Block boundaries
    toStreet: String
    fromAddress: String   // Starting address (e.g., "3401")
    toAddress: String     // Ending address (e.g., "3449")
    centerlineGeometry: LineString  // Always available
    blockfaceGeometry: LineString | null  // Optional
    rules: [...]
}
```

**Benefits**:
- 100% coverage (4,014 segments = 2,007 CNNs × 2 sides)
- Address ranges stored for each side
- Enables address-based RPP matching and queries

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your MongoDB URI and SFMTA API token

# Run ingestion
bash run_ingestion.sh
```

## Quick Start - Run Migration

### Execute CNN Segment Migration
```bash
cd backend
./run_cnn_segment_migration.sh
```

Or manually:
```bash
python3 ingest_data_cnn_segments.py  # Step 1: Ingest
python3 validate_cnn_segments.py     # Step 2: Validate
```

### Expected Results
- ✅ 34,324 street segments created (2 per CNN for 17,162 Active Streets)
- ✅ 100% coverage achieved (All Active Streets)
- ✅ 22,573 segments with street cleaning data (65.8% of segments)
  - **Note**: This reflects 100% of the data provided in the cleaning dataset.
  - The missing ~34% corresponds to streets not present in the official `yhqp-riqs` source (likely private/non-swept streets).
- ✅ 6,965 segments with parking regulations
- ✅ 4,090 segments with parking meters

## API Endpoints

### Current
- `GET /api/blockfaces` - Get blockfaces with rules
- `GET /api/blockfaces/{id}` - Get specific blockface

### New (CNN Segments - To Be Implemented)
- `GET /api/segments` - Get street segments with rules
- `GET /api/segments/{cnn}/{side}` - Get specific segment

## Testing & Validation

### CNN Segment Validation
```bash
# Comprehensive validation (recommended after migration)
python3 validate_cnn_segments.py
```

### Legacy Testing Scripts
```bash
# Quick database check
python quick_check.py

# Validate CNN mappings
python verify_cnn_mappings.py

# Check for missing blockfaces
python check_missing_blockfaces.py
```

## Development

### Benchmarking
- **`benchmark_api.py`**: Run performance tests against the local API.
- **`BENCHMARK_LOG.md`**: Historical log of performance metrics.

### Key Files
- **`ingest_data_cnn_segments.py`** - New CNN-based ingestion (522 lines)
- **`ingest_data.py`** - Current ingestion with **address-based RPP matching**
- **`models.py`** - Data models (includes StreetSegment)
- **`main.py`** - FastAPI application
- **`validate_cnn_segments.py`** - Validation script (226 lines)
- **`run_cnn_segment_migration.sh`** - Migration runner
- **`RPP_IMPLEMENTATION_PLAN.md`** - Four-method RPP validation strategy

### CNN Segment Ingestion Flow
1. **Load Active Streets** → Create 2 segments per CNN (L & R) + **Store address ranges** (fromAddress, toAddress)
2. **Add Blockface Geometries** → Optional enhancement where available
3. **Match Street Sweeping** → Direct CNN + side match + capture cardinal directions
4. **Match Parking Regulations** → Spatial join with distance analysis (<10m = clear, 10-50m = boundary)
   - Extract RPP zones from regulation's `rpparea1` field
   - Assign to CNN L and/or CNN R based on distance
   - Use Parcel Overlay for boundary conflict resolution
5. **Match Meters** → CNN + location inference
6. **Save to MongoDB** → With proper indexes

**Address Range Storage (Implemented Nov 2024):**
- Left segments: `fromAddress` = `lf_fadd`, `toAddress` = `lf_toadd`
- Right segments: `fromAddress` = `rt_fadd`, `toAddress` = `rt_toadd`
- Example: CNN 799000 Left side stores "3401" to "3449"

### Key Features
- **Spatial join for regulations**: Distance-based CNN L/R assignment with boundary resolution
- **RPP from regulations**: RPP zones come directly from regulation records (`rpparea1`)
- **Address ranges for queries**: Enable address-based lookups and conflict resolution
- **Direct street cleaning join**: 100% coverage via CNN + Side fields
- **Cardinal directions**: User-friendly display (N, S, E, W, etc.)
- **100% coverage**: Every CNN gets L & R segments
- **Dual geometries**: Centerline (required) + blockface (optional)

## Implementation Status

### ✅ Phase 1: Core Implementation (COMPLETE)
- [x] StreetSegment data model
- [x] Segment generation logic (2 per CNN)
- [x] Enhanced parking regulation matching
- [x] Complete ingestion rewrite
- [x] Validation script
- [x] Migration tools

### ⏳ Phase 2: API Updates (Next - 1-2 days)
- [ ] Create `/api/segments` endpoints
- [ ] Update existing endpoints
- [ ] Test with Postman/curl

### ✅ Phase 3: Frontend Updates (COMPLETE)
- [x] Update data types
- [x] Modify API calls
- [x] Update map visualization
- [x] Navigation & Zoom Overhaul (Vicinity, Walking, Neighborhood)

See **[CNN_SEGMENT_IMPLEMENTATION_COMPLETE.md](CNN_SEGMENT_IMPLEMENTATION_COMPLETE.md)** for full implementation summary.

## Contributing

When making changes:
1. Update relevant documentation
2. Run validation scripts
3. Check test coverage
4. Update this README if architecture changes

## License

See main project LICENSE