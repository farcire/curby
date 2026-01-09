#!/usr/bin/env python3
"""
Root-level deployment wrapper.
Runs the backend API from backend/src/api/main.py
"""

import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_path)

if __name__ == "__main__":
    import uvicorn
    # Run the backend API
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=False)