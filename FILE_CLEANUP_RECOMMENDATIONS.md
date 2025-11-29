# Complete Project File Cleanup Recommendations

**Generated:** 2025-11-28  
**Scope:** Entire project (root, backend, frontend)  
**Total Files Analyzed:** 153 files

## Executive Summary

Your project contains 153 .py and .md files across all directories. The majority (143 files) are in the backend directory, with many being one-time investigation/analysis scripts from development. This guide provides systematic recommendations for cleanup.

## Files by Location

### ✅ Root Directory (5 files) - ALL KEEP
**Essential project documentation**

- [`refined-prd.md`](refined-prd.md:1) - 15.03 KB (Most recent, 2025-11-28) ✅
- [`Backend-dev-plan.md`](Backend-dev-plan.md:1) - 10.96 KB - Development plan
- [`plan.md`](plan.md:1) - 2.68 KB - Project plan
- `plan_step_2_detailed.md` - 3.95 KB - Detailed planning
- [`audit_all_files.py`](audit_all_files.py:1) - 3.53 KB - Audit tool (just created)

**Action:** KEEP ALL - These are important project documentation

### ✅ Frontend Directory (5 files) - ALL KEEP
**PRD and documentation files**

- [`frontend/PRD.md`](frontend/PRD.md:1) - 17.24 KB (2025-11-27) ✅
- `frontend/PRD-Notion-Format.md` - 19.67 KB - PRD template
- `frontend/PRD-Template.md` - 6.98 KB - PRD template
- [`frontend/AI_RULES.md`](frontend/AI_RULES.md:1) - 1.00 KB - AI guidelines
- [`frontend/README.md`](frontend/README.md:1) - 1.62 KB - Frontend docs

**Action:** KEEP ALL - Essential product and development documentation

### 🔍 Backend Directory (143 files) - NEEDS CLEANUP

**Breakdown:**
- 100 Python files
- 43 Markdown/text files

## Backend Cleanup Recommendations

### ✅ KEEP - Core Production (7 files)

**Essential for production system:**
- [`main.py`](backend/main.py:1) - FastAPI server
- [`models.py`](backend/models.py:1) - Data models
- [`display_utils.py`](backend/display_utils.py:1) - Display formatting
- [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py:1) - Current ingestion script
- [`run_ingestion.sh`](backend/run_ingestion.sh:1) - Ingestion runner
- [`check_ingestion_status.py`](backend/check_ingestion_status.py:1) - Monitoring tool
- `requirements.txt` - Dependencies

### 🗄️ ARCHIVE - Investigation Scripts (47 files)

**One-time analysis scripts - Safe to archive:**

These were created during development to investigate specific issues:
- `investigate_18th_balmy.py`, `investigate_cardinal_directions.py`, `investigate_20th_street.py`
- `inspect_*` files (20+ files): `inspect_intersections_detailed.py`, `inspect_active_parcels.py`, etc.
- `debug_*` files: `debug_20th_street.py`, `debug_bryant.py`, `debug_db.py`
- `find_*` files: `find_cardinal_directions.py`, `find_balmy_complete.py`, etc.
- `query_*` files: `query_balmy_direct.py`, `query_20th_street.py`, etc.
- `show_*` files: `show_blockface_details.py`
- `analyze_*` files: `analyze_20th_street_block.py`, `analyze_geometry_overlaps.py`

**Recommendation:** Move to `archive/investigation_scripts/`

### 🔍 REVIEW - Validation Scripts (26 files)

**Keep recent/useful ones, archive older:**

**KEEP (Recent & Useful):**
- `verify_collection_fix.py` (2025-11-28)
- `validate_cardinal_directions.py` (2025-11-28)
- `check_18th_street_raw.py` (2025-11-28)
- `check_cardinal_fields.py` (2025-11-28)
- `validate_mission_merge.py` (2025-11-28)

**ARCHIVE (Older validation):**
- `verify_db.py`, `verify_geometry.py`, `verify_regulations.py`
- `validate_join_keys.py`, `validate_side_assignments.py`
- `check_datasets_structure.py`, `check_metered_cnn.py`
- And 15+ other older validation scripts

**Recommendation:** Keep 5-10 recent ones, archive the rest

### 🧪 ARCHIVE - Test Scripts (9 files)

**Archive if current system is working:**
- `test_parking_regs.py`, `test_20th_street.py`, `test_mariposa.py`
- `test_rpp_parcels_mission.py`, `test_offset.py`, `test_ingest.py`
- `quick_mission_analysis.py`, `quick_check.py`, `simple_rpp_test.py`

**Recommendation:** Move to `archive/test_scripts/`

### 📦 ARCHIVE - Old Ingestion (3 files)

**Deprecated - Replaced by current system:**
- `ingest_data.py` - Old ingestion script
- `ingest_mission_only.py` - Mission-only version
- `create_master_cnn_join.py` - Old join approach

**Recommendation:** Move to `archive/old_ingestion/`

### 📝 REVIEW - Documentation (43 files)

**Keep current docs, archive historical:**

**KEEP (Current & Relevant - ~10 files):**
- `README.md` - Main documentation
- `AI_RESTRICTION_INTERPRETATION_SYSTEM.md` - Current system
- `USER_FRIENDLY_DISPLAY_IMPLEMENTATION_PLAN.md` - Current feature
- `CARDINAL_DIRECTION_INGESTION_ISSUE.md` - Known issue
- `DISPLAY_SYSTEM_IMPLEMENTATION_STATUS.md` - Current status
- `FILE_CLEANUP_RECOMMENDATIONS.md` - This document
- `GEOSPATIAL_QUERY_FIX_SUMMARY.md` - Recent fix
- `CNNL_CNNR_OVERLAY_FIX.md` - Recent fix
- `MISSION_COLLECTION_MISMATCH_INVESTIGATION.md` - Recent investigation
- `Backend-dev-plan.md` - Development plan

**ARCHIVE (Historical - ~33 files):**
- Investigation summaries: `INVESTIGATION_SUMMARY.md`, `CNN_SEGMENT_STATUS_AND_FINDINGS.md`
- Old architecture docs: `ARCHITECTURE_COMPARISON.md`, `DATA_ARCHITECTURE_UPDATED.md`
- Analysis output files: `*.txt` files (15+ files)
- Mission-specific docs (now citywide): `MISSION_*.md` files
- Old implementation plans: `RPP_IMPLEMENTATION_PLAN.md`, `CNN_SEGMENT_IMPLEMENTATION_PLAN.md`

**Recommendation:** Keep ~10 current docs, archive ~33 historical docs to `archive/old_docs/`

### 🗑️ DELETE - Backup Files (1 file)

- `backup_database.py` - Backup script (use MongoDB backups instead)

**Recommendation:** Delete

### ❓ UNCATEGORIZED - Review Manually (14 files)

**Scripts that need manual review:**
- `audit_project_files.py` - Audit tool (just created)
- `balmy_correct_api.py`, `balmy_search_all.py`, `balmy_final_query.py`
- `generate_icons.py` - Icon generation
- `pep9_globalid_shape_final_analysis.py` - Analysis
- `mission_comprehensive_analysis.py` - Analysis
- `fetch_intersection_metadata.py`, `fetch_raw_json.py`
- Shell scripts: `check_ingestion_progress.sh`, `run_cnn_segment_migration.sh`, `wait_and_verify.sh`, `backup_database.sh`, `monitor_ingestion.sh`

## Cleanup Commands

### Step 1: Create Archive Directories

```bash
mkdir -p archive/{investigation_scripts,old_ingestion,old_docs,test_scripts,validation_scripts}
```

### Step 2: Archive Investigation Scripts (47 files)

```bash
cd backend
mv investigate_*.py inspect_*.py debug_*.py find_*.py query_*.py show_*.py analyze_*.py ../archive/investigation_scripts/
```

### Step 3: Archive Old Ingestion Scripts (3 files)

```bash
cd backend
mv ingest_data.py ingest_mission_only.py create_master_cnn_join.py ../archive/old_ingestion/
```

### Step 4: Archive Test Scripts (9 files)

```bash
cd backend
mv test_*.py quick_*.py simple_*.py ../archive/test_scripts/
```

### Step 5: Archive Old Validation Scripts

```bash
cd backend
# Keep recent ones, archive older (review list first)
mv verify_db.py verify_geometry.py verify_regulations.py ../archive/validation_scripts/
mv check_datasets_structure.py check_metered_cnn.py ../archive/validation_scripts/
# Add more as needed after review
```

### Step 6: Archive Historical Documentation

```bash
cd backend
# Archive old analysis files
mv *.txt ../archive/old_docs/
# Archive old architecture docs (review list first)
mv ARCHITECTURE_COMPARISON.md DATA_ARCHITECTURE_UPDATED.md ../archive/old_docs/
mv INVESTIGATION_SUMMARY.md CNN_SEGMENT_STATUS_AND_FINDINGS.md ../archive/old_docs/
# Add more as needed after review
```

### Step 7: Delete Backup File

```bash
cd backend
rm backup_database.py
```

## Expected Results

### Before Cleanup:
- **Total files:** 153
- **Backend files:** 143 (100 .py + 43 .md)
- **Total size:** ~1,100 KB

### After Cleanup:
- **Total files:** ~40-50 (core + current docs)
- **Backend files:** ~30-40
- **Archived files:** ~100-110
- **Space savings:** ~400-500 KB (40-50% reduction)

## Important Notes

1. **PRD Files:** All 4 PRD files are preserved (root + frontend)
2. **Ingestion:** The current ingestion in Terminal 16 is NOT affected
3. **Git History:** All files remain in git history if needed
4. **Reversible:** Archived files can be restored anytime
5. **Review First:** Always review the archive commands before executing

## Audit Tools

Run these anytime to check file status:

```bash
# Backend-only audit with categorization
cd backend && python3 audit_project_files.py

# Project-wide audit
python3 audit_all_files.py
```

## Next Steps

1. ✅ Review this document
2. ✅ Manually review validation and documentation files
3. ✅ Execute cleanup commands (after review)
4. ✅ Verify system still works
5. ✅ Commit cleaned-up structure to git

---

**Last Updated:** 2025-11-28  
**Status:** Ready for review and execution