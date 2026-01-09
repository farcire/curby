# File Cleanup Recommendations

**Generated:** 2025-11-28  
**Total Files Analyzed:** 176 files (1,067.53 KB)

## Summary

Your backend directory contains a significant number of investigation, validation, and test scripts that were created during development. Most of these can be safely archived or deleted.

## Breakdown by Category

### ✅ KEEP (7 files - 52.91 KB)
**Core production files - DO NOT DELETE**
- `main.py` - FastAPI server
- `models.py` - Data models  
- `display_utils.py` - Display formatting utilities
- `ingest_data_cnn_segments.py` - Current ingestion script
- `run_ingestion.sh` - Ingestion runner
- `check_ingestion_status.py` - Monitoring tool
- `requirements.txt` - Dependencies

### 🗄️ ARCHIVE (47 files - 247.48 KB)
**Investigation scripts - Safe to archive**

These were one-time analysis scripts used during development:
- 47 `investigate_*`, `inspect_*`, `debug_*`, `find_*`, `query_*`, `show_*` files
- Examples: `investigate_18th_balmy.py`, `find_cardinal_directions.py`, `inspect_intersections_detailed.py`

**Recommendation:** Move to `archive/investigation_scripts/`

### 🔍 REVIEW - Validation (26 files - 88.80 KB)
**Validation scripts - Review before archiving**

These validate the current system. Keep if still useful for debugging:
- `verify_collection_fix.py` - Recent (2025-11-28)
- `validate_cardinal_directions.py` - Recent (2025-11-28)
- `check_18th_street_raw.py` - Recent (2025-11-28)
- Older validation scripts can likely be archived

**Recommendation:** Keep recent ones, archive older validation scripts

### 🧪 REVIEW - Tests (9 files - 33.60 KB)
**Test scripts - Archive if tests passing**

- `test_parking_regs.py`, `test_20th_street.py`, `test_mariposa.py`, etc.
- `quick_mission_analysis.py` - Analysis script

**Recommendation:** Archive if current system is working correctly

### 📦 ARCHIVE - Old Ingestion (3 files - 56.46 KB)
**Deprecated ingestion scripts - SAFE TO ARCHIVE**

- `ingest_data.py` - Replaced by `ingest_data_cnn_segments.py`
- `ingest_mission_only.py` - Mission-only version (deprecated)
- `create_master_cnn_join.py` - Old join approach (deprecated)

**Recommendation:** Move to `archive/old_ingestion/`

### 📝 REVIEW - Documentation (69 files - 574.28 KB)
**Documentation files - Keep current, archive outdated**

**KEEP (Current & Relevant):**
- `README.md` - Main documentation
- `AI_RESTRICTION_INTERPRETATION_SYSTEM.md` - Current system
- `USER_FRIENDLY_DISPLAY_IMPLEMENTATION_PLAN.md` - Current feature
- `CARDINAL_DIRECTION_INGESTION_ISSUE.md` - Known issue
- `DISPLAY_SYSTEM_IMPLEMENTATION_STATUS.md` - Current status

**ARCHIVE (Historical/Outdated):**
- Investigation summaries (20+ files)
- Old architecture docs (10+ files)
- Analysis output files (15+ .txt files)
- Mission-specific docs (now citywide)

**Recommendation:** Keep ~10 current docs, archive ~59 historical docs

### 🗑️ DELETE (1 file - 3.00 KB)
**Backup files - Safe to delete**

- `backup_database.py` - Backup script (not needed if using MongoDB backups)

## Recommended Actions

### Immediate Actions (Safe)

```bash
# Create archive directories
mkdir -p archive/{investigation_scripts,old_ingestion,old_docs,test_scripts}

# Archive investigation scripts (47 files)
mv investigate_*.py inspect_*.py debug_*.py find_*.py query_*.py show_*.py archive/investigation_scripts/

# Archive old ingestion scripts (3 files)
mv ingest_data.py ingest_mission_only.py create_master_cnn_join.py archive/old_ingestion/

# Archive test scripts (9 files)
mv test_*.py quick_*.py simple_*.py archive/test_scripts/

# Delete backup file
rm backup_database.py
```

### Review Before Archiving

**Validation Scripts:** Review these 26 files individually. Keep recent ones that are still useful:
- Keep: `verify_collection_fix.py`, `validate_cardinal_directions.py`, `check_18th_street_raw.py`
- Archive older ones: `verify_db.py`, `check_datasets_structure.py`, etc.

**Documentation:** Review 69 .md and .txt files:
- Keep ~10 current/relevant docs
- Archive ~59 historical/outdated docs to `archive/old_docs/`

## Space Savings

**Potential space savings:** ~400-500 KB (40-50% reduction)

After cleanup, you'll have:
- **~20-30 core files** (production + current validation)
- **~10 current documentation files**
- **~140 archived files** (available if needed, but out of the way)

## Next Steps

1. Review the generated `cleanup_old_files.sh` script
2. Manually review validation and documentation files
3. Execute cleanup (after review)
4. Commit cleaned-up structure to git

## Notes

- The ingestion in Terminal 16 is NOT affected by file cleanup
- All archived files remain available in `archive/` directory
- You can always restore files from git history if needed