# Mobile PWA & Map Refactoring Plan (Zero-Cost / Public Domain)

## 1. Mobile Experience (PWA)
Transform the application into an installable, app-like experience using standard, free web technologies.

### Tasks
- [ ] **Create Web App Manifest** (`public/manifest.json`)
    - Define app name ("Curby"), theme color (`#8b5cf6`), and display mode (`standalone`).
- [ ] **Add App Icons**
    - Generate icons (192x192, 512x512) and place in `public/icons/`.
- [ ] **Update HTML Meta Tags** (`index.html`)
    - Add `apple-mobile-web-app-capable`.
    - Set `theme-color` to match the brand.
- [ ] **Configure Vite PWA Plugin**
    - Install `vite-plugin-pwa` to generate a Service Worker for offline capabilities and caching.
- [ ] **Mobile UI Polish**
    - Ensure buttons are large enough for touch (44px+).
    - Prevent zooming on input focus if necessary.

## 2. Map Geometry Refactoring
**Goal:** Fix the "straight line" overlays to follow street curvature using **only free and public domain resources**.

**Selected Stack:**
- **Map Engine:** Leaflet (Free, Open Source) - *Already in use*.
- **Map Tiles:** OpenStreetMap (Free, Open Data) - *Already in use*.
- **Geometry Data:** SFMTA `Streets` Dataset (Public Domain) - *To be integrated*.

### Tasks
- [x] **Verify `streets` Geometry**
    - Inspect the `streets` collection in MongoDB to confirm it contains detailed `LineString` coordinates (actual curves of the street).
- [x] **Update Backend Ingestion (`ingest_data.py`)**
    - Modify the ingestion script to perform a "join" between the `blockfaces` dataset (parking rules) and the `streets` dataset (physical geometry).
    - Use the `cnn` (Centerline Network Number) or Street Name + Block Number as the join key.
    - **Result:** Each blockface record in the database will now contain the high-fidelity geometry from the `streets` dataset instead of the simplified start/end points.
- [x] **Backend API Verification**
    - Verify `/api/v1/blockfaces` returns the new detailed geometry.
- [x] **Frontend Update**
    - No major changes needed in `MapView.tsx`. Leaflet will automatically render the detailed `LineString` provided by the API, resulting in curved lines that match the street map.

## 3. Data Accuracy & Rules Integration
**Goal:** Ensure all parking rules (meters, RPP, sweeping, time limits) are correctly displayed and interpreted.

### Tasks
- [x] **Implement Runtime Spatial Join**
    - Modify `GET /blockfaces` to fetch and merge `parking_regulations` dynamically.
- [x] **Improve Data Parsing**
    - Update frontend parser to handle various day/time formats ("M-F", "900", etc.).
- [x] **Enhance Rule Engine**
    - Increase time check resolution to 5 minutes to catch short duration restrictions.