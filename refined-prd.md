---
title: Product Requirements Document - REFINED
app: elegant-lynx-play
created: 2025-11-25T07:06:20.848Z
version: 7
source: BA-PRD Agent Refinement
---

# PRODUCT REQUIREMENTS DOCUMENT

## EXECUTIVE SUMMARY

**Product Vision:** Curby simplifies street parking in San Francisco by providing accurate, real-time street parking eligibility based on location and duration. The MVP focuses on the **Mission and SOMA neighborhoods**, powered by a live connection to parking rule databases and a user-driven feedback loop to continuously improve accuracy.

**Core Purpose:** Solve the parking legality problem by providing high-accuracy, plain-language answers to "Can I park here?". It functions as a **Street Parking Regulation Decoder**, not a "spot finder". For the demo, it provides a simulation tool to select any location within the covered area, define a radius, and check parking regulation eligibility for a specified duration.

**Target Users:** 
1. **SF residents who rely on street parking** (Primary)
2. **Daily Commuters**
3. **Gig workers** (DoorDash, Uber, Instacart)
4. **Demo Audience & Stakeholders**

**Key Features:**
- **Progressive Web App (PWA)** (Platform: Mobile-First Web)
- **Demo Location & Radius Selector** (System: Simulation Tool)
- **Interactive map showing real-time parking legality** (System Data: blockface data)
- **Automated Parking Data Monitoring ("Listener Mode")** (System Data: rule updates)
- **User-driven error reporting system** (User-Generated Content: error reports)

**Complexity Assessment:** Moderate
- **State Management:** Local (single-user queries, no distributed state)
- **External Integrations:** 2 (Leaflet/OpenStreetMap, SFMTA real-time data source)
- **Business Logic:** Moderate (rule precedence, time-based evaluation, dynamic data ingestion)
- **Data Synchronization:** Basic (periodic polling/listening for updates from the SFMTA data source)

**Technical & Cost Constraints:**
- **Platform:** Must be built as a Progressive Web App (PWA) to ensure native-like mobile experience without app store overhead.
- **Cost Efficiency:** Architecture must prioritize free, open-domain, or low-cost APIs and services. High-cost proprietary solutions (like Google Maps API) should be avoided in favor of cost-effective alternatives (e.g., Leaflet with OpenStreetMap tiles).
- **Data Strategy:** Use SFMTA's Active Streets dataset as the geometry backbone ("The Graph"). Metered data is joined via CNN. **RPP (Residential Parking Permit) zones are determined using address-based matching** as the primary method: Active Streets provides address ranges (lf_fadd, lf_toadd, rt_fadd, rt_toadd) for each side of every street segment, and RPP Eligibility Parcels (i886-hxz9) provide building addresses with RPP codes. The system matches parcel addresses to street address ranges to deterministically assign RPP zones to L/R sides. Non-metered regulations (Time Limits) from dataset `hi6h-neyh` use spatially offset geometries as a fallback method, with geometric analysis (cross-product calculation) to assign regulations to the correct blockface when address data is unavailable.

**MVP Success Metrics:**
- Users can select any point within Mission/SOMA and see parking legality for a chosen radius and duration.
- The system returns accurate results in <2 seconds for 95% of queries.
- The map displays complete blockface coverage for Mission & SOMA with correct color coding.
- Users can successfully report data errors.

## 1. USERS & PERSONAS

**Primary Persona:**
- **Name:** Stephanie (Active SF Resident)
- **Context:** An active SF resident who spends her time running errands and visiting friends. She needs an easy and intuitive way to understand where she can look for street parking when she plans to visit a neighborhood she doesn't live in.
- **Goals:** Avoid parking tickets, minimize time spent searching for parking.
- **Needs:** Fast, accurate, easy-to-understand street parking eligibility for a specific area, date/day/time, and duration.

## 2. FUNCTIONAL REQUIREMENTS

### 2.1 User-Requested Features (All are Priority 0)

**FR-001: Interactive Parking Legality Map**
- **Description:** Visual map interface showing parking legality for all blockfaces within the **Mission and SOMA neighborhoods**.
- **Acceptance Criteria:**
  - [ ] Map loads showing all blockfaces within Mission & SOMA with correct color coding.
  - [ ] Map lines follow the actual curvature of the streets (high-fidelity geometry).

**FR-002: Short-Term Future Legality Checking**
- **Description:** Allow users to check parking legality for the current time or up to 48 hours in the future (to support 24-hour parking durations).
- **Acceptance Criteria:**
  - [ ] System defaults to the current time on app load.
  - [ ] User can select a start time up to 48 hours in the future.

**FR-003: Parking Rule Interpretation Engine**
- **Description:** Backend system that evaluates parking rules from the live data source with correct precedence.
- **Acceptance Criteria:**
  - [ ] The highest-precedence rule determines the result when multiple rules apply.

**FR-004: Plain-Language Rule Explanations**
- **Description:** Display clear, human-readable explanations of parking rules.
- **Acceptance Criteria:**
  - [ ] Tapping a blockface displays a clear explanation of the current rules.
  - [ ] The explanation must explicitly include:
    - **Street Sweeping:** Day and time window (e.g., "Mon 8am-10am").
    - **Closures:** Any current or planned future permitted closures (date/time range).
    - **Duration:** Maximum allowed parking duration for the current time (for both metered and non-metered areas).
    - **Residential Permits:** For non-metered areas, specifics on which Residential Parking Permit (RPP) Area is required to exceed time limits.

**FR-005: Data Ingestion ("Trust, then Verify")**
- **Description:** The system will directly ingest and use data from the official SFMTA source for Mission & SOMA, with **address-based RPP matching** as the primary method.
- **Acceptance Criteria:**
  - [ ] The system uses Active Streets (3psu-pn9h) as the geometry backbone and address range source.
  - [ ] **RPP zones are determined using address-based matching:** RPP Eligibility Parcels (i886-hxz9) provide building addresses and RPP codes, which are matched to Active Streets address ranges (lf_fadd, lf_toadd, rt_fadd, rt_toadd) to deterministically assign RPP zones to L/R sides.
  - [ ] Metered data is joined via CNN key.
  - [ ] Non-metered regulations (`hi6h-neyh`) are spatially joined and geometrically analyzed (using offset vectors) as a fallback method when address data is unavailable.
  - [ ] **Address-based RPP matching achieves >95% accuracy** compared to geometric methods.

**FR-006: Error Reporting System**
- **Description:** Allow users to report incorrect parking rules they encounter.
- **Acceptance Criteria:**
  - [ ] Users can easily find and use a "Report Incorrect Rule" button.

**FR-007: Anonymous Usage (No Authentication)**
- **Description:** Allow users to access all features without creating accounts.
- **Acceptance Criteria:**
  - [ ] All features are immediately accessible on app load.

**FR-008: Automated Parking Data Monitoring ("Listener Mode")**
- **Description:** A backend process that periodically checks the SFMTA data source for changes to rules within Mission & SOMA.
- **Acceptance Criteria:**
  - [ ] The system automatically polls the SFMTA data source on a regular schedule.

**FR-009: Location & Dynamic Map View (MVP Use Cases)**
- **Description:** Supports two distinct modes of operation with a dynamic map interface that responds to viewport changes.
- **Acceptance Criteria:**
  - [x] **Use Case 1 (GPS):** On app load, the map centers on the user's current location (if within Mission/SOMA) and zooms to a close-up street view (~2-3 block radius).
  - [x] **Use Case 2 (Manual):** Users can pan the map freely within the Mission District bounds without automatic re-centering.
  - [x] **Dynamic Data:** Parking eligibility data automatically populates the entire visible map area as the user pans or zooms. No manual "Radius" slider or "Search" button is required.
  - [x] **User Location Marker:** A Curby logo marker displays the user's actual device location and remains visible even when panning to other areas.
  - [x] **Return to Location:** A button styled to match map controls allows users to quickly return to their actual device location.
  - [x] **Restricted Bounds:** The map view is strictly limited to the Mission District for the MVP.
  - [x] **Loading State:** The loading message must state "Street parking eligibility made easy..." with centered branding.

**FR-010: Progressive Web App (PWA) Capabilities**
- **Description:** The application must be installable on mobile devices, work offline (loading cached app shell), and feel like a native application.
- **Acceptance Criteria:**
  - [ ] Valid Web App Manifest provided (name, icons, theme color).
  - [ ] Service Worker registered for caching static assets (app shell).
  - [ ] "Add to Home Screen" prompt triggerable on supported devices.
  - [ ] Viewport configuration prevents accidental zooming/scaling on mobile.

**FR-011: Enhanced User Controls (Duration & Visuals)**
- **Description:** Provide intuitive controls for parking duration and refined map visuals.
- **Acceptance Criteria:**
  - [ ] **Duration Slider:** Replaces fixed buttons with a 0-24 hour slider.
    - [ ] Non-linear scale prioritizing 1-6 hours (hourly steps) and "squeezing" longer durations (8, 10, 12, 16, 20, 24 hours).
    - [ ] Visual labels for key milestones (1h, 3h, 6h, 12h, 24h).
    - [ ] Dynamic emoji feedback based on duration (e.g., ☕ for short, 🌙 for overnight).
  - [ ] **Map Visuals:** Parking eligibility lines must use semi-transparent colors (opacity ~0.6) to blend with the map, avoiding a "harsh" overlay look.

## 3. USER WORKFLOWS

### 3.1 Use Case 1: "I'm Here Now" (GPS Default)
1. User opens the Curby app while in the Mission/SOMA.
2. App requests location permission.
3. Map loads centered on user's current GPS location.
4. System automatically applies a **3-block radius** and defaults parking duration (e.g., 1 hour).
5. Map displays color-coded parking legality for the immediate surrounding area.
6. User can adjust the radius (1-8 blocks) or duration if needed.

### 3.2 Use Case 2: "I'm Going There" (Manual Search)
1. User pans the map to a destination or taps a specific location/address.
2. System sets this point as the new search center.
3. User selects a desired parking duration.
4. User adjusts the search radius (slider/selector from 1 to 8 blocks).
5. Map updates to show eligible parking spots around the selected destination.
6. User taps a specific blockface to see detailed rules.

## 4. BUSINESS RULES

- **Data Source:** The SFMTA database is the single source of truth.
- **Geometry Source:** Active Streets (3psu-pn9h) provides the authoritative geometry (curved lines).
- **Street Closures:** Street closure data is transient. The system must ingest this data daily and invalidate any closure records with an end date in the past. Only "current" and "future" closures (status = permitted) are valid.
- **Rule Precedence:** Street Sweeping and Street Closures take precedence over both Non-Metered Parking Regulation Time Limits and Meter Operating Schedules/Time Limits. (If a street is closed or being swept, you cannot park there regardless of the meter or time limit status).
- **Permit Assumption:** The system assumes all users **do NOT** hold residential parking permits. Parking eligibility in non-metered areas is calculated based on regulations for non-permit holders (e.g., time limits apply).
- **Error Correction:** User-submitted error reports are the primary mechanism for flagging data inaccuracies.
- **Access Control:** All features are public and anonymous.
- **Scope:** The MVP is limited to the **Mission and SOMA neighborhoods**.

## 5. DATA REQUIREMENTS

**Core Entities:**
- **Blockface:** (geo_id, geometry, associated_rules)
  - `geometry` is a GeoJSON `LineString` from Active Streets.
- **Parking Rule:** (rule_id, type, time_windows, restrictions)
- **Error Report:** (report_id, geo_id, timestamp, user_description, status)

## 6. MVP SCOPE & DEFERRED FEATURES

### 6.1 In Scope for MVP
- All features listed in Section 2.1 (FR-001 through FR-010).
- Geographic focus is the **Mission and SOMA neighborhoods**.

### 6.2 Deferred Features (Post-MVP Roadmap)
- **DF-002: User Accounts & Saved Locations:**
  - **Description:** Allow users to create accounts to save locations.
  - **Reason for Deferral:** Not essential for the core validation flow.
- **DF-003: Expansion to Other Neighborhoods:**
  - **Description:** Include parking data for all of San Francisco.
  - **Reason for Deferral:** The "Listener Mode" and error reporting loop need to be validated on the initial dataset first.
- **DF-004: Long-Term Trip Planning:**
  - **Description:** Allow users to plan a trip for a future date beyond 48 hours (e.g., "Next Tuesday").
  - **Reason for Deferral:** Adds complexity to the simulation tool and rule engine; MVP focuses on immediate or near-term parking needs.
- **DF-005: Special Event Parking Intelligence:**
  - **Description:** Ingest and display temporary parking restrictions related to special events (parades, festivals, sports games).
  - **Reason for Deferral:** Requires integrating additional, often unstructured data sources; MVP focuses on standard recurring rules.
- **DF-006: Voice Command Interface:**
  - **Description:** Hands-free voice control to query parking status ("Can I park here?") and receive spoken responses.
  - **Reason for Deferral:** High technical complexity (Speech-to-Text, Text-to-Speech); safety critical feature best built after core data validation.
- **DF-007: Calendar & Navigation Integration:**
  - **Description:** Connect to user calendars to automatically check parking for upcoming appointments and suggest eligible blocks near the destination.
  - **Reason for Deferral:** Requires user authentication and calendar API integrations (Google/Apple); adds significant scope beyond the core "check here now" loop.
- **DF-008: Smart Parking Navigation Routing:**
  - **Description:** Turn-by-turn navigation that actively routes users through streets with *currently legal* parking, avoiding swept or restricted zones.
  - **Reason for Deferral:** Extremely complex custom routing logic; requires building a custom navigation engine on top of map data.
- **DF-009: External Signal Integration:**
  - **Description:** Incorporate data from external services such as traffic volume, travel time, ride share costs, and a calculated "ease of finding parking" score.
  - **Reason for Deferral:** Advanced analytics requiring historical data accumulation and integration with multiple third-party APIs (e.g., Uber/Lyft, Google Traffic).