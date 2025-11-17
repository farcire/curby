# 🅿️ Curby - Product Requirements Document

> **Product Vision:** Simplify the hardest part of driving in San Francisco by providing accurate, real-time parking legality information.

---

## 📋 Executive Summary

### 🎯 Core Purpose
Solve the parking legality problem in San Francisco by providing high-accuracy, plain-language answers to "Can I park here?" - eliminating citations, time loss, and stress caused by confusing and contradictory parking rules.

### 👥 Target Users
- **SF residents** who rely on street parking
- **Gig workers** (DoorDash, Uber, Instacart)
- **Daily commuters** and tradespeople

### ✨ Key Features
| Feature | Type | Status |
|---------|------|--------|
| Interactive parking map | User-Generated Content | ✅ Implemented |
| Time-based legality checking | System Data | ✅ Implemented |
| Plain-language rule explanations | System Data | ✅ Implemented |
| Error reporting system | User-Generated Content | ✅ Implemented |

### 📊 Complexity Assessment
- **State Management:** Local (single-user queries)
- **External Integrations:** 2 (Mapbox, SFMTA data)
- **Business Logic:** Moderate (rule precedence, time evaluation)
- **Data Synchronization:** None (static dataset for MVP)

### 🎯 MVP Success Metrics
- ✅ Users can check parking legality for any Mission/SOMA location
- ✅ System returns accurate results in <1 second for 95% of queries
- ✅ Map displays complete blockface coverage with correct color coding
- ✅ Users can successfully report data errors

---

## 👤 Users & Personas

### Primary Persona: Maria (Gig Worker)
- **Context:** DoorDash driver making 15-20 deliveries daily in SF
- **Goals:** 
  - Quickly find legal parking near delivery locations
  - Avoid parking tickets
  - Minimize time spent searching
- **Needs:**
  - Fast, accurate legality information
  - Future-time checking for scheduled pickups
  - Clear explanations of parking rules

### Secondary Personas

**Daily Commuter**
- Needs to find legal parking near work
- Often arrives at same time daily

**Tradesperson**
- Makes service calls throughout the day
- Needs quick parking decisions

**SF Resident**
- Weekend errands and social activities
- Wants to avoid tickets and understand neighborhood rules

---

## 🎨 Functional Requirements

### FR-001: Interactive Parking Legality Map ✅

**Description:** Visual map interface showing parking legality status for all blockfaces in Mission + SOMA neighborhoods with color-coded indicators

**Entity Type:** System Data (blockface legality status)

**User Benefit:** Instantly see where parking is legal without reading complex signs

**Lifecycle Operations:**
- **Create:** System generates legality status based on rules and time
- **View:** Users view map with color-coded blockfaces
  - 🟢 Green = Legal
  - 🔴 Red = Illegal
  - ⚫ Gray = Insufficient data
- **Edit:** Not allowed - system-generated data only
- **Delete:** Not allowed - persistent system data
- **List/Search:** Map view shows all blockfaces in viewport

**Acceptance Criteria:**
- ✅ All Mission + SOMA blockfaces display with correct color coding
- ✅ Colors accurately reflect current legality status
- ✅ Map updates when time parameters change
- ✅ Insufficient data shows gray color
- ✅ Pan and zoom work smoothly
- ✅ Complete coverage with no gaps

---

### FR-002: Time-Based Legality Checking ✅

**Description:** Allow users to check parking legality for current time or any future time up to 7 days ahead, with duration selection

**Entity Type:** Configuration (user query parameters)

**User Benefit:** Plan ahead for scheduled activities and understand time-limited parking rules

**Lifecycle Operations:**
- **Create:** User sets time and duration parameters
- **View:** User sees selected time/duration and resulting legality
- **Edit:** User can modify time/duration at any time
- **Delete:** Parameters reset to current time when cleared

**Time Parameters:**
- ⏰ Time range: Now to +7 days
- ⏱️ Duration options: 1hr, 2hr, 3hr, 6hr, 12hr, 24hr

**Acceptance Criteria:**
- ✅ Defaults to current time on app open
- ✅ Future time selection works within 7-day limit
- ✅ System prevents selection >7 days with clear message
- ✅ Duration selection between 1-24 hours works
- ✅ Map recalculates all blockface legality within 1 second
- ✅ Easy toggle between "now" and future times

---

### FR-003: Parking Rule Interpretation Engine ✅

**Description:** Backend system that evaluates parking rules with correct precedence to determine legality

**Entity Type:** System Data (rule evaluation logic)

**User Benefit:** Accurate legality determinations that account for all applicable rules and their interactions

**Rule Types & Precedence:**
1. **Tow-away** (100) - Highest priority
2. **Street sweeping** (90)
3. **No parking** (80)
4. **Meter** (70)
5. **Time limit** (60)
6. **RPP zone** (50) - Lowest priority

**Acceptance Criteria:**
- ✅ Highest-precedence rule determines result
- ✅ Tow-away zones return "illegal" regardless of other rules
- ✅ Street sweeping during active time returns "illegal"
- ✅ Time limit exceeded returns "limited" with explanation
- ✅ Meter hours include meter requirement in result
- ✅ RPP zones indicate permit requirement
- ✅ All rules evaluated correctly for 7-day window

---

### FR-004: Plain-Language Rule Explanations ✅

**Description:** Display clear, human-readable explanations of why a parking spot is legal, limited, or illegal

**Entity Type:** System Data (rule interpretation text)

**User Benefit:** Understand parking restrictions without decoding complex signage

**Example Explanations:**
- ✅ "You can park here! No restrictions apply during your time."
- 🚫 "Don't park here! Street sweeping Tuesday 8-10am."
- ⚠️ "2-hour limit, meter required Mon-Sat 9am-6pm"

**Acceptance Criteria:**
- ✅ Clear explanation displays when user taps blockface
- ✅ Multiple rules listed in plain language
- ✅ Illegal status clearly states the reason
- ✅ Limited status specifies the limitation
- ✅ Legal status confirms with any conditions
- ✅ Simple, non-technical language for all users

---

### FR-005: Manual Dataset Curation (Gold-Standard) ✅

**Description:** Pre-launch manual cleanup of Mission + SOMA parking rule data to eliminate contradictions

**Entity Type:** System Data (curated parking rules dataset)

**User Benefit:** High-accuracy legality results without data conflicts or errors

**Curation Process:**
1. Manual review of SFMTA source data
2. Correction of conflicting rules
3. Fix bad geometries
4. Remove duplicate entries
5. Validate time ranges
6. Export cleaned dataset

**Acceptance Criteria:**
- ✅ No conflicting rule entries remain
- ✅ All blockface geometries correctly aligned
- ✅ All time ranges valid and complete
- ✅ No impossible rule combinations
- ✅ All schedules accurate and complete
- ✅ 100% coverage of Mission + SOMA blockfaces

---

### FR-006: Error Reporting System ✅

**Description:** Allow users to report incorrect parking rules or data errors

**Entity Type:** User-Generated Content (error reports)

**User Benefit:** Contribute to data accuracy and get incorrect information fixed

**Report Fields:**
- 📍 Location (auto-captured)
- 📝 Description (free-text)
- 🕐 Timestamp (auto-captured)

**Acceptance Criteria:**
- ✅ "Report Incorrect Rule" button accessible from any blockface
- ✅ Report form displays with location context
- ✅ Report saves to database with all context
- ✅ User sees confirmation message
- ✅ Admin can access and search all reports
- ✅ Sufficient context captured for manual review

---

### FR-007: Anonymous Usage (No Authentication) ✅

**Description:** Allow users to access all features without creating accounts or logging in

**Entity Type:** Configuration/System

**User Benefit:** Immediate access without friction, complete privacy

**Privacy Features:**
- 🔓 No login required
- 🚫 No user tracking
- 🔒 No stored user data
- ⚡ Instant access to all features

**Acceptance Criteria:**
- ✅ All features immediately accessible on app load
- ✅ No login prompt appears
- ✅ No authentication required on return
- ✅ No user-identifying information stored
- ✅ All features work without accounts

---

## 🔄 User Workflows

### Primary Workflow: Check Parking Legality Now

**Trigger:** User needs to find legal parking in Mission or SOMA

**Outcome:** User knows exactly where they can legally park right now

**Steps:**
1. 📱 User opens Curby app
2. 🗺️ System loads map centered on user's location
3. 👀 User sees color-coded blockfaces showing current legality
4. 🎯 User identifies green (legal) or yellow (limited) blockfaces
5. 👆 User taps specific blockface to see details
6. 📋 System displays plain-language explanation
7. ✅ User decides where to park based on clear information

**Alternative Paths:**
- If outside Mission/SOMA → Show coverage area with message
- If different duration needed → Adjust duration selector
- If incorrect information → Tap "Report Incorrect Rule"

---

### Secondary Workflow: Check Future Parking Legality

**Trigger:** User wants to plan parking for future appointment

**Outcome:** User knows where they can legally park at specific future time

**Steps:**
1. 📱 User opens Curby app
2. ⏰ User taps time selector
3. 📅 User chooses future date/time (within 7 days)
4. ⏱️ User sets expected parking duration
5. 🔄 System recalculates all blockface legality
6. 🗺️ Map updates with new color coding
7. 👀 User sees which spots will be legal at planned time
8. 👆 User taps blockface to see rule explanation
9. ✅ User plans parking strategy

---

### Entity Management: Error Reports

**Create Error Report:**
1. 🔍 User identifies incorrect parking rule on map
2. 👆 User taps blockface with error
3. 🚨 User taps "Report Incorrect Rule" button
4. ✍️ User enters description of error
5. 📤 User submits report
6. 💾 System saves report with location and timestamp
7. ✅ System confirms submission to user

**View Error Reports (Admin):**
1. 🔐 Admin accesses database
2. 📊 Admin queries error_reports table
3. 📋 Admin sees list of all reports
4. 🔍 Admin reviews report details
5. ✏️ Admin manually corrects dataset if error confirmed

> **Note:** Error reports are immutable once submitted. Only admins can act on reports through manual dataset updates.

---

## 📏 Business Rules

### Entity Lifecycle Rules

#### Blockface Legality Status (System Data)
- **Who can create:** System only
- **Who can view:** All users (public data)
- **Who can edit:** No one (system-generated)
- **Who can delete:** No one (persistent)
- **Related data:** Recalculates when time parameters change

#### Error Reports (User-Generated Content)
- **Who can create:** All users (anonymous)
- **Who can view:** Admins only
- **Who can edit:** No one (immutable)
- **Who can delete:** No one (retained for tracking)
- **Related data:** References blockface location

#### Parking Rules Dataset (System Data)
- **Who can create:** System administrators
- **Who can view:** All users (through map)
- **Who can edit:** Administrators only
- **Who can delete:** Administrators only
- **Related data:** Rule changes trigger recalculation

---

### Access Control

**All Users (Anonymous):**
- ✅ View all parking data
- ✅ Check legality for any time/duration
- ✅ Submit error reports
- ✅ Use all map features

**Administrators:**
- ✅ All user permissions
- ✅ Access error reports database
- ✅ Modify parking rules dataset
- ✅ Curate and clean data

---

### Data Rules

**Validation Rules:**
- Time ranges must be valid (start < end)
- Days of week must be 0-6
- Precedence values must be positive integers
- Coordinates must be valid lat/lng pairs
- Duration must be between 15 minutes and 24 hours

**Required Fields:**
- Blockface: id, geometry, streetName, side
- Rule: id, type, timeRanges, description, precedence
- Error Report: blockfaceId, location, description, timestamp

**Constraints:**
- Time check limited to 7 days in future
- Duration limited to 1-24 hours
- Radius limited to 1-8 blocks
- Coverage limited to Mission + SOMA (MVP)

---

## 💾 Data Requirements

### Core Entities

#### User (System/Configuration)
**Attributes:**
- None - anonymous usage only

**Relationships:**
- None - no user accounts

**Lifecycle:** N/A - no user data stored

---

#### Blockface (System Data)
**Attributes:**
- `id` (string) - Unique identifier
- `geometry` (LineString) - Geographic coordinates
- `streetName` (string) - Street name
- `side` (enum) - north/south/east/west
- `rules` (array) - Associated parking rules

**Relationships:**
- Has many ParkingRules
- Referenced by ErrorReports

**Lifecycle:** Created during data curation, updated manually

---

#### ParkingRule (System Data)
**Attributes:**
- `id` (string) - Unique identifier
- `type` (enum) - Rule type (tow-away, street-sweeping, etc.)
- `timeRanges` (array) - When rule applies
- `description` (string) - Plain-language explanation
- `precedence` (number) - Priority level
- `metadata` (object) - Additional rule-specific data

**Relationships:**
- Belongs to Blockface

**Lifecycle:** Created during data curation, updated manually

---

#### ErrorReport (User-Generated Content)
**Attributes:**
- `id` (string) - Unique identifier
- `blockfaceId` (string) - Reference to blockface
- `location` (object) - Lat/lng coordinates
- `description` (string) - User's error description
- `timestamp` (string) - When report was submitted

**Relationships:**
- References Blockface

**Lifecycle:** Created by users, immutable, never deleted

---

## 🔌 Integration Requirements

### External Systems

#### Mapbox (Maps)
**Purpose:** Interactive map display and navigation

**Data Exchange:**
- **Inbound:** Map tiles, geocoding data
- **Outbound:** User location, viewport bounds

**Integration Type:** Client-side JavaScript SDK

---

#### SFMTA Data (Parking Rules)
**Purpose:** Source of parking regulation data

**Data Exchange:**
- **Inbound:** Parking meter data, regulation data
- **Outbound:** None (read-only)

**Integration Type:** REST API (one-time data fetch + manual curation)

**Endpoints:**
- Meters: `https://data.sfgov.org/resource/fqfu-vcqd.json`
- Regulations: `https://data.sfgov.org/resource/qbyz-te2i.json`

---

## 🎨 Functional Views/Areas

### Primary Views

#### 🗺️ Map View (Main)
**Purpose:** Core functionality - visualize parking legality

**Features:**
- Color-coded blockfaces (green/red/gray)
- Interactive tap to see details
- Pan and zoom navigation
- Radius circle showing search area
- Center marker showing user location

---

#### ⏰ Duration Picker
**Purpose:** Set parking duration for legality check

**Features:**
- Quick duration buttons (1hr, 2hr, 3hr, 6hr, 12hr, 24hr)
- Visual emoji indicators
- Current selection highlighted
- Instant map updates

---

#### 📍 Blockface Detail Panel
**Purpose:** Show detailed parking rules for selected location

**Features:**
- Status indicator (legal/illegal)
- Street name and side
- List of all applicable rules
- Permit requirements
- Next restriction warning
- Report error button

---

#### 🔍 Radius Control
**Purpose:** Adjust search radius around user location

**Features:**
- Slider control (1-8 blocks)
- Visual feedback on map
- Stats showing legal spots in radius
- Smooth zoom adjustment

---

#### 🚨 Error Report Dialog
**Purpose:** Allow users to report incorrect data

**Features:**
- Location auto-captured
- Free-text description field
- Friendly, encouraging messaging
- Submission confirmation

---

### Navigation Structure

**Persistent Access:**
- Duration picker (always visible at top)
- Radius control (always visible at bottom)
- Map view (main screen)

**Default Landing:**
- Map view centered on user location (or Mission/SOMA default)
- Current time selected
- 1-hour duration selected
- 3-block radius selected

**Modal/Overlay:**
- Blockface detail panel (slides up from bottom)
- Error report dialog (centered modal)

---

## 🎯 MVP Scope & Constraints

### MVP Success Definition

✅ **Core Workflow Functions:**
- Users can check parking legality for any Mission/SOMA location
- System returns accurate results quickly
- Map displays complete coverage
- Error reporting works end-to-end

✅ **All Entity Lifecycles Complete:**
- Blockface legality: System-generated, view-only
- Error reports: User-created, admin-reviewed
- Parking rules: Admin-curated, system-evaluated

✅ **Basic Features Work Reliably:**
- Map loads and displays correctly
- Color coding is accurate
- Time/duration selection works
- Radius control functions properly

---

### Technical Constraints for MVP

**Performance:**
- Expected concurrent users: 100
- Data volume: ~500-1000 blockfaces (Mission + SOMA)
- Response time: <1 second for 95% of queries
- Map rendering: Smooth at 60fps

**Coverage:**
- Geographic: Mission + SOMA neighborhoods only
- Time horizon: Current time + 7 days
- Duration range: 1-24 hours
- Radius range: 1-8 blocks

---

### Explicitly Excluded from MVP

❌ **Deferred Features:**
- Real-time parking availability
- Payment integration for meters
- Turn-by-turn navigation
- Citywide coverage (beyond Mission/SOMA)
- Historical parking data
- Predictive parking suggestions
- Social features (sharing spots, reviews)
- Permit application/management
- Multi-city support

❌ **Advanced Capabilities:**
- Machine learning for rule interpretation
- Automated data updates from SFMTA
- Push notifications for restrictions
- Offline mode
- Route planning with parking
- Integration with calendar apps

---

## 🤔 Assumptions & Decisions

### Business Model
**Assumption:** Free to use, no monetization in MVP

**Reasoning:** Focus on product-market fit before monetization

---

### Access Model
**Decision:** Anonymous usage only (no accounts)

**Reasoning:**
- Reduces friction for first-time users
- Simplifies MVP development
- Protects user privacy
- Faster time to value

---

### Entity Lifecycle Decisions

**Blockface Legality:**
- **Decision:** System-generated, view-only
- **Reasoning:** Ensures data consistency and accuracy

**Error Reports:**
- **Decision:** User-created, immutable, admin-reviewed
- **Reasoning:** Maintains audit trail while allowing user feedback

**Parking Rules:**
- **Decision:** Manual curation only (no automated updates)
- **Reasoning:** Ensures gold-standard accuracy for MVP

---

### Geographic Scope
**Decision:** Mission + SOMA only for MVP

**Reasoning:**
- High density of gig workers and residents
- Manageable dataset for manual curation
- Sufficient to validate product concept
- Can expand after proving value

---

### Time Horizon
**Decision:** 7-day limit for future checks

**Reasoning:**
- Covers most planning scenarios
- Reduces complexity of rule evaluation
- Parking rules rarely change within 7 days
- Sufficient for MVP validation

---

## 📊 Success Metrics (Post-Launch)

### User Engagement
- Daily active users
- Average session duration
- Number of legality checks per session
- Return user rate

### Product Quality
- Accuracy of legality determinations (target: >95%)
- Error report rate (lower is better)
- User-reported data corrections
- Time to resolve error reports

### User Satisfaction
- App store ratings
- User feedback sentiment
- Feature usage patterns
- Parking ticket avoidance (user-reported)

---

## 🚀 Next Steps

1. ✅ Complete MVP development
2. ✅ Manual data curation for Mission + SOMA
3. 🔄 Beta testing with gig workers
4. 📊 Collect user feedback and metrics
5. 🐛 Fix bugs and improve accuracy
6. 📈 Plan expansion to additional neighborhoods
7. 💰 Explore monetization strategies

---

> **Last Updated:** Based on current prototype implementation
> 
> **Status:** MVP Complete - Ready for Beta Testing
> 
> **Next Review:** After beta testing phase

---

*This PRD is a living document and will be updated as the product evolves based on user feedback and market learnings.*