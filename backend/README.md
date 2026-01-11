# Parking Regulation API - Backend

**Production API for San Francisco parking regulations, street sweeping, and meter data.**

## Quick Start
```bash
# Run the API
./run.sh

# Test it works
curl http://localhost:8000/healthz
```

## Project Structure
```
backend/
├── src/                   # Production code (3 files, 2,871 lines)
│   ├── api/              
│   │   ├── main.py       # FastAPI server (419 lines)
│   │   └── models.py     # Pydantic models (117 lines)
│   └── core/
│       └── regulation_normalizer.py  # Business logic (2,335 lines)
├── scripts/               # Utility scripts (174 files)
│   ├── analysis/         # Data analysis (31 files)
│   ├── ingestion/        # Data loading (16 files)
│   ├── maintenance/      # DB operations (33 files)
│   └── utilities/        # Testing & validation (94 files)
├── config/
│   ├── .env             # Environment variables
│   └── requirements.txt # Dependencies
├── docs/                 # 📚 77 documentation files (organized Jan 11, 2026)
│   ├── README.md        # ← DOCUMENTATION NAVIGATION GUIDE
│   ├── current/         # 8 files - Production systems (running NOW)
│   ├── reference/       # 36 files - Guides, specs, status reports
│   ├── completed/       # 14 files - Implementation history
│   ├── investigations/  # 11 files - Research & analysis
│   └── archive/         # 10 files - Obsolete docs
└── tests/                # Tests
```

## API Endpoints

- GET /healthz - Health check
- GET /api/v1/blockfaces - Get parking segments by location
- GET /api/v1/search - Search addresses/intersections  
- POST /api/v1/error-reports - Submit error reports

Performance: <100ms response time for 95% of queries

## Configuration

Create config/.env:

MONGODB_URI=mongodb://localhost:27017/parking_db
CORS_ORIGINS=http://localhost:5173,http://localhost:5174

## Development

Install:
pip install -r config/requirements.txt

Run API:
./run.sh

Run a script:
python scripts/ingestion/build_cnn_master.py

## Documentation

### 📖 New to the Project?

1. **Start here:** [`docs/README.md`](docs/README.md) - Complete documentation navigation guide
2. **Essential reading:** [`docs/current/INDEX.md`](docs/current/INDEX.md) - 8 production system docs
3. **System overview:** [`docs/current/CNN_MASTER_REFERENCE_ARCHITECTURE.md`](docs/current/CNN_MASTER_REFERENCE_ARCHITECTURE.md)
4. **Project context:** [`docs/current/PROJECT_HISTORY.md`](docs/current/PROJECT_HISTORY.md)

### 📚 Documentation Organization (Reorganized Jan 11, 2026)

All 77 markdown files are organized by **content and purpose**:

- **`docs/current/`** (8 files) - Systems running in production NOW
- **`docs/reference/guides/`** (12 files) - How-to guides for current systems
- **`docs/reference/specs/`** (11 files) - Technical specifications  
- **`docs/reference/status/`** (13 files) - Status reports and bug fixes
- **`docs/completed/`** (14 files) - Implementation summaries (historical)
- **`docs/investigations/`** (11 files) - Research and analysis
- **`docs/archive/`** (10 files) - Obsolete docs (40+ days old)

Each directory has an `INDEX.md` to help you navigate.

### 🔍 Quick Links

- **How does ingestion work?** → [`docs/current/INGESTION_REFACTORING_COMPLETE_SUMMARY.md`](docs/current/INGESTION_REFACTORING_COMPLETE_SUMMARY.md)
- **Database schema?** → [`docs/current/MONGODB_COLLECTION_ARCHITECTURE.md`](docs/current/MONGODB_COLLECTION_ARCHITECTURE.md)
- **Parse days/times?** → [`docs/reference/guides/DAY_TIME_NORMALIZATION_GUIDE.md`](docs/reference/guides/DAY_TIME_NORMALIZATION_GUIDE.md)
- **Known issues?** → [`docs/current/DATA_QUALITY_LOG.md`](docs/current/DATA_QUALITY_LOG.md) (updated Jan 7!)

## Next Steps

- Document recurring vs one-time scripts
- Move one-time analysis scripts to archive/
- Add tests in tests/
