#!/bin/bash

# Database backup script before CNN segment migration
# Date: November 28, 2024

set -e  # Exit on error

BACKUP_DIR="./database_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/pre_cnn_migration_${TIMESTAMP}"

echo "========================================"
echo "Database Backup Before CNN Migration"
echo "========================================"
echo ""
echo "Backup location: ${BACKUP_PATH}"
echo ""

# Load MongoDB URI from .env
source .env

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Backup using mongodump
echo "Starting backup..."
mongodump --uri="${MONGODB_URI}" --out="${BACKUP_PATH}"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Backup completed successfully!"
    echo "Backup saved to: ${BACKUP_PATH}"
    echo ""
    
    # Show backup size
    BACKUP_SIZE=$(du -sh "${BACKUP_PATH}" | cut -f1)
    echo "Backup size: ${BACKUP_SIZE}"
    echo ""
    
    # List collections backed up
    echo "Collections backed up:"
    ls -1 "${BACKUP_PATH}/curby" | grep -v "metadata.json" | sed 's/.bson$//' | sort
    echo ""
    
    # Save backup info
    echo "Backup created: ${TIMESTAMP}" > "${BACKUP_PATH}/backup_info.txt"
    echo "MongoDB URI: ${MONGODB_URI}" >> "${BACKUP_PATH}/backup_info.txt"
    echo "Purpose: Pre CNN-segment migration" >> "${BACKUP_PATH}/backup_info.txt"
    echo "Current system: Blockface-based (7.4% coverage)" >> "${BACKUP_PATH}/backup_info.txt"
    echo "Next step: Migrate to CNN-segment architecture" >> "${BACKUP_PATH}/backup_info.txt"
    
    echo "========================================"
    echo "Ready to proceed with migration"
    echo "========================================"
else
    echo ""
    echo "❌ Backup failed!"
    echo "Please check MongoDB connection and try again"
    exit 1
fi