#!/bin/bash

echo "Monitoring ingestion progress..."
echo "Waiting for completion..."

# Wait for process to finish
while pgrep -f "ingest_data.py" > /dev/null; do
    sleep 3
    # Show last line of log if it exists
    if [ -f ingestion_spatial.log ]; then
        tail -1 ingestion_spatial.log 2>/dev/null
    fi
done

echo ""
echo "===== INGESTION COMPLETE ====="
echo ""
echo "Last 20 lines of log:"
tail -20 ingestion_spatial.log

echo ""
echo "===== RUNNING VERIFICATION ====="
source ../.venv/bin/activate
python quick_check.py
cat test_results.txt