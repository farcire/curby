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
├── docs/                 # Documentation
│   └── PROJECT_HISTORY.md  # Full project history
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

See docs/PROJECT_HISTORY.md for complete project context, investigation findings, and architecture decisions.

## Next Steps

- Document recurring vs one-time scripts
- Move one-time analysis scripts to archive/
- Add tests in tests/
