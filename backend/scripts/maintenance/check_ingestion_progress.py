#!/usr/bin/env python3
"""
Check if ingestion is progressing or hung.
Monitors CPU and memory usage of the ingestion process.
"""
import psutil
import time
import sys

def find_ingestion_process():
    """Find the running ingestion process"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'ingest_data_cnn_segments.py' in ' '.join(cmdline):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def main():
    proc = find_ingestion_process()
    
    if not proc:
        print("❌ No ingestion process found running")
        print("   The script may have finished or crashed")
        sys.exit(1)
    
    print(f"✓ Found ingestion process (PID: {proc.pid})")
    print("\nMonitoring for 30 seconds...")
    print("If CPU stays at 0% for entire duration, process is likely hung\n")
    
    samples = []
    for i in range(30):
        try:
            cpu_percent = proc.cpu_percent(interval=1)
            memory_mb = proc.memory_info().rss / 1024 / 1024
            samples.append(cpu_percent)
            
            status = "🟢 WORKING" if cpu_percent > 5 else "🟡 IDLE"
            print(f"[{i+1:2d}/30] CPU: {cpu_percent:5.1f}%  Memory: {memory_mb:6.1f} MB  {status}")
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print("\n❌ Process terminated during monitoring")
            sys.exit(1)
    
    avg_cpu = sum(samples) / len(samples)
    max_cpu = max(samples)
    
    print(f"\n{'='*60}")
    print(f"Average CPU: {avg_cpu:.1f}%")
    print(f"Max CPU: {max_cpu:.1f}%")
    
    if avg_cpu < 1 and max_cpu < 5:
        print("\n❌ LIKELY HUNG - CPU usage is near zero")
        print("   Recommendation: Stop the process (Ctrl+C) and investigate")
    elif avg_cpu < 10:
        print("\n🟡 SLOW PROGRESS - Low CPU usage")
        print("   Process is working but very slowly")
        print("   Spatial matching is computationally expensive")
    else:
        print("\n✅ WORKING NORMALLY - Process is actively computing")
        print("   Let it continue running")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    main()