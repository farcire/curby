#!/bin/bash
# Monitor the ingestion progress in real-time

LOG_FILE="ingestion_v2_run.log"

echo "Monitoring ingestion progress from $LOG_FILE"
echo "Press Ctrl+C to stop monitoring (ingestion will continue)"
echo "================================================"
echo ""

# Follow the log file
tail -f "$LOG_FILE" 2>/dev/null || echo "Log file not found yet. Waiting..."

# If tail fails, wait and try again
while [ ! -f "$LOG_FILE" ]; do
    sleep 2
done

tail -f "$LOG_FILE"