# Step 2: Fix Map Geometry & Ingest Regulations - Detailed Plan

## 1. Goal
The current system renders streets as single centerlines. We need to split each street into two distinct "Blockfaces" (Left and Right sides) to accurately visualize parking availability and map parking regulations to the correct side of the street.

## 2. Technical Implementation

### A. Blockface Splitting (Active Streets)
**File:** `backend/ingest_data.py`

We will modify the ingestion process for the Active Streets dataset (`3psu-pn9h`) to generate two records for every street segment.

1.  **Geometry Utilities:**
    *   Implement `calculate_bearing(coords)`: Determines the direction of the street line.
    *   Implement `get_cardinal_side(bearing, side_code)`: Maps 'L'/'R' to 'North'/'South'/'East'/'West'.
    *   Implement `offset_polygon(coords, distance, side)`: *Optional visualization helper, but likely we will keep using the original geometry for the backend and let the frontend handle the visual offset, OR we can generate offset geometries now for better spatial joining precision.* **Decision:** We will stick to the original geometry for the DB record but use the logic to assign correct Cardinal Direction labels. The Spatial Join (below) will be distance-based.

2.  **Ingestion Logic:**
    *   For each Active Street record (CNN):
        *   **Create Record 1 (Right):**
            *   `_id`: `{cnn}_R`
            *   `cnn`: `{cnn}`
            *   `side`: "North", "South", etc. (Calculated)
            *   `side_code`: "R"
            *   `geometry`: Original LineString
        *   **Create Record 2 (Left):**
            *   `_id`: `{cnn}_L`
            *   `cnn`: `{cnn}`
            *   `side`: "Opposite Cardinal"
            *   `side_code`: "L"
            *   `geometry`: Original LineString

### B. Regulation Spatial Join (Ingestion Time)
**File:** `backend/ingest_data.py` (New Section)

We will ingest the **Non-Metered Parking Regulations** dataset (`hi6h-neyh`) and link it to our new Blockfaces.

**Key Finding:** The `hi6h-neyh` dataset uses **spatially offset geometries** (lines drawn to the side of the centerline) to indicate side-of-street applicability.

1.  **Fetch Data:** Download the full dataset (geoJSON/JSON).
2.  **Spatial Indexing:** Create an in-memory R-Tree (using `rtree` or simplified bounding box check if deps are restricted) of all Active Street CNNs.
3.  **Join Logic:**
    *   For each Regulation Record:
        *   Extract its Geometry (`shape`).
        *   Find the **nearest Active Street CNN** geometry.
        *   **Determine Side (Confirmed Approach):**
            *   Calculate the **Cross Product** of the vector from the Street Centerline start to the Regulation Midpoint, relative to the Street Direction vector.
            *   If result > 0: Assign to **Left** Blockface (`{cnn}_L`).
            *   If result < 0: Assign to **Right** Blockface (`{cnn}_R`).
        *   **Link:** Add the regulation rule to the corresponding Blockface.

### C. Frontend Updates
**File:** `frontend/src/components/MapView.tsx`

1.  **Refine Rendering:**
    *   Ensure the `Blockface` type correctly handles the new ID format.
    *   The existing offset logic in `MapView` is good, but we need to verify it aligns with our new backend `side` labels.
    *   Update tooltip/click handlers to show the specific rules for that side.

## 3. Execution Checklist

- [ ] **Install Dependencies:** `shapely` (for robust geometric operations) and `rtree` (if system allows, otherwise basic distance check).
- [ ] **Update Backend Models:** Ensure `Blockface` schema supports the split.
- [ ] **Refactor `ingest_data.py`:**
    - [ ] Add `calculate_bearing` & `get_cardinal_side`.
    - [ ] Update Active Streets loop to emit 2x records.
    - [ ] Add "Non-Metered Regulations" ingestion loop.
    - [ ] Implement Spatial Matcher (Regulation -> Street -> Side).
- [ ] **Run Ingestion:** Re-populate the database.
- [ ] **Verify:** Check Mongo for `_L` and `_R` records and populated `rules` arrays.