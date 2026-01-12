# Stable Data Architecture Recommendation

**Date:** December 29, 2024  
**Issue:** Frequent re-ingestion required, knowledge loss between ingestions  
**Recommendation:** Maintain a stable, versioned master database

---

## Current Problem

### Issues with Current Architecture
1. **Repeated Ingestion:** Must re-fetch from SFMTA APIs every time
2. **Knowledge Loss:** Complex ingestion logic must be re-learned/re-executed
3. **Fragility:** Any API changes or network issues break the system
4. **Time Cost:** 30-45 minutes per ingestion
5. **Data Drift:** SFMTA data rarely changes, but you're treating it as volatile

### Current Flow (Problematic)
```
SFMTA APIs (10 datasets)
    ↓ (fetch every time)
Ingestion Script (30-45 min)
    ↓ (complex merging)
MongoDB (temporary)
    ↓
Application
```

---

## Recommended Architecture

### Stable Master Database Approach

```
┌─────────────────────────────────────────────────────────┐
│ ONE-TIME INGESTION (Do Once, Version Control)          │
├─────────────────────────────────────────────────────────┤
│ SFMTA APIs → Ingestion Script → Master MongoDB         │
│                                                          │
│ Output: Clean, merged, enriched dataset                │
│ - 34,292 segments with all rules attached              │
│ - Pre-computed display strings                         │
│ - AI interpretations cached                            │
│ - Spatial indexes created                              │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ EXPORT & VERSION CONTROL                                │
├─────────────────────────────────────────────────────────┤
│ 1. Export to JSON/BSON dump                            │
│ 2. Store in Git LFS or cloud storage                   │
│ 3. Tag with version (e.g., v2024-12-29)                │
│ 4. Document what changed from previous version         │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ DEPLOYMENT (Fast, Reliable)                            │
├─────────────────────────────────────────────────────────┤
│ 1. Download versioned database dump                    │
│ 2. Restore to MongoDB (< 5 minutes)                    │
│ 3. Application ready immediately                       │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Create Master Database (One-Time)

**Step 1: Run Final Ingestion**
```bash
cd backend
python ingest_data_cnn_segments.py 2>&1 | tee final_ingestion.log
```

**Step 2: Export Database**
```bash
# Export entire database
mongodump --uri="$MONGODB_URI" --out=./curby_master_db_2024-12-29

# Or export just the critical collections
mongodump --uri="$MONGODB_URI" \
  --collection=street_segments \
  --collection=parking_regulations \
  --collection=street_cleaning_schedules \
  --out=./curby_master_db_2024-12-29
```

**Step 3: Compress and Store**
```bash
# Compress for storage
tar -czf curby_master_db_2024-12-29.tar.gz curby_master_db_2024-12-29/

# Upload to cloud storage (choose one)
# Option A: AWS S3
aws s3 cp curby_master_db_2024-12-29.tar.gz s3://your-bucket/curby-data/

# Option B: Google Cloud Storage
gsutil cp curby_master_db_2024-12-29.tar.gz gs://your-bucket/curby-data/

# Option C: Git LFS (if < 2GB)
git lfs track "*.tar.gz"
git add curby_master_db_2024-12-29.tar.gz
git commit -m "Add master database v2024-12-29"
```

### Phase 2: Update Deployment Process

**Create Restore Script** (`backend/restore_master_db.sh`):
```bash
#!/bin/bash
set -e

VERSION=${1:-"2024-12-29"}
DB_FILE="curby_master_db_${VERSION}.tar.gz"

echo "Restoring Curby master database version: $VERSION"

# Download from cloud storage
if [ ! -f "$DB_FILE" ]; then
    echo "Downloading database dump..."
    # Choose your storage method
    # aws s3 cp "s3://your-bucket/curby-data/$DB_FILE" .
    # OR
    # gsutil cp "gs://your-bucket/curby-data/$DB_FILE" .
fi

# Extract
echo "Extracting database..."
tar -xzf "$DB_FILE"

# Restore to MongoDB
echo "Restoring to MongoDB..."
mongorestore --uri="$MONGODB_URI" \
  --drop \
  --dir="curby_master_db_${VERSION}/curby"

echo "✓ Database restored successfully!"
echo "✓ Application ready to use"

# Cleanup
rm -rf "curby_master_db_${VERSION}"
```

**Update Deployment** (`.github/workflows/deploy.yml` or similar):
```yaml
- name: Restore Master Database
  run: |
    chmod +x backend/restore_master_db.sh
    ./backend/restore_master_db.sh 2024-12-29
```

### Phase 3: Incremental Updates (When SFMTA Data Changes)

**Create Update Script** (`backend/update_master_db.sh`):
```bash
#!/bin/bash
set -e

OLD_VERSION=${1:-"2024-12-29"}
NEW_VERSION=$(date +%Y-%m-%d)

echo "Creating new master database version: $NEW_VERSION"
echo "Based on: $OLD_VERSION"

# 1. Restore old version
./restore_master_db.sh "$OLD_VERSION"

# 2. Run incremental update (only fetch changed data)
python update_changed_data.py

# 3. Export new version
mongodump --uri="$MONGODB_URI" --out="./curby_master_db_${NEW_VERSION}"
tar -czf "curby_master_db_${NEW_VERSION}.tar.gz" "curby_master_db_${NEW_VERSION}/"

# 4. Upload new version
# aws s3 cp "curby_master_db_${NEW_VERSION}.tar.gz" s3://your-bucket/curby-data/

echo "✓ New version created: $NEW_VERSION"
```

---

## Benefits of This Approach

### 1. **Reliability**
- ✅ No dependency on SFMTA API availability
- ✅ No network issues during deployment
- ✅ Consistent data across all environments

### 2. **Speed**
- ✅ Deployment: < 5 minutes (vs 30-45 minutes)
- ✅ No complex ingestion logic to re-run
- ✅ Immediate application startup

### 3. **Version Control**
- ✅ Track exactly what data is in production
- ✅ Easy rollback to previous versions
- ✅ Document changes between versions
- ✅ Test new data before deploying

### 4. **Cost Savings**
- ✅ No repeated SFMTA API calls
- ✅ Faster deployments = less compute time
- ✅ Reduced MongoDB Atlas usage

### 5. **Knowledge Preservation**
- ✅ Ingestion logic runs once, results preserved
- ✅ AI interpretations cached permanently
- ✅ Manual overrides maintained
- ✅ No "forgetting" between deployments

---

## Data Update Strategy

### When to Update Master Database

**Quarterly Updates (Recommended)**
```
Q1: January 1
Q2: April 1
Q3: July 1
Q4: October 1
```

**Or Event-Driven Updates**
- SFMTA announces regulation changes
- New parking meters installed
- Street cleaning schedule changes
- User reports indicate data issues

### Update Process

1. **Check for Changes**
   ```bash
   python check_sfmta_changes.py --since=2024-12-29
   ```

2. **Run Incremental Update**
   ```bash
   ./update_master_db.sh 2024-12-29
   ```

3. **Test New Version**
   ```bash
   # Restore to staging environment
   ./restore_master_db.sh 2025-01-15 --env=staging
   
   # Run validation tests
   python validate_data_quality.py
   ```

4. **Deploy to Production**
   ```bash
   ./restore_master_db.sh 2025-01-15 --env=production
   ```

---

## File Structure

```
backend/
├── database_dumps/
│   ├── curby_master_db_2024-12-29.tar.gz
│   ├── curby_master_db_2025-01-15.tar.gz
│   └── CHANGELOG.md
├── restore_master_db.sh
├── update_master_db.sh
├── check_sfmta_changes.py
├── validate_data_quality.py
└── ingest_data_cnn_segments.py  # Keep for major updates
```

---

## Migration Steps

### Step 1: Create Initial Master Database (This Week)
```bash
# Run final ingestion
cd backend
python ingest_data_cnn_segments.py

# Export
mongodump --uri="$MONGODB_URI" --out=./curby_master_db_2024-12-29
tar -czf curby_master_db_2024-12-29.tar.gz curby_master_db_2024-12-29/

# Store (choose your method)
# Upload to S3/GCS or commit to Git LFS
```

### Step 2: Test Restore Process
```bash
# Create restore script
cat > restore_master_db.sh << 'EOF'
#!/bin/bash
VERSION=${1:-"2024-12-29"}
tar -xzf "curby_master_db_${VERSION}.tar.gz"
mongorestore --uri="$MONGODB_URI" --drop --dir="curby_master_db_${VERSION}/curby"
rm -rf "curby_master_db_${VERSION}"
EOF

chmod +x restore_master_db.sh

# Test it
./restore_master_db.sh 2024-12-29
```

### Step 3: Update Deployment Scripts
- Remove `run_ingestion.sh` from deployment
- Add `restore_master_db.sh` to deployment
- Update documentation

### Step 4: Document Version
Create `database_dumps/CHANGELOG.md`:
```markdown
# Curby Master Database Changelog

## v2024-12-29
- Initial master database
- 34,292 street segments
- All SFMTA datasets integrated
- AI interpretations for ~500 unique regulations
- Manual overrides applied
```

---

## Monitoring & Maintenance

### Monthly Check
```bash
# Check if SFMTA data has changed
python check_sfmta_changes.py --since=$(cat LAST_UPDATE_DATE)
```

### Quarterly Update
```bash
# Create new version
./update_master_db.sh $(cat LAST_UPDATE_DATE)

# Test
./restore_master_db.sh $(date +%Y-%m-%d) --env=staging
python validate_data_quality.py

# Deploy
./restore_master_db.sh $(date +%Y-%m-%d) --env=production

# Update tracking
date +%Y-%m-%d > LAST_UPDATE_DATE
```

---

## Cost Analysis

### Current Approach
- Ingestion time: 30-45 min per deployment
- SFMTA API calls: 10 datasets × multiple requests
- MongoDB compute: High during ingestion
- Developer time: Debugging ingestion issues

### Stable Database Approach
- Deployment time: < 5 minutes
- SFMTA API calls: Only during quarterly updates
- MongoDB compute: Minimal (just restore)
- Developer time: Minimal maintenance

**Estimated Savings:** 80-90% reduction in deployment time and complexity

---

## Conclusion

**Recommendation:** Implement stable master database architecture immediately.

**Benefits:**
1. ✅ Eliminate repeated ingestion
2. ✅ Preserve knowledge between deployments
3. ✅ Faster, more reliable deployments
4. ✅ Version-controlled data
5. ✅ Reduced costs and complexity

**Next Steps:**
1. Run final ingestion this week
2. Export and store master database
3. Create restore script
4. Update deployment process
5. Schedule quarterly updates

---

**Document Status:** Ready for Implementation  
**Priority:** High - Solves core architectural issue  
**Estimated Effort:** 1-2 days initial setup, minimal ongoing maintenance