#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Starting Parking Regulation API..."
uvicorn src.api.main:app --reload --port 8000
