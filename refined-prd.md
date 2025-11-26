---
title: Product Requirements Document - REFINED
app: elegant-lynx-play
created: 2025-11-25T07:06:20.848Z
version: 4
source: BA-PRD Agent Refinement
---

# PRODUCT REQUIREMENTS DOCUMENT

## EXECUTIVE SUMMARY

**Product Vision:** Curby simplifies street parking in San Francisco by providing accurate, real-time street parking eligibility based on location and duration. The MVP focuses on the **Mission and SOMA neighborhoods**, powered by a live connection to parking rule databases and a user-driven feedback loop to continuously improve accuracy.

**Core Purpose:** Solve the parking legality problem by providing high-accuracy, plain-language answers to "Can I park here?". For the demo, it provides a simulation tool to select any location within the covered area, define a radius, and check parking legality for a specified duration.

**Target Users:** 
- SF residents who rely on street parking
- Gig workers (DoorDash, Uber, Instacart)
- Demo Audience & Stakeholders

**Key Features:**
- **Demo Location & Radius Selector** (System: Simulation Tool)
- Interactive map showing real-time parking legality (System Data: blockface data)
- Automated Parking Data Monitoring ("Listener Mode") (System Data: rule updates)
- User-driven error reporting system (User-Generated Content: error reports)

**Complexity Assessment:** Moderate
- **State Management:** Local (single-user queries, no distributed state)
- **External Integrations:** 2 (Mapbox, SFMTA real-time data source)
- **Business Logic:** Moderate (rule precedence, time-based evaluation, dynamic data ingestion)
- **Data Synchronization:** Basic (periodic polling/listening for updates from the SFMTA data source)

**MVP Success Metrics:**
- Users can select any point within Mission/SOMA and see parking legality for a chosen radius and duration.
- The system returns accurate results in <2 seconds for 95% of queries.
- The map displays complete blockface coverage for Mission & SOMA with correct color coding.
- Users can successfully report data errors.

## 1. USERS & PERSONAS

**Primary Persona:**
- **Name:** Maria (Gig Worker)
- **Context:** DoorDash driver needing to quickly find legal parking in Mission and SOMA.
- **Goals:** Avoid parking tickets, minimize time spent searching for parking.
- **Needs:** Fast, accurate, and up-to-the-minute legality information for a specific area.

## 2. FUNCTIONAL REQUIREMENTS

### 2.1 User-Requested Features (All are Priority 0)

**FR-001: Interactive Parking Legality Map**
- **Description:** Visual map interface showing parking legality for all blockfaces within the **Mission and SOMA neighborhoods**.
- **Acceptance Criteria:**
  - [ ] Map loads showing all blockfaces within Mission & SOMA with correct color coding.

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
- **Description:** The system will directly ingest and use data from the official SFMTA source for Mission & SOMA.
- **Acceptance Criteria:**
  - [ ] The system starts with the assumption that the ingested data is accurate.

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

**FR-009: Location & Radius Selector (MVP Use Cases)**
- **Description:** Supports two distinct modes of operation: automatic GPS-based discovery and manual location selection.
- **Acceptance Criteria:**
  - [ ] **Use Case 1 (GPS):** On app load, the map centers on the user's current location (if within MVP area) and defaults to a 3-block search radius.
  - [ ] **Use Case 2 (Manual):** Users can tap anywhere on the map or select an address to set a search center.
  - [ ] Users can adjust the search radius between 1 and 8 blocks.
  - [ ] The map updates to show parking legality for all blockfaces within the current radius and duration settings.

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
- **Street Closures:** Street closure data is transient. The system must ingest this data daily and invalidate any closure records with an end date in the past. Only "current" and "future" closures (status = permitted) are valid.
- **Rule Precedence:** Street Sweeping and Street Closures take precedence over both Non-Metered Parking Regulation Time Limits and Meter Operating Schedules/Time Limits. (If a street is closed or being swept, you cannot park there regardless of the meter or time limit status).
- **Permit Assumption:** The system assumes all users **do NOT** hold residential parking permits. Parking eligibility in non-metered areas is calculated based on regulations for non-permit holders (e.g., time limits apply).
- **Error Correction:** User-submitted error reports are the primary mechanism for flagging data inaccuracies.
- **Access Control:** All features are public and anonymous.
- **Scope:** The MVP is limited to the **Mission and SOMA neighborhoods**.

## 5. DATA REQUIREMENTS

**Core Entities:**
- **Blockface:** (geo_id, geometry, associated_rules)
- **Parking Rule:** (rule_id, type, time_windows, restrictions)
- **Error Report:** (report_id, geo_id, timestamp, user_description, status)

## 6. MVP SCOPE & DEFERRED FEATURES

### 6.1 In Scope for MVP
- All features listed in Section 2.1 (FR-001 through FR-009).
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