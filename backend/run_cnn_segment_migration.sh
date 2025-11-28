#!/bin/bash

echo "=========================================="
echo "CNN SEGMENT MIGRATION SCRIPT"
echo "=========================================="
echo ""

# Activate virtual environment if it exists
if [ -d "../.venv" ]; then
    echo "Activating virtual environment..."
    source ../.venv/bin/activate
fi

echo "Step 1: Running new CNN segment ingestion..."
echo "----------------------------------------"
python3 ingest_data_cnn_segments.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Ingestion completed successfully!"
    echo ""
    echo "Step 2: Running validation..."
    echo "----------------------------------------"
    python3 validate_cnn_segments.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓✓✓ MIGRATION COMPLETE AND VALIDATED ✓✓✓"
        echo ""
        echo "Next steps:"
        echo "1. Review validation results above"
        echo "2. Test API endpoints"
        echo "3. Update frontend components"
    else
        echo ""
        echo "⚠ Validation failed. Review errors above."
    fi
else
    echo ""
    echo "✗ Ingestion failed. Review errors above."
    exit 1
fi