#!/bin/bash

# Create INDEX.md files for all directories
# These help navigate and understand the documentation structure

echo "Creating INDEX.md files..."

# ====================================
# current/INDEX.md
# ====================================
cat > current/INDEX.md << 'EOF'
# Current Production Documentation

**Last Updated:** January 8, 2026

These 8 documents describe systems **RUNNING IN PRODUCTION RIGHT NOW**.

---

## 🚀 Essential Reading (Start Here)

If you're new to the project, read these in order:

### 1. CNN_MASTER_REFERENCE_ARCHITECTURE.md
**Main system architecture**
- Describes the CNN (Centerline Network Number) foundation
- 6 data architecture layers
- How all datasets integrate
- **Start here** if you're new

### 2. REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md
**Current regulation normalization system** (Updated: Jan 1, 2026)
- How parking regulations are normalized
- Special event zones (Oracle Park, Chase Center)
- 6-color cap system
- Meter schedule priority: TOW > ALTERNATE > OP > PRE+FREE
- **This IS your active normalization logic**

### 3. INGESTION_REFACTORING_COMPLETE_SUMMARY.md
**Current 12-step ingestion process** (Updated: Jan 5, 2026 - 3 days ago!)
- Documents the CURRENT ingestion pipeline
- 12 sequential steps from streets to final database
- Just fixed critical bugs 3 days ago
- 100% meter matching success
- **This IS your production ingestion**

---

## 📊 Database & Schema

### 4. MONGODB_COLLECTION_ARCHITECTURE.md
**Current database schema**
- Collection structure
- Field definitions
- Query patterns

---

## 📐 Geometry & Spatial

### 5. BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md
**Current geometry system** (Updated: Dec 30, 2024)
- Meter-calibrated offset: 5.55 meters
- THREE-PRIORITY blockface integration
- 93% of blockfaces use synthetic geometry with this offset
- **This IS running in production NOW**

---

## 🐛 Quality Tracking (ACTIVE)

### 6. DATA_QUALITY_ISSUES.md
**Active issue tracking** (Last updated: Jan 4, 2026)
- Known data quality issues
- Resolution status
- Issue #013: 24/7 No Parking conflicts (RESOLVED Jan 4)
- Issue #017: Meter matching odd/even parity (RESOLVED Jan 7)

### 7. DATA_QUALITY_LOG.md
**Active quality log** (Last entry: Jan 7, 2026 - YESTERDAY!)
- Chronological log of quality issues and fixes
- Most recent tracking
- Check here for latest updates

---

## 📖 Context & History

### 8. PROJECT_HISTORY.md
**Why decisions were made**
- Project evolution
- Key decisions and rationale
- Essential for understanding "why we did it this way"

---

## 📈 Key Metrics (Current Production)

From INGESTION_REFACTORING_COMPLETE_SUMMARY.md:
- **Total segments:** 34,324
- **With meters:** 3,763 (11%)
- **With regulations:** 23,794 (69.3%)
- **With street sweeping:** 22,574 (65.8%)
- **Meter matching:** 100% success
- **Meter schedules:** 72.8% coverage

---

## 🎯 When to Read These

**New team member?**
→ Read 1, 2, 3 in order

**Debugging production issue?**
→ Check 6, 7 for known issues

**Understanding a decision?**
→ Read 8 for context

**Working on geometry?**
→ Read 5 for current offset system

**Database query help?**
→ Read 4 for schema

---

## ⚠️ Important Notes

- These docs describe **CURRENT PRODUCTION**
- Files with "COMPLETE" in name = "NOW IN PRODUCTION" (not archived!)
- Recent dates (Jan 2026) = very current
- Check DATA_QUALITY_LOG.md (updated yesterday!) for latest issues

---

**Next:** See `reference/` for guides and specs on how to use these systems
EOF

# ====================================
# reference/guides/INDEX.md
# ====================================
cat > reference/guides/INDEX.md << 'EOF'
# Reference Guides

**Last Updated:** January 8, 2026

How-to guides for using current production systems.

---

## 🔧 System Operation Guides

### BLOCKFACE_GEOMETRY_INTEGRATION_GUIDE.md
How to integrate blockface geometries
- THREE-PRIORITY system
- When to use deterministic vs synthetic

### DAY_TIME_NORMALIZATION_GUIDE.md
How to use regulation_normalizer.py
- Parse days and times consistently
- Format for display
- Current system guide

### INGESTION_CHECKPOINT_GUIDE.md
How ingestion checkpoints work
- Resume from failure
- Track progress

### INGESTION_PROGRESS_GUIDE.md
How to monitor ingestion progress
- Status checking
- Progress indicators

### MANUAL_DATA_OVERRIDES_GUIDE.md
How to apply manual data overrides
- Override format
- When to use overrides

### TESTING_GUIDE.md
Testing procedures and best practices

---

## 📋 Display & Formatting Guides

### NON_METERED_REGULATION_COMPLETE_DISPLAY_GUIDE.md
How to display non-metered parking regulations
- Display format rules
- User-friendly text

### REGULATION_DISPLAY_EXAMPLES.md
Examples of regulation displays

### REGULATION_DISPLAY_FINAL_IMPLEMENTATION.md
Final display implementation guide
- Complete display logic

---

## 🧹 Specialized Guides

### BLOCKFACE_GEOMETRY_README.md
README for blockface geometry system

### STREET_CLEANING_ANALYSIS_GUIDE.md
Guide to street cleaning data

### STREET_CLEANING_INTEGRATION_GUIDE.md
How street cleaning integrates with other data

---

## 📌 Quick Reference

**Need to parse days/times?**
→ DAY_TIME_NORMALIZATION_GUIDE.md

**Need to display regulations?**
→ NON_METERED_REGULATION_COMPLETE_DISPLAY_GUIDE.md

**Running ingestion?**
→ INGESTION_PROGRESS_GUIDE.md

**Applying manual fixes?**
→ MANUAL_DATA_OVERRIDES_GUIDE.md

---

**See also:** `reference/specs/` for technical specifications
EOF

# ====================================
# reference/specs/INDEX.md
# ====================================
cat > reference/specs/INDEX.md << 'EOF'
# Technical Specifications

**Last Updated:** January 8, 2026

Technical specifications for current production systems.

---

## 📐 Architecture Specs

### INGESTION_ARCHITECTURE_SPECIFICATION.md
Complete ingestion architecture specification
- 12-step process detailed
- Matching logic for all datasets

### CNN_MASTER_FILE_DESIGN.md
CNN master file structure design
- Field definitions
- Data organization

### METER_POLICIES_INTEGRATION_ARCHITECTURE.md
Meter policies integration architecture

### REFACTORING_PLAN.md
Overall system refactoring specifications

---

## 🔄 Process Specs

### INGESTION_ORDER_REFACTORING_PLAN.md
Ingestion order refactoring specification

### INGESTION_ORDER_REFACTORING_PLAN_V2.md
Updated ingestion order specification (v2)

---

## 🎨 Display & Logic Specs

### REGULATION_SEVERITY_HIERARCHY.md
Regulation hierarchy specification
*(Note: "severity" terminology was corrected, but hierarchy concept is still valid)*

### RULE_DISPLAY_CENTRALIZATION_PLAN.md
Display centralization specification

### FALLBACK_MATCHING_STRATEGY.md
Fallback matching strategy specification

---

## 🗄️ Database Specs

### SCHEMA_OPTIMIZATION_NOTE.md
Schema optimization notes

### SCHEMA_OPTIMIZATION_PLAN.md
Schema optimization plan
- Identified issues with street_name field
- Display field redundancy

---

## 📌 Quick Reference

**Understanding ingestion?**
→ INGESTION_ARCHITECTURE_SPECIFICATION.md

**Database schema questions?**
→ SCHEMA_OPTIMIZATION_PLAN.md

**Regulation logic?**
→ REGULATION_SEVERITY_HIERARCHY.md

**Display formatting?**
→ RULE_DISPLAY_CENTRALIZATION_PLAN.md

---

**See also:** `reference/guides/` for how-to guides
EOF

# ====================================
# reference/status/INDEX.md
# ====================================
cat > reference/status/INDEX.md << 'EOF'
# Status Reports & Fixes

**Last Updated:** January 8, 2026

Status reports, bug fixes, and resolution documentation.

---

## ✅ Issue Resolutions

### 247_NO_PARKING_CONFLICT_RESOLUTION.md
24/7 No Parking conflict resolution

### ASYMMETRIC_STREET_CLEANING_DATA_GAPS.md
Analysis of asymmetric street cleaning data

### BLOCKFACE_GEOMETRY_ISSUE_AND_FIX.md
Blockface geometry issue identified and fixed

### CARDINAL_DIRECTION_INGESTION_ISSUE.md
Cardinal direction ingestion issue resolution

### METER_INGESTION_FIX_SUMMARY.md
Meter ingestion bug fix (was checking wrong field)

### METER_MATCHING_FIX_SUMMARY.md
Meter matching fix (duplicate assignments to L and R)

### METER_SCHEDULE_DISPLAY_FIX.md
Meter schedule display fix

### METER_SCHEDULE_FIELD_FIX.md
Meter schedule field fix

---

## 📊 Status Reports

### BLOCKFACE_GEOMETRY_STATUS_REPORT.md
Blockface geometry status report

### FUZZY_MATCHING_VALIDATION_SUMMARY.md
Fuzzy matching validation results
- Result: 21.4% accuracy
- **Decision: ABANDONED** in favor of deterministic matching

### INGESTION_SUCCESS_SUMMARY.md
Ingestion success summary (Jan 1, 2026)
- Current production data snapshot
- 34,324 segments successfully ingested

### ON_STREET_METER_COVERAGE_REPORT.md
On-street meter coverage analysis

### OVERSIZED_VEHICLE_FIX_SUMMARY.md
Oversized vehicle regulation fix

---

## ⚠️ Critical Warnings

### DO_NOT_DEPLOY_cnn_master_with_blockfaces.md
**⚠️ CRITICAL WARNING**
- Identifies incorrect file with synthetic geometries
- DO NOT USE this file for deployment
- Still relevant warning!

---

## 📌 Quick Reference

**Looking for a specific fix?**
- Meter issues → METER_INGESTION_FIX_SUMMARY.md, METER_MATCHING_FIX_SUMMARY.md
- Geometry issues → BLOCKFACE_GEOMETRY_ISSUE_AND_FIX.md
- Data gaps → ASYMMETRIC_STREET_CLEANING_DATA_GAPS.md

**Current data snapshot?**
→ INGESTION_SUCCESS_SUMMARY.md (Jan 1, 2026)

**Why we abandoned fuzzy matching?**
→ FUZZY_MATCHING_VALIDATION_SUMMARY.md (21.4% accuracy!)

---

**See also:** `current/DATA_QUALITY_LOG.md` for most recent issues (updated yesterday!)
EOF

# ====================================
# completed/INDEX.md
# ====================================
cat > completed/INDEX.md << 'EOF'
# Completed Work Summaries

**Last Updated:** January 8, 2026

Historical record of completed implementations and refactorings.

These document work that **IS DONE** and integrated into production.

---

## 📋 Implementation Summaries

### ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md
Analysis of 371 ALTERNATE meter schedules
- 7 patterns identified (School Days, Giants games, etc.)
- All are passenger loading zones when active

### ALTERNATE_SCHEDULE_ANALYSIS_SUMMARY.md
Summary of ALTERNATE schedule patterns

### DAY_TIME_NORMALIZATION_REFACTORING_SUMMARY.md
Day/time parsing refactoring
- Centralized into regulation_normalizer.py
- Eliminated code duplication across 4+ files
- 44% reduction in display_utils.py

### DURATION_STANDARDIZATION_COMPLETE.md
Duration/time limit standardization
- Storage: Integer minutes
- Display: Pre-computed strings

### METER_DATASETS_VALIDATION_SUMMARY.md
Validation of 3 meter datasets
- Confirmed relationships
- Identified temporal modifications

### METER_MATCHING_FIX_SUMMARY.md
Meter matching algorithm fix
- Fixed duplicate assignments
- Now uses blockface_id for side determination

### METER_RATE_APPLICATION_SUMMARY.md
Meter rate application
- 60,485 rate records
- 100% match rate, zero conflicts

### REGULATION_DISPLAY_IMPLEMENTATION_SUMMARY.md
Regulation display implementation
- Centralized formatting
- Removed 249 lines from frontend

---

## 🔧 Architecture Corrections

### ARCHITECTURE_CORRECTION_FINAL_SUMMARY.md
Fixed incorrect "severity hierarchy" model
- Corrected: Non-metered and metered are equal-priority types
- Updated 5 major files
- ~70% of corrections complete

---

## 🔍 Audits & Analysis

### BOUNDARY_GENERATION_ANALYSIS.md
Boundary generation analysis

### CODE_AUDIT_REGULATION_DISPLAY.md
Code audit results for regulation display

---

## 📊 Historical Updates

### DATA_ARCHITECTURE_UPDATED.md (38 days old)
Historical architecture update

### DATA_MODEL_UPDATE.md (37 days old)
Historical data model update

### DATA_QUALITY_FOLLOWUP_TASKS.md (37 days old)
Historical followup tasks

---

## 📌 Quick Reference

**Understanding ALTERNATE schedules?**
→ ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md

**How day/time parsing was refactored?**
→ DAY_TIME_NORMALIZATION_REFACTORING_SUMMARY.md

**Why severity hierarchy was wrong?**
→ ARCHITECTURE_CORRECTION_FINAL_SUMMARY.md

**Meter rate application details?**
→ METER_RATE_APPLICATION_SUMMARY.md

---

**Note:** These are historical records. For CURRENT production systems, see `current/`
EOF

# ====================================
# investigations/INDEX.md
# ====================================
cat > investigations/INDEX.md << 'EOF'
# Investigations & Analysis

**Last Updated:** January 8, 2026

Research, analysis, and root cause investigations.

---

## 🔍 Location-Specific Investigations

### 18TH_ST_NORTH_PARKING_INVESTIGATION.md
18th Street North 2700-2798 investigation
- CNN: 868000
- Oversized vehicle regulation issue

### CNN_111000_INVESTIGATION_REPORT.md
CNN 111000 investigation

### KING_ST_CNN_INVESTIGATION.md
King Street CNN investigation

### BRYANT_OVERLAY_INVESTIGATION.md
Bryant Street overlay investigation

### cnn_961000_investigation/ (directory)
CNN 961000 investigation files

---

## 📊 Pattern Analysis

### BLOCKID_SUFFIX_PATTERN_ANALYSIS.md
Analysis of blockID suffix patterns

### METER_OPERATING_SCHEDULES_INVESTIGATION_SUMMARY.md
Investigation of meter schedule patterns

### UNMATCHED_METERS_ANALYSIS.md
Analysis of unmatched meters

---

## 🔧 Technical Investigations

### RUN_GEOMETRY_FIX.md (37 days old)
Geometry fix investigation

### RUN_SYSTEMIC_FIXES.md (37 days old)
Systemic fixes investigation

### SYSTEMIC_ISSUES_FIX_PLAN.md (37 days old)
Fix plan for systemic issues

---

## 📌 Quick Reference

**Specific street issue?**
- 18th St → 18TH_ST_NORTH_PARKING_INVESTIGATION.md
- King St → KING_ST_CNN_INVESTIGATION.md
- Bryant St → BRYANT_OVERLAY_INVESTIGATION.md

**Pattern analysis?**
→ BLOCKID_SUFFIX_PATTERN_ANALYSIS.md

**Meter schedules?**
→ METER_OPERATING_SCHEDULES_INVESTIGATION_SUMMARY.md

---

**Note:** These are research documents. For fixes and resolutions, see `reference/status/`
EOF

# ====================================
# archive/INDEX.md
# ====================================
cat > archive/INDEX.md << 'EOF'
# Archived Documentation

**Last Updated:** January 8, 2026

Obsolete documentation (40+ days old, superseded, or abandoned approaches).

---

## 📦 Obsolete Documents

### ARCHITECTURE_CORRECTION_SUMMARY.md (10 days old)
Early draft of architecture correction
- **Superseded by:** ARCHITECTURE_CORRECTION_FINAL_SUMMARY.md (in completed/)

### BENCHMARK_LOG.md (42 days old)
Old benchmark data

### COST_OPTIMIZATION_REPORT.md (41 days old)
Old cost optimization report

### EVALUATION_REPORT.md (41 days old)
Old evaluation report

### FILE_CLEANUP_RECOMMENDATIONS.md (43 days old)
Old cleanup recommendations

### FREE_TIER_PROCESSING_PLAN.md (41 days old)
Old processing plan for free tier

### GOLDEN_DATASET_NOTES.md (41 days old)
Old dataset notes

### LLM_EVALUATION_STRATEGY.md (43 days old)
Old LLM evaluation strategy

### PARKING_REGULATION_INTERPRETATION_SYSTEM.md (43 days old)
Old interpretation system

### prompts/ (directory)
Old prompts directory

---

## 📌 Note

These documents are kept for historical reference but are no longer current or relevant to the production system.

**For current documentation, see:**
- `current/` - Current production systems
- `reference/` - How-to guides and specs
- `completed/` - Recently completed work (< 40 days)

---

**Archive Criteria:**
- 40+ days old AND not referenced by current docs
- Explicitly superseded by newer documents
- Abandoned approaches or old strategies
EOF

echo "✅ All INDEX.md files created!"
echo ""
echo "INDEX files created in:"
echo "  - current/INDEX.md"
echo "  - reference/guides/INDEX.md"
echo "  - reference/specs/INDEX.md"
echo "  - reference/status/INDEX.md"
echo "  - completed/INDEX.md"
echo "  - investigations/INDEX.md"
echo "  - archive/INDEX.md"
