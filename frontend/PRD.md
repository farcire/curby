---
title: Product Requirements Document
app: elegant-lynx-play
created: 2025-11-17T00:10:25.960Z
version: 1
source: Deep Mode PRD Generation
---

# PRODUCT REQUIREMENTS DOCUMENT

## EXECUTIVE SUMMARY

**Product Vision:** Curby simplifies the hardest part of driving in San Francisco by providing accurate, real-time parking legality information. The MVP focuses on Mission + SOMA neighborhoods with manually curated, contradiction-free parking rules, enabling drivers to know exactly where they can legally park right now or up to 7 days in the future.

**Core Purpose:** Solve the parking legality problem in San Francisco by providing high-accuracy, plain-language answers to "Can I park here?" - eliminating citations, time loss, and stress caused by confusing and contradictory parking rules.

**Target Users:** 
- SF residents who rely on street parking
- Gig workers (DoorDash, Uber, Instacart)
- Daily commuters and tradespeople

**Key Features:**
- Interactive map showing parking legality (User-Generated Content: blockface data)
- Time-based legality checking (now + 7 days ahead) (System Data: rule evaluation)
- Plain-language rule explanations (System Data: rule interpretation)
- Error reporting system (User-Generated Content: error reports)

**Complexity Assessment:** Moderate
- **State Management:** Local (single-user queries, no distributed state)
- **External Integrations:** 2 (Mapbox for maps, SFMTA data source)
- **Business Logic:** Moderate (rule precedence, time-based evaluation, conflict resolution)
- **Data Synchronization:** None (static dataset for MVP, no real-time sync)

**MVP Success Metrics:**
- Users can check parking legality for any Mission/SOMA location
- System returns accurate results in <1 second for 95% of queries
- Map displays complete blockface coverage with correct color coding
- Users can successfully report data errors

## 1. USERS & PERSONAS

**Primary Persona:**
- **Name:** Maria (Gig Worker)
- **Context:** DoorDash driver making 15-20 deliveries daily in SF, constantly searching for legal parking spots
- **Goals:** Quickly find legal parking near delivery locations, avoid parking tickets, minimize time spent searching
- **Needs:** Fast, accurate legality information; future-time checking for scheduled pickups; clear explanations of parking rules

**Secondary Personas:**
- **Daily Commuter:** Needs to find legal parking near work, often arrives at same time daily
- **Tradesperson:** Makes service calls throughout the day, needs quick parking decisions
- **SF Resident:** Weekend errands and social activities, wants to avoid tickets and understand neighborhood rules

## 2. FUNCTIONAL REQUIREMENTS

### 2.1 User-Requested Features (All are Priority 0)

**FR-001: Interactive Parking Legality Map - COMPLETE VERSION**
- **Description:** Visual map interface showing parking legality status for all blockfaces in Mission + SOMA neighborhoods with color-coded indicators
- **Entity Type:** System Data (blockface legality status)
- **User Benefit:** Instantly see where parking is legal without reading complex signs
- **Primary User:** All personas
- **Lifecycle Operations:**
  - **Create:** System generates legality status based on rules and time
  - **View:** Users view map with color-coded blockfaces (green=legal, yellow=limited, red=illegal, gray=insufficient data)
  - **Edit:** Not allowed - system-generated data only
  - **Delete:** Not allowed - persistent system data
  - **List/Search:** Map view shows all blockfaces in viewport; users can pan/zoom to explore
  - **Additional:** Real-time updates when user changes time/duration parameters
- **Acceptance Criteria:**
  - [ ] Given user opens app, when map loads, then all Mission + SOMA blockfaces display with correct color coding
  - [ ] Given user views a blockface, when they see the color, then it accurately reflects current legality status
  - [ ] Given user changes time parameters, when map updates, then all blockface colors recalculate correctly
  - [ ] Given insufficient data exists, when blockface displays, then it shows gray color with appropriate indicator
  - [ ] Users can pan and zoom the map smoothly without performance degradation
  - [ ] Map displays complete coverage of Mission + SOMA with no gaps

**FR-002: Time-Based Legality Checking - COMPLETE VERSION**
- **Description:** Allow users to check parking legality for current time or any future time up to 7 days ahead, with duration selection
- **Entity Type:** Configuration (user query parameters)
- **User Benefit:** Plan ahead for scheduled activities and understand time-limited parking rules
- **Primary User:** All personas
- **Lifecycle Operations:**
  - **Create:** User sets time and duration parameters for legality check
  - **View:** User sees selected time/duration and resulting legality status
  - **Edit:** User can modify time/duration at any time to see updated results
  - **Delete:** Parameters reset to current time when user clears selection
  - **Additional:** Time picker with 7-day limit enforcement; duration selector (15min to 4hrs)
- **Acceptance Criteria:**
  - [ ] Given user opens app, when no time selected, then system defaults to current time
  - [ ] Given user selects future time, when within 7 days, then legality calculation uses that time
  - [ ] Given user attempts to select time >7 days ahead, when they try, then UI prevents selection with clear message
  - [ ] Given user selects duration, when between 15min and 4hrs, then system evaluates legality for entire duration
  - [ ] Given user changes time/duration, when parameters update, then map recalculates all blockface legality within 1 second
  - [ ] Users can easily switch between "now" and future times

**FR-003: Parking Rule Interpretation Engine - COMPLETE VERSION**
- **Description:** Backend system that evaluates parking rules (street sweeping, tow-away, time limits, meters, RPP zones) with correct precedence to determine legality
- **Entity Type:** System Data (rule evaluation logic)
- **User Benefit:** Accurate legality determinations that account for all applicable rules and their interactions
- **Primary User:** All personas (transparent backend service)
- **Lifecycle Operations:**
  - **Create:** System processes rules from curated dataset on startup
  - **View:** Users see results through map colors and rule explanations
  - **Edit:** Not allowed - rules updated only through manual dataset curation
  - **Delete:** Not allowed - rules are persistent system data
  - **Additional:** Rule precedence enforcement (tow-away > street sweeping > no parking > meters > time limits > permits)
- **Acceptance Criteria:**
  - [ ] Given multiple rules apply to a blockface, when system evaluates legality, then highest-precedence rule determines result
  - [ ] Given tow-away zone active, when user checks legality, then system returns "illegal" regardless of other rules
  - [ ] Given street sweeping scheduled, when user checks during sweeping time, then system returns "illegal"
  - [ ] Given time limit applies, when user's duration exceeds limit, then system returns "limited" with explanation
  - [ ] Given meter hours active, when user checks legality, then system includes meter requirement in result
  - [ ] Given RPP zone, when user checks legality, then system indicates permit requirement
  - [ ] System evaluates all rules correctly for any time within 7-day window

**FR-004: Plain-Language Rule Explanations - COMPLETE VERSION**
- **Description:** Display clear, human-readable explanations of why a parking spot is legal, limited, or illegal
- **Entity Type:** System Data (rule interpretation text)
- **User Benefit:** Understand parking restrictions without decoding complex signage
- **Primary User:** All personas
- **Lifecycle Operations:**
  - **Create:** System generates explanation based on applicable rules
  - **View:** Users see explanation when they tap/click a blockface
  - **Edit:** Not allowed - system-generated content
  - **Delete:** Not allowed - explanations generated on-demand
  - **Additional:** Explanations update in real-time when time/duration changes
- **Acceptance Criteria:**
  - [ ] Given user taps blockface, when legality determined, then clear explanation displays
  - [ ] Given multiple rules apply, when explanation shows, then it lists all relevant restrictions in plain language
  - [ ] Given illegal status, when explanation displays, then it clearly states the reason (e.g., "Street sweeping Tuesday 8-10am")
  - [ ] Given limited status, when explanation shows, then it specifies the limitation (e.g., "2-hour limit, meter required")
  - [ ] Given legal status, when explanation displays, then it confirms "Legal to park" with any conditions
  - [ ] Explanations use simple, non-technical language accessible to all users

**FR-005: Manual Dataset Curation (Gold-Standard) - COMPLETE VERSION**
- **Description:** Pre-launch manual cleanup of Mission + SOMA parking rule data to eliminate contradictions, fix geometries, and ensure accuracy
- **Entity Type:** System Data (curated parking rules dataset)
- **User Benefit:** High-accuracy legality results without data conflicts or errors
- **Primary User:** System (enables accurate results for all user personas)
- **Lifecycle Operations:**
  - **Create:** Manual review and correction of SFMTA source data before MVP launch
  - **View:** Developers/curators review dataset for conflicts and errors
  - **Edit:** Manual correction of conflicting rules, bad geometries, missing data, impossible combinations
  - **Delete:** Remove duplicate or invalid rule entries
  - **Additional:** Export cleaned dataset as contradiction-free CSV/JSON for system use
- **Acceptance Criteria:**
  - [ ] Given SFMTA source data, when manual review complete, then no conflicting rule entries remain
  - [ ] Given blockface geometries, when cleanup complete, then all segments correctly aligned and no gaps exist
  - [ ] Given time ranges in rules, when review complete, then all ranges are valid and complete
  - [ ] Given rule combinations, when validation complete, then no impossible combinations exist (e.g., conflicting tow-away times)
  - [ ] Given sweeping and meter data, when cleanup complete, then all schedules are accurate and complete
  - [ ] Cleaned dataset covers 100% of Mission + SOMA blockfaces with verified accuracy

**FR-006: Error Reporting System - COMPLETE VERSION**
- **Description:** Allow users to report incorrect parking rules or data errors they encounter
- **Entity Type:** User-Generated Content (error reports)
- **User Benefit:** Contribute to data accuracy and get incorrect information fixed
- **Primary User:** All personas
- **Lifecycle Operations:**
  - **Create:** User submits error report with free-text description and location context
  - **View:** User sees confirmation that report was submitted; admin reviews reports in database
  - **Edit:** Not allowed - reports are immutable once submitted
  - **Delete:** Not allowed - reports retained for data quality tracking
  - **List/Search:** Admin can query reports by location, date, status
  - **Additional:** Reports logged with timestamp, location, user description; manual review queue
- **Acceptance Criteria:**
  - [ ] Given user finds incorrect rule, when they tap "Report Incorrect Rule", then report form displays
  - [ ] Given user enters description, when they submit, then report saves to database with location context
  - [ ] Given report submitted, when save completes, then user sees confirmation message
  - [ ] Given multiple reports submitted, when admin reviews, then all reports are accessible and searchable
  - [ ] Users can report errors from any blockface on the map
  - [ ] System captures sufficient context (location, time checked, user description) for manual review

### 2.2 Essential Market Features

**FR-007: Anonymous Usage (No Authentication)**
- **Description:** Allow users to access all features without creating accounts or logging in
- **Entity Type:** Configuration/System
- **User Benefit:** Immediate access without friction, complete privacy
- **Primary User:** All personas
- **Lifecycle Operations:**
  - **Create:** Not applicable - no user accounts
  - **View:** Users access all features immediately on app load
  - **Edit:** Not applicable - no user profiles
  - **Delete:** Not applicable - no stored user data
  - **Additional:** No session management, no user tracking
- **Acceptance Criteria:**
  - [ ] Given user opens app, when it loads, then all features are immediately accessible
  - [ ] Given user uses app, when they interact, then no login prompt appears
  - [ ] Given user closes app, when they return, then no authentication required
  - [ ] System does not store any user-identifying information
  - [ ] All features work without user accounts

## 3. USER WORKFLOWS

### 3.1 Primary Workflow: Check Parking Legality Now

**Trigger:** User needs to find legal parking in Mission or SOMA
**Outcome:** User knows exactly where they can legally park right now

**Steps:**
1. User opens Curby app
2. System loads map centered on user's current location (or Mission/SOMA default)
3. User sees color-coded blockfaces showing current legality status
4. User identifies green (legal) or yellow (limited) blockfaces near destination
5. User taps specific blockface to see details
6. System displays plain-language explanation of parking rules
7. User decides where to park based on clear legality information

**Alternative Paths:**
- If user's location is outside Mission/SOMA, map shows Mission/SOMA area with message about coverage
- If user wants different duration, they adjust duration selector and map updates
- If user finds incorrect information, they tap "Report Incorrect Rule"

### 3.2 Secondary Workflow: Check Future Parking Legality

**Trigger:** User wants to plan parking for future appointment or delivery
**Outcome:** User knows where they can legally park at specific future time

**Steps:**
1. User opens Curby app
2. User taps time selector
3. User chooses future date/time (within 7 days)
4. User sets expected parking duration (15min to 4hrs)
5. System recalculates all blockface legality for selected time and duration
6. Map updates with new color coding
7. User sees which spots will be legal at their planned arrival time
8. User taps blockface to see rule explanation for that time
9. User plans parking strategy based on future legality

**Alternative Paths:**
- If user tries to select time >7 days ahead, system prevents selection and shows message
- If rules change during selected duration (e.g., street sweeping starts), system shows "limited" or "illegal"

### 3.3 Entity Management Workflows

**Error Report Management Workflow**

**Create Error Report:**
1. User identifies incorrect parking rule on map
2. User taps blockface with error
3. User taps "Report Incorrect Rule" button
4. User enters description of the error in free-text field
5. User submits report
6. System saves report with location, timestamp, and description
7. System confirms submission to user

**View Error Reports (Admin):**
1. Admin accesses database directly
2. Admin queries error_reports table
3. Admin sees list of all submitted reports with location and description
4. Admin reviews report details and compares to actual signage/rules
5. Admin manually corrects dataset if error confirmed

**No Edit/Delete for Users:**
- Error reports are immutable once submitted
- Only admins can act on reports through manual dataset updates

### 3.4 Map Interaction Workflow

**Explore Parking Options:**
1. User opens map view
2. User pans to area of interest within Mission/SOMA
3. User zooms in to see individual blockfaces clearly
4. User observes color coding across multiple blocks
5. User taps blockfaces to compare rules
6. User identifies best parking option based on legality and location
7. User navigates to chosen spot using external navigation app

**Change Time Parameters:**
1. User adjusts time picker to different time
2. System immediately recalculates legality for all visible blockfaces
3. Map colors update within 1 second
4. User sees how legality changes over time
5. User can toggle between current time and future times to compare

## 4. BUSINESS RULES

### Entity Lifecycle Rules

**Blockface Legality Status (System Data):**
- **Who can create:** System only (generated from rules + time parameters)
- **Who can view:** All users (public data)
- **Who can edit:** No one (system-generated, updated through dataset changes only)
- **Who can delete:** No one (persistent system data)
- **What happens on deletion:** N/A - data is never deleted
- **Related data handling:** Legality recalculates when time parameters change or dataset updates

**Error Reports (User-Generated Content):**
- **Who can create:** All users (anonymous)
- **Who can view:** Admins only (database access)
- **Who can edit:** No one (immutable once submitted)
- **Who can delete:** No one (retained for data quality tracking)
- **What happens on deletion:** N/A - reports are never deleted
- **Related data handling:** Reports reference blockface location but don't modify it

**Parking Rules Dataset (System Data):**
- **Who can create:** System administrators (manual curation)
- **Who can view:** All users (through map and explanations)
- **Who can edit:** Administrators only (manual dataset updates)
- **Who can delete:** Administrators only (remove invalid rules)
- **What happens on deletion:** Blockface shows "insufficient data" status
- **Related data handling:** Rule changes trigger legality recalculation for affected blockfaces

### Access Control
- All users