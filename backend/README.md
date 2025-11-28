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
- 🔄 **Migration to CNN Segments**: In Progress
- ⏳ **Database Backup**: Pending
- ⏳ **Full Implementation**: Starting

## Data Sources

- **Active Streets** (3psu-pn9h): Street centerlines with CNN identifiers
- **Street Cleaning** (yhqp-riqs): Sweeping schedules by CNN + side
- **Parking Regulations** (hi6h-neyh): Regulations with geometry only
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
    centerlineGeometry: LineString  // Always available
    blockfaceGeometry: LineString | null  // Optional
    rules: [...]
}
```

**Benefit**: 100% coverage (4,014 segments = 2,007 CNNs × 2 sides)

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

## API Endpoints

### Current
- `GET /api/blockfaces` - Get blockfaces with rules
- `GET /api/blockfaces/{id}` - Get specific blockface

### Planned (CNN Segments)
- `GET /api/segments` - Get street segments with rules
- `GET /api/segments/{cnn}/{side}` - Get specific segment

## Testing

```bash
# Quick database check
python quick_check.py

# Validate CNN mappings
python verify_cnn_mappings.py

# Check for missing blockfaces
python check_missing_blockfaces.py
```

## Development

### Key Files
- `ingest_data.py` - Main data ingestion script
- `models.py` - Data models
- `main.py` - FastAPI application

### Ingestion Flow
1. Load Active Streets (centerlines + CNN)
2. Create segments for each CNN (L & R)
3. Match street sweeping via CNN + side (direct)
4. Match parking regulations via spatial + side (complex)
5. Match meters via CNN + location
6. Save to MongoDB

## Migration Plan

See [CNN_SEGMENT_IMPLEMENTATION_PLAN.md](CNN_SEGMENT_IMPLEMENTATION_PLAN.md) for detailed migration steps.

**Timeline**: 5-7 days
- Days 1-2: Core data model implementation
- Days 3-4: Enhanced parking regulation matching
- Day 5: Testing & validation
- Days 6-7: API & frontend updates

## Contributing

When making changes:
1. Update relevant documentation
2. Run validation scripts
3. Check test coverage
4. Update this README if architecture changes

## License

See main project LICENSE