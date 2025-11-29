#!/bin/bash

# Navigate to the directory where the script is located
cd "$(dirname "$0")"

# Activate virtual environment
# Assuming .venv is in the parent directory of backend
source ../.venv/bin/activate

# Run the CNN-based ingestion script for full San Francisco
echo "Starting full San Francisco data ingestion..."
echo "This will fetch and process all SF streets, parking regulations, meters, and street cleaning schedules."
echo "Estimated time: 30-60 minutes"
echo ""
python ingest_data_cnn_segments.py
echo ""
echo "✓ Full San Francisco data ingestion completed!"