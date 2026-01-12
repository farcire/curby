# Curby - San Francisco Parking Regulation Decoder

**Status:** ✅ Beta Ready (December 2025) - ⚠️ Known Data Quality Issues
**Coverage:** Mission & SOMA Neighborhoods
**Tech Stack:** React + TypeScript (Frontend) | FastAPI + Python (Backend) | MongoDB Atlas

---

## 🎯 What is Curby?

Curby is a mobile-first Progressive Web App (PWA) that simplifies street parking in San Francisco by providing accurate, real-time parking eligibility based on your location and desired parking duration. It's a **Street Parking Regulation Decoder**, not a "spot finder" - it tells you where you *can* park, not where spots are available.

### Key Features

- 🗺️ **Interactive Map** - Visual display of parking legality for all blockfaces
- 📍 **Smart Geolocation** - Centers on your location with unrestricted city-wide exploration
- ⏱️ **Duration Checking** - Check parking legality for 1-24 hours
- 🔮 **Future Planning** - Check parking up to 7 days in advance
- 📱 **PWA Support** - Installable on mobile devices with offline capabilities
- 🎨 **Three-Tier Zoom** - Optimized viewing at Vicinity, Walking, and Neighborhood levels
- 🚫 **Plain Language Rules** - Clear explanations of parking restrictions

---

## 📂 Project Structure

```
elegant-lynx-play/
├── frontend/          # React + TypeScript PWA
│   ├── src/
│   │   ├── components/   # Map, Navigation, Detail views
│   │   ├── pages/        # Main Index page
│   │   ├── types/        # TypeScript definitions
│   │   └── utils/        # Data fetching, rule engine
│   └── README.md
├── backend/           # FastAPI + Python
│   ├── main.py           # API server
│   ├── models.py         # Data models
│   ├── display_utils.py  # Display formatting
│   ├── ingest_data_cnn_segments.py  # Data ingestion
│   └── README.md
├── archive/           # Historical files
│   ├── investigation_scripts/
│   ├── old_docs/
│   ├── old_ingestion/
│   ├── old_plans/
│   ├── test_scripts/
│   └── validation_scripts/
├── refined-prd.md     # Product Requirements Document
├── Backend-dev-plan.md  # Development plan & status
└── README.md          # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ (Frontend)
- Python 3.13+ (Backend)
- MongoDB Atlas account (Database)
- SFMTA API token (Data source)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with MongoDB URI and SFMTA API token

# Run data ingestion (one-time)
bash run_ingestion.sh

# Start API server
uvicorn main:app --reload --port 8000
```

Backend API runs at: `http://localhost:8000`

---

## 📊 Current Status

### ✅ Completed Features

- **Core Functionality**
  - CNN-based street segment architecture (34,292 segments)
  - Runtime spatial joins for parking regulations
  - Duration-based legality checking (1-24 hours)
  - Future time support (up to 7 days)
  - Plain-language rule explanations

- **Data Integration**
  - Active Streets (geometry + address ranges)
  - Parking Regulations (spatial join with RPP zones)
  - Street Cleaning (direct CNN + side matching with cardinal directions)
  - Parking Meters (CNN-based matching)
  - 100% coverage of Mission District

- **User Experience**
  - PWA with offline app shell
  - Three-tier zoom system
  - Dynamic viewport-based data loading
  - Refined duration slider (1-24h with dynamic emoji indicators)
  - Free parking filter toggle (show all or free-only spots)
  - Unrestricted city-wide exploration
  - User location marker with return button
  - Optimized pill UI with balanced spacing and clear visual hierarchy

- **Performance**
  - <100ms response time for standard queries
  - <1 second for 95% of queries
  - In-memory caching for regulations

### ⚠️ Known Issues

- **Data Quality**: Some street cleaning records missing from SFMTA dataset
  - Example: CNN 961000R (19th St, North side) - Missing Thursday 12AM-6AM schedule
  - Impact: Users may not see all street cleaning restrictions
  - See [`backend/DATA_QUALITY_ISSUES.md`](backend/DATA_QUALITY_ISSUES.md) for details
- **Oversized Vehicle Regulations**: Systematic misinterpretation of oversized vehicle parking regulations
  - Example: CNN 868000 (18th St North, 2700-2798) - Displaying as "time-limit" instead of "No oversize vehicles"
  - Impact: Incorrect display of parking restrictions, but does NOT affect parking eligibility
  - Note: Assumes users have standard vehicles, so these restrictions are informational only
  - See [`backend/OVERSIZED_VEHICLE_FIX_SUMMARY.md`](backend/OVERSIZED_VEHICLE_FIX_SUMMARY.md) for details
  - Investigation: [`backend/18TH_ST_NORTH_PARKING_INVESTIGATION.md`](backend/18TH_ST_NORTH_PARKING_INVESTIGATION.md)
  - Validation tool available: [`backend/validate_street_cleaning_completeness.py`](backend/validate_street_cleaning_completeness.py)

### 🔄 In Progress

- Data quality validation and workarounds

### 📋 Planned Features

- Automated data monitoring ("Listener Mode")
- Expansion beyond Mission/SOMA
- User accounts & saved locations
- Special event parking intelligence
- Voice command interface

---

## 📖 Documentation

### Core Documents

- **[`refined-prd.md`](refined-prd.md)** - Complete Product Requirements Document
- **[`Backend-dev-plan.md`](Backend-dev-plan.md)** - Development plan with sprint details
- **[`frontend/README.md`](frontend/README.md)** - Frontend-specific documentation
- **[`backend/README.md`](backend/README.md)** - Backend architecture & API docs

### Data Quality

- **[`backend/DATA_QUALITY_ISSUES.md`](backend/DATA_QUALITY_ISSUES.md)** - Known data quality issues and workarounds
- **[`backend/cnn_961000_investigation/`](backend/cnn_961000_investigation/)** - Example investigation with findings
- **[`backend/validate_street_cleaning_completeness.py`](backend/validate_street_cleaning_completeness.py)** - Validation tool

### Archive

Historical investigation scripts, old documentation, and deprecated code are organized in the [`archive/`](archive/) directory for reference.

---

## 🏗️ Architecture Overview

### Data Flow

```
SFMTA Data Sources
    ↓
Data Ingestion (ingest_data_cnn_segments.py)
    ↓
MongoDB Atlas (street_segments, parking_regulations)
    ↓
FastAPI Backend (main.py)
    ↓
REST API (/api/v1/blockfaces)
    ↓
React Frontend (MapView, ParkingNavigator)
    ↓
User Interface (Leaflet Map + Controls)
```

### Key Technologies

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- Leaflet + React Leaflet (mapping)
- Tailwind CSS (styling)
- vite-plugin-pwa (PWA support)

**Backend:**
- FastAPI (Python web framework)
- Motor (async MongoDB driver)
- Pydantic (data validation)

**Database:**
- MongoDB Atlas (cloud database)
- Geospatial indexes (2dsphere)
- Collections: street_segments, parking_regulations, error_reports

---

## 🎯 Target Users

1. **SF Residents** - Primary users who rely on street parking
2. **Daily Commuters** - Regular visitors to Mission/SOMA
3. **Gig Workers** - DoorDash, Uber, Instacart drivers
4. **Demo Audience** - Stakeholders and potential investors

---

## 📈 Success Metrics

- ✅ Users can select any point and see parking legality
- ✅ <100ms response time for small queries (300m radius)
- ✅ <1s response time for medium queries (1000m radius)
- ✅ Complete blockface coverage for Mission & SOMA
- ✅ Users can report data errors

---

## 🤝 Contributing

This is currently a private project. For questions or collaboration inquiries, please contact the project maintainer.

---

## 📝 License

See LICENSE file for details.

---

## 🔗 Related Resources

- [SFMTA Open Data Portal](https://data.sfgov.org/)
- [Active Streets Dataset](https://data.sfgov.org/Transportation/Active-Streets/3psu-pn9h)
- [Parking Regulations Dataset](https://data.sfgov.org/Transportation/Parking-Regulations/hi6h-neyh)
- [Street Cleaning Dataset](https://data.sfgov.org/Transportation/Street-Cleaning/yhqp-riqs)

---

## ⚠️ Important Notes

### Data Quality Disclaimer

This application relies on publicly available SFMTA datasets. Investigation has revealed that some street cleaning records are missing from the source data, which may result in incomplete parking restriction information. We are actively working with SFMTA to address these issues and have implemented validation tools to identify affected areas.

For the most accurate parking information, always verify with posted street signs.

---

**Last Updated:** December 5, 2025
**Version:** Beta 1.0
**Project Status:** Ready for Beta Testing (with known data quality issues documented)