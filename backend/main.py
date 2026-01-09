#!/usr/bin/env python3
"""
Deployment wrapper for backward compatibility.
Actual code is in src/api/main.py

For local development, use: ./run.sh
"""

if __name__ == "__main__":
    import uvicorn
    # Run the app from the new location
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=False)