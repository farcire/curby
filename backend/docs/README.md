# Documentation Guide

**Last Updated:** January 12, 2026
**Total:** 78 markdown files organized by content and purpose

---

## 🚀 Quick Start

**New to the project?** Read these in order:

1. [`current/INDEX.md`](current/INDEX.md) - Overview of 8 essential production docs
2. [`current/CNN_MASTER_REFERENCE_ARCHITECTURE.md`](current/CNN_MASTER_REFERENCE_ARCHITECTURE.md) - System architecture
3. [`current/REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md`](current/REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md) - How regulations work
4. [`current/INGESTION_REFACTORING_COMPLETE_SUMMARY.md`](current/INGESTION_REFACTORING_COMPLETE_SUMMARY.md) - How data loads
5. [`current/PROJECT_HISTORY.md`](current/PROJECT_HISTORY.md) - Why decisions were made

**Looking for something specific?** Each directory has an `INDEX.md` file to help navigate.

---

## 📁 Directory Structure

```
docs/
├── README.md (you are here)
│
├── current/                      # 8 files - PRODUCTION SYSTEMS
│   ├── INDEX.md                 # ← Start here
│   ├── CNN_MASTER_REFERENCE_ARCHITECTURE.md
│   ├── REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md (Jan 1)
│   ├── INGESTION_REFACTORING_COMPLETE_SUMMARY.md (Jan 5)
│   ├── BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md
│   ├── MONGODB_COLLECTION_ARCHITECTURE.md
│   ├── DATA_QUALITY_ISSUES.md (updated Jan 4)
│   ├── DATA_QUALITY_LOG.md (updated Jan 7)
│   └── PROJECT_HISTORY.md
│
├── reference/                    # 37 files - HOW TO USE
│   ├── guides/INDEX.md          # 13 how-to guides
│   ├── specs/INDEX.md           # 11 technical specs
│   └── status/INDEX.md          # 13 status reports & fixes
│
├── completed/INDEX.md            # 14 implementation summaries
├── investigations/INDEX.md       # 11 research documents
└── archive/INDEX.md              # 10 obsolete docs
```

---

## 🎯 How to Navigate

### By Role

**Developer (New)?**
→ Start with [`current/INDEX.md`](current/INDEX.md)

**Debugging Issue?**
→ Check [`current/DATA_QUALITY_LOG.md`](current/DATA_QUALITY_LOG.md) (updated yesterday!)  
→ Browse [`reference/status/`](reference/status/)

**Need How-To?**
→ Browse [`reference/guides/INDEX.md`](reference/guides/INDEX.md)

**Understanding Architecture?**
→ Read [`reference/specs/INDEX.md`](reference/specs/INDEX.md)

**Historical Context?**
→ Check [`completed/INDEX.md`](completed/INDEX.md)

### By Question

| Question | Document |
|----------|----------|
| How do I set up locally? | `reference/guides/GUIDE_development_setup.md` |
| How do I deploy to production? | `reference/guides/GUIDE_deployment_quickref.md` |
| How does ingestion work? | `current/INGESTION_REFACTORING_COMPLETE_SUMMARY.md` |
| How do I parse days/times? | `reference/guides/DAY_TIME_NORMALIZATION_GUIDE.md` |
| What's the database schema? | `current/MONGODB_COLLECTION_ARCHITECTURE.md` |
| Why did we abandon fuzzy matching? | `reference/status/FUZZY_MATCHING_VALIDATION_SUMMARY.md` |
| How are regulations normalized? | `current/REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md` |
| What are known issues? | `current/DATA_QUALITY_ISSUES.md` + `DATA_QUALITY_LOG.md` |

---

## 📊 Current Production Metrics

From **INGESTION_REFACTORING_COMPLETE_SUMMARY.md** (Jan 5, 2026):
- Total segments: **34,324**
- With meters: **3,763** (11%)
- With regulations: **23,794** (69.3%)
- With street sweeping: **22,574** (65.8%)
- Meter matching: **100%** success
- Meter schedules: **72.8%** coverage

From **BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md** (Dec 30, 2024):
- Calibrated offset: **5.55 meters** (learned from 34,324 meters)
- Synthetic blockfaces: **31,930** (93%)
- Deterministic blockfaces: **2,394** (7%)

---

## 🗂️ Organization Principles

**This organization is based on CONTENT, not file names.**

### current/ = Production Systems (Running NOW)
- Recent dates (Jan 2026)
- Status: ✅ COMPLETE IMPLEMENTATION
- Referenced by code in `../src/`

### reference/ = How to Use Current Systems
- **guides/** - Step-by-step instructions
- **specs/** - Technical architecture
- **status/** - Bug fixes and reports

### completed/ = Historical Record
- What was built and when
- Implementation summaries
- Recently finished work

### investigations/ = Research
- Root cause analysis
- Pattern investigations
- Location-specific deep dives

### archive/ = Obsolete
- 40+ days old
- Superseded by newer docs
- Abandoned approaches

---

## ⚠️ Important Note: File Names

**File names have NOT been standardized yet** (Phase 2 coming in 1-2 weeks).

**Current state:**
- Files organized by CONTENT (location)
- Names reflect original purpose
- Example: "COMPLETE_SUMMARY" could be current production OR historical

**Why "COMPLETE" files are in different folders:**
- Recent "COMPLETE" (< 10 days) = **current/** (production NOW)
- Older "COMPLETE" (> 10 days) = **completed/** (historical)

**Phase 2 will standardize names to match content:**
- `ARCH_regulation_normalization_current.md`
- `GUIDE_day_time_normalization.md`
- `INVESTIGATION_fuzzy_matching_abandoned.md`

---

## 🔗 Related Documentation

**In the backend:**
- [`../README.md`](../README.md) - Backend overview, API, configuration
- [`../src/core/regulation_normalizer.py`](../src/core/regulation_normalizer.py) - Core business logic (2,335 lines)
- [`../scripts/`](../scripts/) - 174 utility scripts

**Key production code:**
- `../src/api/main.py` - FastAPI server (419 lines)
- `../src/api/models.py` - Pydantic models (117 lines)

---

## 📞 Common Searches

Can't find something? Try these patterns:

**Search by topic:**
```bash
# In backend/docs/
grep -r "meter schedules" . --include="*.md"
grep -r "street sweeping" . --include="*.md"
grep -r "blockface" . --include="*.md"
```

**Check INDEX files first:**
- Each directory has an INDEX.md with quick links
- Start with the INDEX, then drill down

**Still stuck?**
- Read `current/PROJECT_HISTORY.md` for context
- Check the INDEX.md in relevant directory
- Search for keywords in file names

---

**Organization completed:** January 11, 2026
**Last updated:** January 12, 2026 (added deployment guide)
**Method:** Content analysis of all 78 files (not just names)
**Next:** Phase 2 naming standardization (in 1-2 weeks)
