#!/usr/bin/env python3
"""
Check the progress of the refactored ingestion script
"""
import os
import time
from datetime import datetime

LOG_FILE = "ingestion_v2_run.log"

def check_progress():
    """Check current progress from log file"""
    if not os.path.exists(LOG_FILE):
        print("❌ Log file not found yet. Ingestion may not have started.")
        return
    
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
    
    if len(lines) <= 2:
        print("⏳ Ingestion starting... (only SSL warning so far)")
        return
    
    print(f"📊 Ingestion Progress Report")
    print(f"{'='*60}")
    print(f"Log file: {LOG_FILE}")
    print(f"Total lines: {len(lines)}")
    print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Look for key progress indicators
    steps_completed = []
    current_step = None
    
    for line in lines:
        line = line.strip()
        
        # Check for step completions
        if "STEP 1:" in line or "Creating CNN-Based Street Segments" in line:
            current_step = "Step 1: Streets"
        elif "STEP 2:" in line or "Intersections" in line:
            current_step = "Step 2: Intersections"
        elif "STEP 3:" in line or "Matching Parking Meters" in line:
            current_step = "Step 3: Meters"
        elif "STEP 4:" in line or "Blockfaces with Meters" in line:
            current_step = "Step 4: Blockfaces with Meters"
        elif "STEP 5:" in line or "Synthetic Blockfaces" in line:
            current_step = "Step 5: Synthetic Blockfaces"
        elif "STEP 6:" in line or "Meter Operating Schedules" in line:
            current_step = "Step 6: Meter Schedules"
        elif "STEP 7:" in line or "Parking Regulations" in line:
            current_step = "Step 7: Regulations"
        elif "STEP 8:" in line or "Street Sweeping" in line:
            current_step = "Step 8: Street Sweeping"
        elif "STEP 9:" in line or "Manual Overrides" in line:
            current_step = "Step 9: Manual Overrides"
        elif "STEP 10:" in line or "Aggregate" in line:
            current_step = "Step 10: Aggregate"
        elif "STEP 11:" in line or "Cardinal Direction" in line:
            current_step = "Step 11: Cardinal"
        elif "STEP 12:" in line or "Saving Street Segments" in line:
            current_step = "Step 12: Save to DB"
        
        # Check for completion markers
        if "✓" in line and current_step:
            if current_step not in steps_completed:
                steps_completed.append(current_step)
    
    # Display progress
    if steps_completed:
        print("✅ Completed Steps:")
        for step in steps_completed:
            print(f"   {step}")
        print()
    
    if current_step:
        print(f"⏳ Current Step: {current_step}\n")
    
    # Show last 10 lines
    print("📝 Last 10 lines of output:")
    print("-" * 60)
    for line in lines[-10:]:
        print(line.rstrip())
    print("-" * 60)
    
    # Check for errors
    errors = [line for line in lines if "ERROR" in line or "Error" in line or "Failed" in line]
    if errors:
        print(f"\n⚠️  Found {len(errors)} potential errors:")
        for error in errors[-5:]:  # Show last 5 errors
            print(f"   {error.strip()}")

if __name__ == "__main__":
    try:
        check_progress()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
    except Exception as e:
        print(f"Error: {e}")