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
