#!/usr/bin/env python3
"""Monitor the progress of interpretation layer generation."""

import os
import time
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

# Load .env from backend directory
backend_dir = Path(__file__).parent
env_path = backend_dir / '.env'
load_dotenv(env_path)

# Connect to MongoDB
mongodb_uri = os.getenv('MONGODB_URI')
client = MongoClient(mongodb_uri)
db = client.curby

print("Monitoring interpretation layer generation progress...")
print("Press Ctrl+C to stop monitoring\n")

last_count = 0
start_time = time.time()

try:
    while True:
        total = db.street_segments.count_documents({})
        with_interp = db.street_segments.count_documents({'interpretation': {'$exists': True}})
        
        percentage = (with_interp / total * 100) if total > 0 else 0
        remaining = total - with_interp
        
        # Calculate rate
        if with_interp > last_count:
            elapsed = time.time() - start_time
            rate = (with_interp - last_count) / elapsed if elapsed > 0 else 0
            eta_seconds = remaining / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60
            
            print(f"\rProgress: {with_interp:,}/{total:,} ({percentage:.1f}%) | "
                  f"Remaining: {remaining:,} | "
                  f"Rate: {rate:.1f}/s | "
                  f"ETA: {eta_minutes:.1f} min", end='', flush=True)
            
            last_count = with_interp
            start_time = time.time()
        else:
            print(f"\rProgress: {with_interp:,}/{total:,} ({percentage:.1f}%) | "
                  f"Remaining: {remaining:,}", end='', flush=True)
        
        if with_interp >= total:
            print("\n\n✅ Interpretation layer generation complete!")
            break
            
        time.sleep(5)  # Check every 5 seconds
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped.")
finally:
    client.close()