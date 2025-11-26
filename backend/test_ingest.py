import sys
import subprocess

print("Starting ingest_data.py test...")
result = subprocess.run(
    [sys.executable, "ingest_data.py"],
    cwd="/Users/ssp/Desktop/snapdev-apps/elegant-lynx-play/backend",
    capture_output=True,
    text=True
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nExit code: {result.returncode}")