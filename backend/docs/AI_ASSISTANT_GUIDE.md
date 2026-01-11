# AI Assistant Documentation Guide

**For: Claude, ChatGPT, Cursor, Copilot, and all AI coding agents**  
**Last Updated:** January 11, 2026  
**Purpose:** Ensure consistent documentation practices across all AI assistants

---

## 👤 User-Specific Paths

**Project Root:** `/Users/ssp/Desktop/snapdev-apps/elegant-lynx-play/`  
**Backend:** `/Users/ssp/Desktop/snapdev-apps/elegant-lynx-play/backend/`  
**Docs:** `/Users/ssp/Desktop/snapdev-apps/elegant-lynx-play/backend/docs/`  
**Downloads:** `/Users/ssp/Downloads/`

**When files are downloaded from Claude:**
```bash
cd /Users/ssp/Downloads
# Files will be here - move them to appropriate location
cp [filename] /Users/ssp/Desktop/snapdev-apps/elegant-lynx-play/backend/docs/
```

---

## 🎯 Core Principle

**UPDATE, DON'T DUPLICATE**

- Always check if documentation already exists before creating new files
- Update existing files rather than creating new versions
- Never create "v2", "updated", "final", or timestamped duplicates
- One canonical file per topic

---

## 📁 Directory Structure & File Placement

### Documentation Lives in `backend/docs/`

```
docs/
├── README.md                     # Main navigation hub
│
├── current/                      # Production systems running NOW
│   ├── INDEX.md
│   └── [8 files describing active production systems]
│
├── reference/
│   ├── guides/                  # How-to documentation
│   │   ├── INDEX.md
│   │   └── [12 files: step-by-step instructions]
│   ├── specs/                   # Technical specifications
│   │   ├── INDEX.md
│   │   └── [11 files: architecture, design]
│   └── status/                  # Status reports & fixes
│       ├── INDEX.md
│       └── [13 files: bug fixes, reports]
│
├── completed/                    # Historical implementations
│   ├── INDEX.md
│   └── [14 files: past work summaries]
│
├── investigations/               # Research & analysis
│   ├── INDEX.md
│   └── [11 files: root cause analysis]
│
└── archive/                      # Obsolete (40+ days old)
    ├── INDEX.md
    └── [10 files: superseded docs]
```

---

## 🔍 Before Creating ANY Documentation

### Step 1: Search for Existing Files

**ALWAYS run this search first:**

```bash
# Search for existing documentation on topic
grep -r "your_topic" docs/ --include="*.md"

# Check if file already exists
ls docs/**/*topic*.md

# Read relevant INDEX files
cat docs/current/INDEX.md
cat docs/reference/guides/INDEX.md
```

### Step 2: Decision Tree

```
Does documentation on this topic exist?
├─ YES → UPDATE the existing file
│   ├─ Add new section
│   ├─ Update outdated info
│   └─ Mark old info as superseded
│
└─ NO → Check if it SHOULD exist
    ├─ Is this temporary? → Don't create a file, use comments in code
    ├─ Is this a one-time thing? → Don't create a file
    └─ Is this needed long-term? → Create NEW file (follow naming below)
```

---

## 📝 File Naming Convention

### Format: `[TYPE]_[TOPIC]_[VARIANT].md`

### Types (Prefix):

| Type | When to Use | Example |
|------|-------------|---------|
| `ARCH_` | System architecture, design | `ARCH_regulation_normalization_current.md` |
| `GUIDE_` | Step-by-step how-to | `GUIDE_day_time_normalization.md` |
| `SPEC_` | Technical specification | `SPEC_ingestion_architecture.md` |
| `STATUS_` | Status report, bug fix | `STATUS_meter_matching_fixed.md` |
| `INVESTIGATION_` | Research, analysis | `INVESTIGATION_fuzzy_matching_abandoned.md` |
| `SUMMARY_` | Implementation summary | `SUMMARY_alternate_schedules_dec2024.md` |

### Variants (Suffix):

| Variant | When to Use |
|---------|-------------|
| `_current` | Current production system |
| `_[date]` | Dated historical doc (e.g., `_jan2026`, `_dec2024`) |
| `_[status]` | Status indicator (e.g., `_fixed`, `_abandoned`, `_planned`) |
| *(none)* | Timeless guide or spec |

### Naming Rules:

1. **Lowercase only** (except TYPE prefix)
2. **Underscores** separate words (not hyphens, not spaces)
3. **No version numbers** (v2, v3, final, updated)
4. **No dates in middle** (dates only as suffix if historical)
5. **Descriptive but concise** (2-4 words for topic)

### Examples:

✅ **GOOD:**
```
ARCH_regulation_normalization_current.md
GUIDE_day_time_normalization.md
STATUS_meter_matching_fixed_dec2024.md
INVESTIGATION_fuzzy_matching_abandoned.md
SPEC_ingestion_12step.md
```

❌ **BAD:**
```
RegulationNormalizationCompleteV2Final.md  # Too many issues
regulation-normalization.md                # Missing type prefix
GUIDE_how_to_normalize_days_and_times_2024.md  # Too long
meter_fix_v2_updated.md                    # Version numbers
Day_Time_NORMALIZATION_guide.md            # Inconsistent casing
```

---

## 🗂️ Choosing the Right Directory

### Decision Matrix:

| If the document describes... | Put it in... | Example |
|------------------------------|--------------|---------|
| System running in production NOW | `current/` | `ARCH_regulation_normalization_current.md` |
| How to use a current system | `reference/guides/` | `GUIDE_day_time_normalization.md` |
| Technical architecture/design | `reference/specs/` | `SPEC_ingestion_architecture.md` |
| A bug fix or status report | `reference/status/` | `STATUS_meter_matching_fixed.md` |
| A completed past implementation | `completed/` | `SUMMARY_alternate_schedules_dec2024.md` |
| Research or root cause analysis | `investigations/` | `INVESTIGATION_king_st_cnn.md` |
| Obsolete (40+ days old) | `archive/` | *(move existing obsolete files here)* |

### Rules:

1. **"Current" = Running NOW** (not "recently completed")
2. **"Completed" = Done and in production** (historical record)
3. **"Status" = Bug fixes, reports** (even if recent)
4. **When in doubt:** Put in `reference/` (easier to move later)

---

## ✏️ Updating Existing Documentation

### When Updating a File:

```markdown
# Document Title

**Last Updated:** January 11, 2026  
**Status:** ✅ CURRENT | 🚧 IN PROGRESS | ⏳ PLANNED | ❌ OBSOLETE

---

## Recent Updates

### January 11, 2026
- Added section on XYZ
- Updated ABC with new approach
- Deprecated old method (see Archive section)

---

[Main content...]

---

## Archive

### Superseded Information

**Old approach (deprecated Jan 11, 2026):**
[Keep old info here for context, marked as deprecated]
```

### Update Checklist:

- [ ] Add "Last Updated" date at top
- [ ] Add entry to "Recent Updates" section
- [ ] Update relevant INDEX.md file
- [ ] Mark old information as deprecated (don't delete!)
- [ ] Update any cross-references in other docs

---

## 🚫 What NOT to Document

### Don't Create Files For:

1. **Temporary investigations** → Use code comments or terminal output
2. **One-time scripts** → Document in script header comments
3. **Debug output** → Keep in terminal, don't save
4. **Personal notes** → Keep in external notes app
5. **Work-in-progress** → Use TODO comments in code
6. **Meeting notes** → Unless project-critical decisions

### Exception:

Create documentation if:
- Multiple people need to reference it
- It affects system design
- It explains a non-obvious decision
- It's needed for onboarding

---

## 📋 Documentation Standards

### File Structure (Template):

```markdown
# Document Title

**Type:** [Guide/Spec/Investigation/etc]  
**Last Updated:** [Date]  
**Status:** [Current/Completed/Obsolete]

---

## Overview

[1-2 sentence summary of what this doc covers]

---

## [Main Sections]

[Clear headers, concise content]

---

## Related Documentation

- [`docs/current/ARCH_main_system.md`](../current/ARCH_main_system.md)
- [`docs/reference/guides/GUIDE_related_topic.md`](GUIDE_related_topic.md)

---

**Last reviewed:** [Date]
```

### Writing Style:

- ✅ **Concise** - Get to the point quickly
- ✅ **Active voice** - "The system processes..." not "Processing is done by..."
- ✅ **Specific** - Include actual file names, line numbers, commands
- ✅ **Scannable** - Use headers, bullets, tables
- ❌ **No fluff** - Avoid "As we all know..." or "Obviously..."
- ❌ **No redundancy** - Don't repeat what's in another doc, link to it

### Headers:

```markdown
# H1: Document Title (one per file)
## H2: Main Sections
### H3: Subsections
#### H4: Details (use sparingly)
```

### Code Examples:

```markdown
**Always include:**
- Language identifier
- Context (what it does)
- Full working example (not fragments)

```python
# Good: Full working example with context
def normalize_day(day_string: str) -> int:
    """Convert day name to integer (0=Monday, 6=Sunday)."""
    days = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 
            'fri': 4, 'sat': 5, 'sun': 6}
    return days.get(day_string[:3].lower(), -1)
```

❌ **Bad:**
```
# Fragment without context
return days.get(day_string[:3].lower())
```
```

---

## 🔄 INDEX.md Maintenance

### When to Update INDEX Files:

**ALWAYS update the relevant INDEX.md when you:**
- Add a new file to a directory
- Update an important file (mark with ✅ Updated [Date])
- Move a file between directories
- Mark a file as obsolete

### INDEX.md Template:

```markdown
# [Directory Name]

**Last Updated:** [Date]  
**File Count:** [N files]

---

## Quick Reference

**[Most Common Question]?** → [FILE_NAME.md]
**[Second Common Question]?** → [FILE_NAME.md]

---

## Files in This Directory

### [Category 1]
- **[FILE_NAME.md]** - Brief description
- **[FILE_NAME.md]** - Brief description

### [Category 2]
- **[FILE_NAME.md]** - Brief description

---

**See also:** [`../other_directory/`](../other_directory/)
```

---

## 🤖 AI Assistant Checklist

### Before Creating ANY File:

```bash
# 1. Search existing docs
grep -r "topic" docs/ --include="*.md"

# 2. Check INDEX files
cat docs/*/INDEX.md | grep -i "topic"

# 3. Ask yourself:
# - Does this already exist? (→ UPDATE it)
# - Is this temporary? (→ DON'T document)
# - Is this needed long-term? (→ CREATE with proper naming)
```

### When Creating a New File:

- [ ] Searched for existing documentation
- [ ] Chose correct directory (see decision matrix)
- [ ] Used proper naming convention (`[TYPE]_[topic]_[variant].md`)
- [ ] Included file header (Type, Last Updated, Status)
- [ ] Added entry to relevant INDEX.md
- [ ] Added cross-references to related docs
- [ ] Committed with descriptive message

### When Updating a File:

- [ ] Updated "Last Updated" date
- [ ] Added entry to "Recent Updates" section
- [ ] Marked old info as deprecated (didn't delete)
- [ ] Updated INDEX.md if significance changed
- [ ] Updated cross-references if structure changed
- [ ] Committed with message: `docs: update [FILE] - [what changed]`

---

## 💬 Commit Message Format

### For Documentation Changes:

```bash
# New file
git commit -m "docs: add [TYPE]_[topic] - [what it covers]

- Created [directory]/[FILE_NAME.md]
- Added to [directory]/INDEX.md
- [Any other relevant changes]"

# Update file
git commit -m "docs: update [FILE] - [what changed]

- Updated [section] with [new info]
- Deprecated [old approach]
- [Any other relevant changes]"

# Move/rename file
git commit -m "docs: reorganize [files] - [why]

- Moved [OLD] to [NEW]
- Updated INDEX.md files
- Updated cross-references"
```

### Examples:

✅ **GOOD:**
```
docs: add GUIDE_day_time_normalization - parsing guide

- Created reference/guides/GUIDE_day_time_normalization.md
- Documents how to use regulation_normalizer.py
- Added to reference/guides/INDEX.md
```

```
docs: update ARCH_ingestion_current - add step 12

- Added new meter policy step
- Updated flow diagram
- Marked old 11-step process as deprecated
```

❌ **BAD:**
```
updated docs
```

```
docs: added new file for day time stuff
```

---

## 📊 Quick Reference Card

### I need to document...

| Scenario | Action | Directory | Example Name |
|----------|--------|-----------|--------------|
| Current production system | UPDATE if exists, CREATE if new | `current/` | `ARCH_[system]_current.md` |
| How to use a feature | UPDATE guide if exists | `reference/guides/` | `GUIDE_[feature].md` |
| Technical architecture | UPDATE spec if exists | `reference/specs/` | `SPEC_[component].md` |
| Bug fix I just did | CREATE new | `reference/status/` | `STATUS_[issue]_fixed.md` |
| Research findings | CREATE new | `investigations/` | `INVESTIGATION_[topic].md` |
| Completed implementation | CREATE new | `completed/` | `SUMMARY_[feature]_[date].md` |
| One-time debug output | DON'T DOCUMENT | *(terminal only)* | N/A |
| Work in progress | DON'T DOCUMENT | *(code comments)* | N/A |

---

## 🎯 Key Principles (Memorize These)

1. **UPDATE > CREATE** - Always check if doc exists first
2. **ONE CANONICAL FILE** - Never create v2, final, updated versions
3. **DESCRIPTIVE NAMES** - `GUIDE_day_time_normalization.md` not `guide.md`
4. **CURRENT = NOW** - Only production systems in `current/`
5. **UPDATE INDEX** - Always update INDEX.md when adding/changing files
6. **LINK, DON'T DUPLICATE** - Reference other docs, don't copy content
7. **DEPRECATE, DON'T DELETE** - Mark old info as superseded, keep for context
8. **MINIMAL DOCS** - If it doesn't need to be documented, don't document it

---

## 📞 When In Doubt

1. **Ask the user** which directory/name to use
2. **Search existing docs** before creating anything
3. **Update existing** rather than create new
4. **Check INDEX.md** files for guidance
5. **Follow examples** from similar existing docs

---

## 🔗 Related Files

- **Main Navigation:** [`docs/README.md`](README.md)
- **Current Systems:** [`docs/current/INDEX.md`](current/INDEX.md)
- **All INDEX Files:** Check each directory's `INDEX.md`

---

**This is the single source of truth for documentation standards.**  
**All AI assistants must follow these guidelines.**

Last Updated: January 11, 2026
