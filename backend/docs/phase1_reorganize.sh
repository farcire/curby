#!/bin/bash

# Phase 1: Content-Based Documentation Organization
# Generated: January 8, 2026
# Based on: Comprehensive content analysis of all 77 files
# Method: Read all files, analyzed status markers, dates, and content

set -e  # Exit on error

echo "=========================================="
echo "Phase 1: Documentation Organization"
echo "Content-Based (Not Name-Based!)"
echo "=========================================="
echo ""

# Check we're in the right directory
if [ ! -f "CNN_MASTER_REFERENCE_ARCHITECTURE.md" ]; then
    echo "❌ Error: Not in docs directory"
    echo "Please run: cd backend/docs"
    exit 1
fi

echo "✓ Found docs directory"
echo ""

# Phase 1: Create Directory Structure
echo "Phase 1: Creating directory structure..."
mkdir -p current
mkdir -p reference/{guides,specs,status}
mkdir -p completed
mkdir -p investigations
mkdir -p archive
echo "✓ Directories created"
echo ""

# Phase 2: Move CURRENT PRODUCTION (8 files)
echo "Phase 2: Moving CURRENT PRODUCTION docs (8 files)..."
echo "  These describe systems RUNNING IN PRODUCTION RIGHT NOW"
echo ""

mv CNN_MASTER_REFERENCE_ARCHITECTURE.md current/ 2>/dev/null || echo "  (already moved)"
mv MONGODB_COLLECTION_ARCHITECTURE.md current/ 2>/dev/null || echo "  (already moved)"
mv DATA_QUALITY_ISSUES.md current/ 2>/dev/null || echo "  (already moved)"
mv DATA_QUALITY_LOG.md current/ 2>/dev/null || echo "  (already moved)"
mv PROJECT_HISTORY.md current/ 2>/dev/null || echo "  (already moved)"
mv REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md current/ 2>/dev/null || echo "  (already moved)"
mv INGESTION_REFACTORING_COMPLETE_SUMMARY.md current/ 2>/dev/null || echo "  (already moved)"
mv BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md current/ 2>/dev/null || echo "  (already moved)"

echo "✓ Current production docs moved"
echo ""

# Phase 3: Move REFERENCE - Guides (12 files)
echo "Phase 3a: Moving reference guides (12 files)..."
echo "  How-to guides for current systems"
echo ""

mv BLOCKFACE_GEOMETRY_INTEGRATION_GUIDE.md reference/guides/ 2>/dev/null || true
mv BLOCKFACE_GEOMETRY_README.md reference/guides/ 2>/dev/null || true
mv DAY_TIME_NORMALIZATION_GUIDE.md reference/guides/ 2>/dev/null || true
mv INGESTION_CHECKPOINT_GUIDE.md reference/guides/ 2>/dev/null || true
mv INGESTION_PROGRESS_GUIDE.md reference/guides/ 2>/dev/null || true
mv MANUAL_DATA_OVERRIDES_GUIDE.md reference/guides/ 2>/dev/null || true
mv NON_METERED_REGULATION_COMPLETE_DISPLAY_GUIDE.md reference/guides/ 2>/dev/null || true
mv REGULATION_DISPLAY_EXAMPLES.md reference/guides/ 2>/dev/null || true
mv REGULATION_DISPLAY_FINAL_IMPLEMENTATION.md reference/guides/ 2>/dev/null || true
mv STREET_CLEANING_ANALYSIS_GUIDE.md reference/guides/ 2>/dev/null || true
mv STREET_CLEANING_INTEGRATION_GUIDE.md reference/guides/ 2>/dev/null || true
mv TESTING_GUIDE.md reference/guides/ 2>/dev/null || true

echo "✓ Guides moved"
echo ""

# Phase 3b: Move REFERENCE - Specs (11 files)
echo "Phase 3b: Moving reference specs (11 files)..."
echo "  Technical specifications for current systems"
echo ""

mv CNN_MASTER_FILE_DESIGN.md reference/specs/ 2>/dev/null || true
mv FALLBACK_MATCHING_STRATEGY.md reference/specs/ 2>/dev/null || true
mv INGESTION_ARCHITECTURE_SPECIFICATION.md reference/specs/ 2>/dev/null || true
mv INGESTION_ORDER_REFACTORING_PLAN.md reference/specs/ 2>/dev/null || true
mv INGESTION_ORDER_REFACTORING_PLAN_V2.md reference/specs/ 2>/dev/null || true
mv METER_POLICIES_INTEGRATION_ARCHITECTURE.md reference/specs/ 2>/dev/null || true
mv REFACTORING_PLAN.md reference/specs/ 2>/dev/null || true
mv REGULATION_SEVERITY_HIERARCHY.md reference/specs/ 2>/dev/null || true
mv RULE_DISPLAY_CENTRALIZATION_PLAN.md reference/specs/ 2>/dev/null || true
mv SCHEMA_OPTIMIZATION_NOTE.md reference/specs/ 2>/dev/null || true
mv SCHEMA_OPTIMIZATION_PLAN.md reference/specs/ 2>/dev/null || true

echo "✓ Specs moved"
echo ""

# Phase 3c: Move REFERENCE - Status Reports (13 files)
echo "Phase 3c: Moving status reports (13 files)..."
echo "  Status reports and fixes"
echo ""

mv 247_NO_PARKING_CONFLICT_RESOLUTION.md reference/status/ 2>/dev/null || true
mv ASYMMETRIC_STREET_CLEANING_DATA_GAPS.md reference/status/ 2>/dev/null || true
mv BLOCKFACE_GEOMETRY_ISSUE_AND_FIX.md reference/status/ 2>/dev/null || true
mv BLOCKFACE_GEOMETRY_STATUS_REPORT.md reference/status/ 2>/dev/null || true
mv CARDINAL_DIRECTION_INGESTION_ISSUE.md reference/status/ 2>/dev/null || true
mv DO_NOT_DEPLOY_cnn_master_with_blockfaces.md reference/status/ 2>/dev/null || true
mv FUZZY_MATCHING_VALIDATION_SUMMARY.md reference/status/ 2>/dev/null || true
mv INGESTION_SUCCESS_SUMMARY.md reference/status/ 2>/dev/null || true
mv METER_INGESTION_FIX_SUMMARY.md reference/status/ 2>/dev/null || true
mv METER_SCHEDULE_DISPLAY_FIX.md reference/status/ 2>/dev/null || true
mv METER_SCHEDULE_FIELD_FIX.md reference/status/ 2>/dev/null || true
mv ON_STREET_METER_COVERAGE_REPORT.md reference/status/ 2>/dev/null || true
mv OVERSIZED_VEHICLE_FIX_SUMMARY.md reference/status/ 2>/dev/null || true

echo "✓ Status reports moved"
echo ""

# Phase 4: Move COMPLETED WORK (14 files)
echo "Phase 4: Moving completed implementation summaries (14 files)..."
echo "  Historical record of implementations"
echo ""

mv ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md completed/ 2>/dev/null || true
mv ALTERNATE_SCHEDULE_ANALYSIS_SUMMARY.md completed/ 2>/dev/null || true
mv ARCHITECTURE_CORRECTION_FINAL_SUMMARY.md completed/ 2>/dev/null || true
mv BOUNDARY_GENERATION_ANALYSIS.md completed/ 2>/dev/null || true
mv CODE_AUDIT_REGULATION_DISPLAY.md completed/ 2>/dev/null || true
mv DATA_ARCHITECTURE_UPDATED.md completed/ 2>/dev/null || true
mv DATA_MODEL_UPDATE.md completed/ 2>/dev/null || true
mv DATA_QUALITY_FOLLOWUP_TASKS.md completed/ 2>/dev/null || true
mv DAY_TIME_NORMALIZATION_REFACTORING_SUMMARY.md completed/ 2>/dev/null || true
mv DURATION_STANDARDIZATION_COMPLETE.md completed/ 2>/dev/null || true
mv METER_DATASETS_VALIDATION_SUMMARY.md completed/ 2>/dev/null || true
mv METER_MATCHING_FIX_SUMMARY.md completed/ 2>/dev/null || true
mv METER_RATE_APPLICATION_SUMMARY.md completed/ 2>/dev/null || true
mv REGULATION_DISPLAY_IMPLEMENTATION_SUMMARY.md completed/ 2>/dev/null || true

echo "✓ Completed work moved"
echo ""

# Phase 5: Move INVESTIGATIONS (11 files + 1 dir)
echo "Phase 5: Moving investigations (11 files + 1 directory)..."
echo "  Research, analysis, and root cause investigations"
echo ""

mv 18TH_ST_NORTH_PARKING_INVESTIGATION.md investigations/ 2>/dev/null || true
mv BLOCKID_SUFFIX_PATTERN_ANALYSIS.md investigations/ 2>/dev/null || true
mv BRYANT_OVERLAY_INVESTIGATION.md investigations/ 2>/dev/null || true
mv CNN_111000_INVESTIGATION_REPORT.md investigations/ 2>/dev/null || true
mv KING_ST_CNN_INVESTIGATION.md investigations/ 2>/dev/null || true
mv METER_OPERATING_SCHEDULES_INVESTIGATION_SUMMARY.md investigations/ 2>/dev/null || true
mv RUN_GEOMETRY_FIX.md investigations/ 2>/dev/null || true
mv RUN_SYSTEMIC_FIXES.md investigations/ 2>/dev/null || true
mv SYSTEMIC_ISSUES_FIX_PLAN.md investigations/ 2>/dev/null || true
mv UNMATCHED_METERS_ANALYSIS.md investigations/ 2>/dev/null || true
mv cnn_961000_investigation investigations/ 2>/dev/null || true

echo "✓ Investigations moved"
echo ""

# Phase 6: Move to ARCHIVE (10 files + 1 dir)
echo "Phase 6: Moving obsolete docs to archive (10 files)..."
echo "  40+ days old, superseded, or obsolete"
echo ""

mv ARCHITECTURE_CORRECTION_SUMMARY.md archive/ 2>/dev/null || true
mv BENCHMARK_LOG.md archive/ 2>/dev/null || true
mv COST_OPTIMIZATION_REPORT.md archive/ 2>/dev/null || true
mv EVALUATION_REPORT.md archive/ 2>/dev/null || true
mv FILE_CLEANUP_RECOMMENDATIONS.md archive/ 2>/dev/null || true
mv FREE_TIER_PROCESSING_PLAN.md archive/ 2>/dev/null || true
mv GOLDEN_DATASET_NOTES.md archive/ 2>/dev/null || true
mv LLM_EVALUATION_STRATEGY.md archive/ 2>/dev/null || true
mv PARKING_REGULATION_INTERPRETATION_SYSTEM.md archive/ 2>/dev/null || true
mv prompts archive/ 2>/dev/null || true

echo "✓ Archive complete"
echo ""

# Verification
echo "=========================================="
echo "Verification"
echo "=========================================="
echo ""
echo "Current production:          $(ls current/*.md 2>/dev/null | wc -l | xargs) files"
echo "Reference guides:            $(ls reference/guides/*.md 2>/dev/null | wc -l | xargs) files"
echo "Reference specs:             $(ls reference/specs/*.md 2>/dev/null | wc -l | xargs) files"
echo "Reference status:            $(ls reference/status/*.md 2>/dev/null | wc -l | xargs) files"
echo "Completed implementations:   $(ls completed/*.md 2>/dev/null | wc -l | xargs) files"
echo "Investigations:              $(find investigations -name "*.md" 2>/dev/null | wc -l | xargs) files"
echo "Archive:                     $(find archive -name "*.md" 2>/dev/null | wc -l | xargs) files"
echo ""

REMAINING=$(ls *.md 2>/dev/null | wc -l | xargs)
echo "Files remaining in root:     $REMAINING"
echo ""

if [ "$REMAINING" -eq 0 ]; then
    echo "✅ SUCCESS! All markdown files organized."
else
    echo "⚠️  Note: $REMAINING files remain in root"
    ls *.md 2>/dev/null
fi

echo ""
echo "=========================================="
echo "NEXT STEPS"
echo "=========================================="
echo ""
echo "1. Review the organization:"
echo "   ls -la current/"
echo "   ls -la reference/guides/"
echo ""
echo "2. Create INDEX.md files (run create_index_files.sh)"
echo ""
echo "3. Commit the changes:"
echo "   git add ."
echo "   git commit -m 'docs: organize by content (Phase 1 of 2)'"
echo ""
echo "4. Use this structure for 1-2 weeks, then we'll do Phase 2 (renaming)"
echo ""
echo "=========================================="
