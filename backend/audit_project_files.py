#!/usr/bin/env python3
"""
Systematic audit of all .py and .md files in the project.
Categorizes files by purpose and identifies candidates for cleanup.
"""
import os
from pathlib import Path
from datetime import datetime
import re

# Define file categories
CATEGORIES = {
    "CORE_PRODUCTION": {
        "description": "Essential files for production system",
        "patterns": [
            r"^main\.py$",
            r"^models\.py$",
            r"^display_utils\.py$",
            r"^ingest_data_cnn_segments\.py$",
            r"^run_ingestion\.sh$",
            r"^check_ingestion_status\.py$",
            r"^\.env$",
            r"^requirements\.txt$",
        ],
        "action": "KEEP"
    },
    "INVESTIGATION_SCRIPTS": {
        "description": "One-time investigation/analysis scripts",
        "patterns": [
            r"^investigate_.*\.py$",
            r"^inspect_.*\.py$",
            r"^debug_.*\.py$",
            r"^analyze_.*\.py$",
            r"^find_.*\.py$",
            r"^show_.*\.py$",
            r"^query_.*\.py$",
        ],
        "action": "REVIEW - Likely safe to archive/delete"
    },
    "VALIDATION_SCRIPTS": {
        "description": "Validation and verification scripts",
        "patterns": [
            r"^verify_.*\.py$",
            r"^validate_.*\.py$",
            r"^check_.*\.py$",
        ],
        "action": "REVIEW - Keep if still validating current system"
    },
    "TEST_SCRIPTS": {
        "description": "Test and experimental scripts",
        "patterns": [
            r"^test_.*\.py$",
            r"^quick_.*\.py$",
            r"^simple_.*\.py$",
        ],
        "action": "REVIEW - Archive if tests are passing"
    },
    "OLD_INGESTION": {
        "description": "Deprecated ingestion scripts",
        "patterns": [
            r"^ingest_data\.py$",
            r"^ingest_mission_only\.py$",
            r"^create_master_cnn_join\.py$",
        ],
        "action": "ARCHIVE - Replaced by ingest_data_cnn_segments.py"
    },
    "DOCUMENTATION": {
        "description": "Documentation and analysis files",
        "patterns": [
            r".*\.md$",
            r".*\.txt$",
        ],
        "action": "REVIEW - Keep current docs, archive outdated"
    },
    "BACKUP_FILES": {
        "description": "Backup and temporary files",
        "patterns": [
            r"^backup_.*\.py$",
            r".*_backup\.py$",
            r".*\.pyc$",
            r".*\.log$",
        ],
        "action": "DELETE - Safe to remove"
    }
}

def categorize_file(filename):
    """Categorize a file based on its name pattern."""
    for category, info in CATEGORIES.items():
        for pattern in info["patterns"]:
            if re.match(pattern, filename, re.IGNORECASE):
                return category, info["action"]
    return "UNCATEGORIZED", "REVIEW - Manual inspection needed"

def get_file_info(filepath):
    """Get file metadata."""
    stat = filepath.stat()
    return {
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime),
        "size_kb": round(stat.st_size / 1024, 2)
    }

def audit_directory(directory):
    """Audit all .py and .md files in directory."""
    results = {}
    
    # Find all .py and .md files
    py_files = list(Path(directory).glob("*.py"))
    md_files = list(Path(directory).glob("*.md"))
    txt_files = list(Path(directory).glob("*.txt"))
    sh_files = list(Path(directory).glob("*.sh"))
    
    all_files = py_files + md_files + txt_files + sh_files
    
    for filepath in all_files:
        filename = filepath.name
        category, action = categorize_file(filename)
        
        if category not in results:
            results[category] = []
        
        file_info = get_file_info(filepath)
        results[category].append({
            "filename": filename,
            "path": str(filepath),
            "action": action,
            **file_info
        })
    
    return results

def print_audit_report(results):
    """Print formatted audit report."""
    print("=" * 100)
    print("PROJECT FILE AUDIT REPORT")
    print("=" * 100)
    print()
    
    total_files = sum(len(files) for files in results.values())
    total_size_kb = sum(
        sum(f["size_kb"] for f in files)
        for files in results.values()
    )
    
    print(f"Total Files Analyzed: {total_files}")
    print(f"Total Size: {total_size_kb:.2f} KB")
    print()
    
    # Print by category
    for category in CATEGORIES.keys():
        if category not in results:
            continue
            
        files = results[category]
        if not files:
            continue
        
        info = CATEGORIES[category]
        print("=" * 100)
        print(f"CATEGORY: {category}")
        print(f"Description: {info['description']}")
        print(f"Recommended Action: {info['action']}")
        print(f"File Count: {len(files)}")
        print("-" * 100)
        
        # Sort by modification date (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        for f in files:
            mod_date = f["modified"].strftime("%Y-%m-%d %H:%M")
            print(f"  {f['filename']:50s} | {f['size_kb']:8.2f} KB | {mod_date}")
        
        print()
    
    # Print uncategorized files
    if "UNCATEGORIZED" in results and results["UNCATEGORIZED"]:
        print("=" * 100)
        print("UNCATEGORIZED FILES (Manual Review Needed)")
        print("-" * 100)
        for f in results["UNCATEGORIZED"]:
            mod_date = f["modified"].strftime("%Y-%m-%d %H:%M")
            print(f"  {f['filename']:50s} | {f['size_kb']:8.2f} KB | {mod_date}")
        print()

def generate_cleanup_script(results):
    """Generate a shell script to archive old files."""
    script_lines = [
        "#!/bin/bash",
        "# Auto-generated cleanup script",
        "# Review before executing!",
        "",
        "# Create archive directory",
        "mkdir -p archive/investigation_scripts",
        "mkdir -p archive/old_docs",
        "mkdir -p archive/old_ingestion",
        "",
    ]
    
    # Add commands to move files
    for category, files in results.items():
        if category in ["INVESTIGATION_SCRIPTS", "OLD_INGESTION"]:
            script_lines.append(f"# Archive {category}")
            for f in files:
                filename = f["filename"]
                if category == "INVESTIGATION_SCRIPTS":
                    script_lines.append(f"# mv {filename} archive/investigation_scripts/")
                elif category == "OLD_INGESTION":
                    script_lines.append(f"# mv {filename} archive/old_ingestion/")
            script_lines.append("")
    
    return "\n".join(script_lines)

if __name__ == "__main__":
    backend_dir = Path(__file__).parent
    
    print("Auditing backend directory...")
    print()
    
    results = audit_directory(backend_dir)
    print_audit_report(results)
    
    # Generate cleanup script
    cleanup_script = generate_cleanup_script(results)
    
    cleanup_path = backend_dir / "cleanup_old_files.sh"
    with open(cleanup_path, "w") as f:
        f.write(cleanup_script)
    
    print("=" * 100)
    print(f"Cleanup script generated: {cleanup_path}")
    print("Review the script before executing!")
    print("=" * 100)