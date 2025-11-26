#!/bin/bash

# Navigate to the directory where the script is located
cd "$(dirname "$0")"

# Activate virtual environment
# Assuming .venv is in the parent directory of backend
source ../.venv/bin/activate

# Run the ingestion script
echo "Starting data ingestion..."
python ingest_data.py
echo "Data ingestion completed."