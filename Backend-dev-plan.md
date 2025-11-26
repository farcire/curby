# Backend Development Plan: Curby Parking App

### 1️⃣ Executive Summary
- **Current Status:** Backend environment is set up (S0 completed). Real data ingestion scripts have been written and data validation is complete.
- **Next Phase:** Focus shifts to **S1 (Core Data Service)** to expose this validated data via API and connect the frontend.
- **Constraints:** FastAPI (Python 3.13), MongoDB Atlas (Motor), No Docker, Single Branch (`main`), Manual Testing.

---

### 2️⃣ In-Scope & Success Criteria
- **In-Scope:**
  - Serve validated `blockfaces` data via geospatial API.
  - Connect Frontend `MapView` to real backend data.
  - Implement Error Reporting endpoint.
  - Formalize data ingestion as a background process.
- **Success Criteria:**
  - `GET /api/v1/blockfaces` returns live geospatial data.
  - Frontend Map renders real blockfaces instead of mock data.
  - Error reports are successfully saved to MongoDB.

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
- **Collection: `blockfaces`** (Populated by existing `ingest_data.py`)
  - **Index:** **Must ensure `2dsphere` index exists on `geometry` field.**
  - **Schema:**
    ```json
    {
      "id": "string",
      "streetName": "string",
      "side": "string",
      "geometry": { "type": "LineString", "coordinates": [...] },
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
- **Map View (`MapView.tsx`):**
  - **Action:** Switch data fetching from local mock file to `GET /api/v1/blockfaces`.
  - **Validation:** Visual check of map markers/lines matching the new data.

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

### 🧩 S1 – API Implementation & Frontend Integration

**Context:** We have validated data in the DB. Now we must serve it.

- **Objectives:**
  - Define Pydantic models matching the ingested data.
  - Ensure MongoDB geospatial index is created.
  - Implement `GET /api/v1/blockfaces` endpoint.
  - Connect Frontend to API.

- **Tasks:**

  - **Task S1.1: Create Models & Ensure Index**
    - Define `Blockface` Pydantic model in `main.py` (or `models.py`).
    - Add a startup event or script to ensuring `db.blockfaces.create_index([("geometry", "2dsphere")])`.
    - **Manual Test Step:** Restart backend. Check MongoDB Atlas "Indexes" tab for `blockfaces` collection. Confirm `geometry_2dsphere` exists.
    - **User Test Prompt:** "Restart the server and check MongoDB Atlas to confirm the 2dsphere index was created on the blockfaces collection."

  - **Task S1.2: Implement GET /blockfaces**
    - Implement endpoint using `find` with `$near` query.
    - **Manual Test Step:** `curl "http://localhost:8000/api/v1/blockfaces?lat=37.76&lng=-122.41&radius_meters=500"` → Returns JSON list.
    - **User Test Prompt:** "Use your browser or curl to hit the /blockfaces endpoint with coordinates. Verify you get a JSON list of blockfaces back."

  - **Task S1.3: Connect Frontend**
    - Modify `frontend/src/components/MapView.tsx` (and potentially `sfmtaDataFetcher.ts` or similar) to fetch from API.
    - Remove reliance on `mockBlockfaces.ts` for the main map view.
    - **Manual Test Step:** Open App. Pan map. Check Network tab for `/blockfaces` calls. Verify lines appear on map.
    - **User Test Prompt:** "Open the frontend. Pan the map. verify in the Network tab that requests are going to localhost:8000/api/v1/blockfaces and the map is rendering data."

- **Definition of Done:**
  - Frontend displays real parking data from MongoDB via FastAPI.

---

### 🧱 S2 – Error Reporting & Automation

- **Objectives:**
  - Allow users to report data errors.
  - Formalize ingestion script into a scheduled background task (if required) or documented manual process.

- **Tasks:**

  - **Task S2.1: Error Reporting API**
    - Implement `POST /error-reports`.
    - **Manual Test Step:** Send POST request via Postman. Check `error_reports` collection in Atlas.
    - **User Test Prompt:** "Send a test POST to /error-reports. Check MongoDB to confirm the document was created."

  - **Task S2.2: Frontend Error Wiring**
    - Connect "Report Issue" button in UI to the API.
    - **Manual Test Step:** Click "Report" in UI. Submit. Check DB.
    - **User Test Prompt:** "Submit an error report through the app UI and confirm it appears in the database."

- **Definition of Done:**
  - User feedback loop is functional.