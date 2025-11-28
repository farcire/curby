#!/bin/bash

# Check if ingestion process is running
if pgrep -f "ingest_data.py" > /dev/null; then
    echo "✓ Ingestion process is still running..."
    echo ""
    echo "Latest log output:"
    tail -n 20 backend/ingestion_spatial_fixed.log 2>/dev/null || tail -n 20 ingestion_spatial_fixed.log
    echo ""
    echo "To monitor in real-time, run:"
    echo "  tail -f backend/ingestion_spatial_fixed.log"
else
    echo "✓ Ingestion process has completed!"
    echo ""
    echo "Full log output:"
    cat backend/ingestion_spatial_fixed.log 2>/dev/null || cat ingestion_spatial_fixed.log
    echo ""
    echo "Next steps:"
    echo "  1. cd backend && source ../.venv/bin/activate"
    echo "  2. python quick_check.py"
    echo "  3. cat test_results.txt"
fi