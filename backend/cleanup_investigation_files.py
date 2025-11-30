import os
import shutil
from datetime import datetime

def cleanup_files():
    # Define files to archive
    files_to_archive = [
        "backend/check_york_street.py",
        "backend/check_api_response.py",
        "backend/inspect_sweeping_data.py",
        "backend/debug_script.py",
        "backend/patch_debug.log",
        "backend/patch_cardinal_directions.py"
    ]
    
    # Create archive directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = os.path.join("archive", f"debug_scripts_{timestamp}")
    
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        print(f"Created archive directory: {archive_dir}")
        
    # Move files
    count = 0
    for file_path in files_to_archive:
        if os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(archive_dir, file_name)
            try:
                shutil.move(file_path, dest_path)
                print(f"Moved {file_path} -> {dest_path}")
                count += 1
            except Exception as e:
                print(f"Error moving {file_path}: {e}")
        else:
            print(f"Skipping missing file: {file_path}")
            
    print(f"\nCleanup complete. Archived {count} files.")

if __name__ == "__main__":
    cleanup_files()