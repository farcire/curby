# Documentation Summary & Quick Reference

**Last Updated:** December 1, 2024  
**Project Status:** ✅ Beta Ready  
**Purpose:** Quick reference guide for picking up development after a break

---

## 📋 Project Overview

**Curby** is a mobile-first PWA that decodes San Francisco parking regulations in real-time. Currently covers Mission & SOMA neighborhoods with 100% data coverage (34,292 street segments).

---

## 🗂️ Documentation Structure

### Root Level Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [`README.md`](README.md) | Main project overview & quick start | ✅ Current |
| [`refined-prd.md`](refined-prd.md) | Complete Product Requirements Document | ✅ Current (v8) |
| [`Backend-dev-plan.md`](Backend-dev-plan.md) | Development plan with sprint details | ✅ Current |
| [`UNIQUE_REGULATIONS_EXTRACTION_PLAN.md`](UNIQUE_REGULATIONS_EXTRACTION_PLAN.md) | AI interpretation system design | 🔄 In Progress |
| [`GEMINI_FREE_TIER_STRATEGY.md`](GEMINI_FREE_TIER_STRATEGY.md) | Cost-efficient LLM processing | 🔄 In Progress |

### Frontend Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| [`frontend/README.md`](frontend/README.md) | Frontend setup & architecture | ✅ Current |
| [`frontend/PRD.md`](frontend/PRD.md) | Frontend-specific PRD | ✅ Current |

### Backend Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| [`backend/README.md`](backend/README.md) | Backend architecture & API docs | ✅ Current |
| [`backend/BENCHMARK_LOG.md`](backend/BENCHMARK_LOG.md) | Performance benchmarks | ✅ Current |

### Archived Documentation

| Location | Contents | Purpose |
|----------|----------|---------|
| [`archive/old_plans/`](archive/old_plans/) | Completed plans & cleanup docs | Historical reference |
| [`archive/old_docs/`](archive/old_docs/) | Historical investigation docs | Development history |
| [`archive/investigation_scripts/`](archive/investigation_scripts/) | One-time analysis scripts | Debugging reference |
| [`archive/old_ingestion/`](archive/old_ingestion/) | Deprecated ingestion scripts | Migration reference |
| [`archive/test_scripts/`](archive/test_scripts/) | Old test scripts | Testing reference |
| [`archive/validation_scripts/`](archive/validation_scripts/) | Validation tools | Quality assurance |

---

## 🎯 Current State (December 2024)

### ✅ Completed Features

**Core Functionality:**
- CNN-based street segment architecture (34,292 segments)
- Runtime spatial joins for parking regulations
- Duration-based legality checking (1-24 hours)
- Future time support (up to 7 days)
- Plain-language rule explanations
- Error reporting system

**Data Integration:**
- Active Streets (geometry + address ranges)
- Parking Regulations (spatial join with RPP zones)
- Street Cleaning (CNN + side matching with cardinal directions)
- Parking Meters (CNN-based matching)
- 100% Mission District coverage

**User Experience:**
- PWA with offline app shell
- Three-tier zoom system (Vicinity, Walking, Neighborhood)
- Dynamic viewport-based data loading
- Duration slider (1-24h with emoji feedback)
- Unrestricted city-wide exploration
- User location marker with return button

**Performance:**
- <100ms response time for standard queries
- <1 second for 95% of queries
- In-memory caching for regulations

### 🔄 In Progress

**AI-Powered Interpretation:**
- Extracting unique regulation combinations (~500)
- Gemini 2.0 Flash integration for natural language processing
- Worker → Judge pipeline for quality assurance
- Cost-efficient processing strategy (free tier)

### 📋 Next Steps

**Immediate (Beta Testing):**
1. Deploy to production (Vercel + Railway/Render)
2. Set up monitoring and error tracking
3. Recruit beta testers from Mission/SOMA
4. Create feedback collection system
5. Monitor performance and user experience

**Short-Term (AI Integration):**
1. Complete unique regulations extraction
2. Process through Gemini 2.0 Flash
3. Create interpretation cache
4. Integrate with API endpoints

**Long-Term (Post-Beta):**
1. Automated data monitoring ("Listener Mode")
2. Expand coverage beyond Mission/SOMA
3. User accounts & saved locations
4. Special event parking intelligence
5. Voice command interface

---

## 🚀 Quick Start Commands

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

### Backend
```bash
cd backend
pip install -r requirements.txt
# Configure .env with MongoDB URI and SFMTA API token
bash run_ingestion.sh  # One-time data ingestion
uvicorn main:app --reload --port 8000
# API at http://localhost:8000
```

### Monitoring
```bash
# Check ingestion status
cd backend && python check_ingestion_status.py

# Validate data
python validate_cnn_segments.py

# Run benchmarks
python benchmark_api.py
```

---

## 📊 Key Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Street Segments | 34,292 | ✅ Complete |
| Mission District Coverage | 100% | ✅ Complete |
| Standard Query Response | <100ms | ✅ Optimized |
| Medium Query Response | <1s | ✅ Optimized |
| PWA Score | 100/100 | ✅ Optimized |
| Database Size | ~50MB | ✅ Efficient |

---

## 🔗 Important Links

### Data Sources
- [SFMTA Open Data Portal](https://data.sfgov.org/)
- [Active Streets Dataset](https://data.sfgov.org/Transportation/Active-Streets/3psu-pn9h)
- [Parking Regulations Dataset](https://data.sfgov.org/Transportation/Parking-Regulations/hi6h-neyh)
- [Street Cleaning Dataset](https://data.sfgov.org/Transportation/Street-Cleaning/yhqp-riqs)

### Development Resources
- [Leaflet Documentation](https://leafletjs.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)

---

## 🗺️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     SFMTA Data Sources                       │
│  (Active Streets, Parking Regs, Street Cleaning, Meters)    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Ingestion (Python)                         │
│         ingest_data_cnn_segments.py                          │
│  • Spatial joins for regulations                             │
│  • CNN-based segment creation                                │
│  • Address range storage                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  MongoDB Atlas                               │
│  Collections: street_segments, parking_regulations,          │
│               error_reports, regulation_interpretations      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                        │
│  • GET /api/v1/blockfaces (geospatial queries)              │
│  • POST /api/v1/error-reports                               │
│  • Runtime spatial joins                                     │
│  • <100ms response time                                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              React Frontend (TypeScript)                     │
│  • Leaflet map with OpenStreetMap tiles                     │
│  • Dynamic viewport-based data loading                       │
│  • PWA with offline support                                  │
│  • Three-tier zoom system                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 File Organization

### Active Development Files

**Root:**
- `README.md` - Main overview
- `refined-prd.md` - Product requirements
- `Backend-dev-plan.md` - Development plan
- `UNIQUE_REGULATIONS_EXTRACTION_PLAN.md` - AI system design
- `GEMINI_FREE_TIER_STRATEGY.md` - LLM cost strategy

**Frontend:**
- `frontend/src/components/` - React components
- `frontend/src/pages/` - Page components
- `frontend/src/types/` - TypeScript definitions
- `frontend/src/utils/` - Utility functions

**Backend:**
- `backend/main.py` - FastAPI server
- `backend/models.py` - Data models
- `backend/ingest_data_cnn_segments.py` - Data ingestion
- `backend/display_utils.py` - Display formatting

### Archived Files

All historical investigation scripts, old documentation, and deprecated code are organized in the `archive/` directory with clear subdirectories for easy reference.

---

## 🎯 Decision Log

### Key Architectural Decisions

1. **CNN-Based Segments** (Nov 2024)
   - Decision: Use CNN (Centerline Network) as primary identifier
   - Rationale: 100% coverage vs 7.4% with blockface geometries
   - Result: 34,292 segments with complete data

2. **Runtime Spatial Joins** (Nov 2024)
   - Decision: Perform spatial joins at query time
   - Rationale: Simpler than pre-computing all joins
   - Result: <100ms performance with flexibility

3. **Gemini 2.0 Flash** (Dec 2024)
   - Decision: Use free tier for regulation interpretation
   - Rationale: $0 cost vs $60-$60k/month for runtime processing
   - Result: One-time 50-minute processing for 500 unique regulations

4. **PWA Architecture** (Nov 2024)
   - Decision: Build as Progressive Web App
   - Rationale: No app store overhead, instant updates
   - Result: Installable on mobile with offline support

---

## 🔍 Troubleshooting Quick Reference

### Common Issues

**Backend not starting:**
```bash
# Check MongoDB connection
echo $MONGODB_URI
# Verify Python version
python --version  # Should be 3.13+
# Reinstall dependencies
pip install -r requirements.txt
```

**Frontend not loading data:**
```bash
# Check API is running
curl http://localhost:8000/api/v1/blockfaces?lat=37.7749&lng=-122.4194&radius_meters=300
# Check browser console for CORS errors
# Verify environment variables
```

**Data ingestion issues:**
```bash
# Check ingestion status
python backend/check_ingestion_status.py
# Re-run ingestion
cd backend && bash run_ingestion.sh
```

---

## 📞 Contact & Support

For questions or issues:
1. Check this documentation first
2. Review archived investigation scripts for similar issues
3. Check git history for context on specific changes
4. Consult the PRD for feature requirements

---

**Remember:** All terminals should be running for full functionality:
- Terminal 1: Backend API (`cd backend && uvicorn main:app --reload --port 8000`)
- Terminal 3: Frontend dev server (`cd frontend && npm run dev`)

**Happy coding! 🚀**