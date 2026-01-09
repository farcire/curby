#!/usr/bin/env python3
"""
Wrapper script to run ingest_data_cnn_segments.py with progress monitoring
"""
import subprocess
import sys
import time
from datetime import datetime

def print_progress(message):
    """Print timestamped progress message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()

def main():
    print_progress("=" * 80)
    print_progress("STARTING CNN MASTER DATASET INGESTION")
    print_progress("=" * 80)
    print_progress("")
    print_progress("This will:")
    print_progress("  1. Fetch all San Francisco streets (~17,500 CNNs)")
    print_progress("  2. Create L/R segments (~35,000 segments)")
    print_progress("  3. Match parking regulations (spatial)")
    print_progress("  4. Match parking meters (blockface-based)")
    print_progress("  5. Match street sweeping (direct CNN+side)")
    print_progress("  6. Pre-compute all display strings")
    print_progress("  7. Save to MongoDB")
    print_progress("")
    print_progress("Expected runtime: 15-30 minutes")
    print_progress("=" * 80)
    print_progress("")
    
    start_time = time.time()
    
    # Run the ingestion script
    print_progress("Launching ingest_data_cnn_segments.py...")
    print_progress("")
    
    try:
        # Run with real-time output
        process = subprocess.Popen(
            [sys.executable, "ingest_data_cnn_segments.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream output line by line
        for line in process.stdout:
            print(line, end='')
            sys.stdout.flush()
        
        # Wait for completion
        return_code = process.wait()
        
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        print_progress("")
        print_progress("=" * 80)
        if return_code == 0:
            print_progress(f"✓ INGESTION COMPLETED SUCCESSFULLY in {minutes}m {seconds}s")
            print_progress("=" * 80)
            print_progress("")
            print_progress("Next steps:")
            print_progress("  1. Verify data in MongoDB")
            print_progress("  2. Test queries by CNN+side, address, or meter_id")
            print_progress("  3. Check pre-computed display strings")
            return 0
        else:
            print_progress(f"✗ INGESTION FAILED with exit code {return_code}")
            print_progress("=" * 80)
            return return_code
            
    except KeyboardInterrupt:
        print_progress("")
        print_progress("=" * 80)
        print_progress("✗ INGESTION INTERRUPTED BY USER")
        print_progress("=" * 80)
        return 1
    except Exception as e:
        print_progress("")
        print_progress("=" * 80)
        print_progress(f"✗ ERROR: {e}")
        print_progress("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())