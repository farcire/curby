# Backend Development Plan: Curby Parking App

### 1️⃣ Executive Summary
- **Current Status:** Core backend API, data ingestion (S0-S2), and Map geometry refactoring are complete. **Runtime Spatial Join (S4.1)** has been implemented to merge non-metered parking regulations with blockfaces dynamically.
- **Next Phase:** Focus shifts to **S3 (PWA Implementation)** and refining **S4.2 (Future Legality Logic)**.
- **Constraints:** FastAPI (Python 3.13), MongoDB Atlas (Motor), No Docker, Single Branch (`main`), Manual Testing.
- **New Requirement:** Architecture must support PWA (Service Workers, Manifest) and prioritize cost-efficiency (Leaflet/OSM).

---

### 2️⃣ In-Scope & Success Criteria
- **In-Scope:**
  - PWA configuration (Manifest, Service Worker, Splash Screens).
  - Short-term future legality checking (backend logic).
  - Serve validated `blockfaces` data via geospatial API (DONE).
  - Connect Frontend `MapView` to real backend data (DONE).
  - Implement Error Reporting endpoint (DONE).
- **Success Criteria:**
  - App is installable on iOS/Android (Add to Home Screen).
  - App loads offline (App Shell).
  - Users can check parking legality for future times (e.g., "Tomorrow at 10 AM").
  - `GET /api/v1/blockfaces` returns live geospatial data (DONE).
  - **Map dynamically resizes and updates data as user changes radius.**
  - **UI terminology reflects "Regulation Decoding" instead of "Spot Finding".**

---

### 3️⃣ API Design
- **Base path:** `/api/v1`

- **Endpoint 1: Get Blockfaces by Location**
  - **Method:** `GET /blockfaces`
  - **Query Params:** `lat` (float), `lng` (float), `radius_meters` (int)
  - **Response:** `List[Blockface]`
  - **Logic:** Query MongoDB `blockfaces` collection using `$near` or `$geoWithin` on the `geometry` field.

- **Endpoint 2: Create Error Report**
  - **Method:** `POST /error-reports`
  - **Body:** `{ "blockfaceId": "string", "description": "string" }`
  - **Response:** `{ "id": "string", "status": "received" }`

---

### 4️⃣ Data Model (MongoDB Atlas)
- **Collection: `blockfaces`** (Populated by `ingest_data.py` using Active Streets geometry)
- **Index:** **`2dsphere` index exists on `geometry` field.**
- **Schema:**
  ```json
  {
    "id": "string", // CNN
    "streetName": "string",
    "side": "string",
    "geometry": { "type": "LineString", "coordinates": [...] }, // Sourced from Active Streets
    "rules": [],
    "schedules": []
  }
  ```

- **Collection: `error_reports`**
  - **Schema:**
    ```json
    {
      "blockfaceId": "string",
      "description": "string",
      "createdAt": "date",
      "status": "new"
    }
    ```

---

### 5️⃣ Frontend Audit & Feature Map
- **Map View (`MapView.tsx`) & Navigator (`ParkingNavigator.tsx`):**
  - **Action:** Switch data fetching from local mock file to `GET /api/v1/blockfaces`.
  - **Requirement:** Map viewport must automatically fit the bounds of the selected radius.
  - **Requirement:** Data fetching must trigger on radius change (debounced).
  - **Requirement:** Update loading states to say "Decoding regulations..." instead of "Finding spots...".
  - **Validation:** Visual check of map markers/lines matching the new data and dynamic resizing.

- **Error Reporting (`BlockfaceDetail.tsx`):**
  - **Action:** Wire up submit button to `POST /api/v1/error-reports`.

---

### 9️⃣ Testing Strategy (Manual via Frontend)
- **Primary Method:** Browser interaction.
- **Verification:**
  - Network tab inspection (confirm API calls).
  - Visual verification (map loads correct data).
  - Database verification (Atlas UI to confirm writes).

---

### 🔟 Dynamic Sprint Plan

---

### ✅ S0 – Environment Setup (COMPLETED)
- **Status:** Done.
- **Artifacts:** `main.py` created, MongoDB connected, `ingest_data.py` validated.

---

### ✅ S1 – API Implementation & Frontend Integration (COMPLETED)
- **Status:** Done.
- **Artifacts:** `GET /blockfaces` active, Frontend connected.

---

### ✅ S2 – Error Reporting & Automation (COMPLETED)
- **Status:** Done.
- **Artifacts:** `POST /error-reports` implemented, `frontend` connected, `run_ingestion.sh` created.

---

### ✅ S3 – Progressive Web App (PWA) & UI Overhaul (COMPLETED)

**Context:** To support the "Mobile-First" requirement without an app store, we must make the web app installable. Additionally, a major UI overhaul was requested to simplify the user experience.

- **Objectives:**
  - Configure PWA manifest and assets.
  - Implement Service Worker for offline app shell loading.
  - Ensure mobile viewport settings prevent accidental scaling.
  - **New:** Remove Radius Slider, implement Dynamic Map View, and add Duration Slider.

- **Tasks (Completed):**
  - Configured `vite-plugin-pwa` with manifest and icons.
  - Implemented dynamic data fetching based on map viewport (`onMapMove`).
  - Restricted map bounds to Mission District.
  - Created custom Duration Slider with non-linear scale (1-24h).
  - Refined map visuals (transparent overlays) and loading screen.

---

### ✅ S4 – Runtime Spatial Join & Future Legality (PARTIALLY COMPLETE)

- **Objectives:**
  - **CRITICAL:** Implement runtime spatial join to merge `parking_regulations` (non-metered rules) with `blockfaces`.
  - Enable checking parking for future dates.
  - Polish the "Future" time selector UI.

- **Tasks:**
  - **Task S4.1: Runtime Spatial Join Implementation (COMPLETED)**
    - **Context:** `GET /blockfaces` was missing general regulations (RPP, time limits) because they lived in a separate, non-joined collection.
    - **Action:** Updated backend to perform a parallel `$geoWithin` query on `parking_regulations`.
    - **Logic:** Implemented a distance-based heuristic (Haversine formula) to link regulations to the nearest blockface centroid at runtime.
    - **Result:** Streets now correctly display RPP zones, time limits, and no-parking rules.

  - **Task S4.2: Future Time Logic**
    - Ensure `ruleEngine.ts` correctly handles arbitrary Date objects (not just `new Date()`).
    - **Manual Test Step:** Select a time 24 hours from now where street sweeping occurs. Verify status changes to "Illegal".
    - **User Test Prompt:** "Set the time to a known street sweeping slot tomorrow. Verify the map indicates parking is illegal."

- **Definition of Done:**
  - Users see regulations (not just gray) on non-metered residential streets.
  - Users can plan parking for tomorrow.

---

### 📝 Technical Findings & Implementation Notes

#### Data Quality & Parsing
- **Day Formats:** The SFMTA data contains inconsistent day abbreviations (e.g., "M-F", "Tues", "Thurs", "Daily"). The frontend parser was updated to normalize these variations.
- **Time Formats:** Time data comes in multiple formats (e.g., "900", "1800", "0", "6"). A robust parser was implemented to handle these cases.
- **Rule Types:** Explicit mapping was required to categorize "Time limited", "Tow Away", and "Residential Permit" into internal types (`time-limit`, `tow-away`, `rpp-zone`).

#### Side-of-Street Determination Strategy
- **Dataset:** "Map of Parking Regulations" (`hi6h-neyh`).
- **Finding:** This dataset does not typically contain explicit side codes (e.g., "Even", "Odd", "North"). Instead, it uses **offset geometries**. The lines representing regulations are drawn spatially to the left or right of the street centerline.
- **Solution:** Implemented a Geometric Side Analysis:
  1. Fetch street centerline (Active Streets).
  2. Fetch nearby regulations.
  3. Calculate the **Cross Product** of the regulation geometry's midpoint relative to the street centerline vector.
  4. **Result:**
     - Cross Product > 0: Regulation is on the **Left** side.
     - Cross Product < 0: Regulation is on the **Right** side.
  5. Assign the regulation to the specific Blockface ID (`{cnn}_L` or `{cnn}_R`) rather than the generic street.

#### Runtime Spatial Join Strategy
- **Problem:** Parking regulations (`parking_regulations` collection) are massive and complex to pre-join perfectly during ingestion without a robust spatial database (PostGIS).
- **Solution:** Implemented a "Runtime Spatial Merge" in `get_blockfaces`:
  1. Fetch blockfaces within radius.
  2. Fetch regulations within the same radius (using `$geoWithin`).
  3. Perform the **Geometric Side Analysis** (described above) in real-time or via a caching layer to link regulations to the correct blockface side.
- **Trade-off:** This is an O(N*M) operation in Python, but given the small number of items in a typical viewport (N, M < 100), the performance impact is negligible (<10ms). It avoids a complex and potentially fragile full database spatial join.

#### Dynamic Radius Calculation
- **Context:** The frontend no longer sends a fixed radius from a slider.
- **Solution:** The frontend calculates the distance from the map center to the map corner (NE) to determine the visible radius.
- **API Adjustment:** The `radius_meters` parameter in `GET /blockfaces` is now rounded to an integer by the frontend to prevent 422 validation errors in FastAPI.