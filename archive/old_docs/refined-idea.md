**App Description**: A performance optimization for the Curby parking app that pre-parses parking regulation text into machine-readable formats during data ingestion. This shifts heavy processing away from the API read-time, enabling instant, client-side filtering and rendering of parking rules based on dynamic user time windows.
**Target Users**: Curby App Users (for speed) and Backend Developers (for maintainability).
**Core Features**:
1. Pre-computation of display strings and address parity during ingestion.
2. Conversion of rule logic (days/times) into integer-based "math-ready" formats during ingestion.
3. Updated API architecture to serve pre-processed data directly ("dumb pipe").
4. Client-side logic to handle dynamic time filtering using the pre-parsed integer data.
**Technical Requirements**: Update `StreetSegment` model, modify `ingest_data_cnn_segments.py` to use `display_utils` and parsing logic, update `main.py` to remove runtime processing.