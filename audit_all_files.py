#!/usr/bin/env python3
"""
Complete project audit - scans all directories for .py and .md files.
"""
import os
from pathlib import Path
from datetime import datetime

def get_file_info(filepath):
    """Get file metadata."""
    stat = filepath.stat()
    return {
        "size_kb": round(stat.st_size / 1024, 2),
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
    }

def audit_project():
    """Audit entire project."""
    root = Path(".")
    
    # Exclude directories
    exclude_dirs = {".venv", "node_modules", ".git", "__pycache__", "dist", "build"}
    
    results = {
        "root": [],
        "backend": [],
        "frontend": []
    }
    
    # Find all .py and .md files
    for filepath in root.rglob("*"):
        # Skip excluded directories
        if any(excluded in filepath.parts for excluded in exclude_dirs):
            continue
        
        # Only process .py and .md files
        if filepath.suffix not in [".py", ".md"]:
            continue
        
        if not filepath.is_file():
            continue
        
        info = get_file_info(filepath)
        file_data = {
            "name": filepath.name,
            "path": str(filepath),
            **info
        }
        
        # Categorize by location
        if "backend" in filepath.parts:
            results["backend"].append(file_data)
        elif "frontend" in filepath.parts:
            results["frontend"].append(file_data)
        else:
            results["root"].append(file_data)
    
    return results

def print_report(results):
    """Print formatted report."""
    print("=" * 100)
    print("COMPLETE PROJECT FILE AUDIT")
    print("=" * 100)
    print()
    
    total_files = sum(len(files) for files in results.values())
    print(f"Total Files: {total_files}")
    print()
    
    # Root directory files
    if results["root"]:
        print("=" * 100)
        print(f"ROOT DIRECTORY ({len(results['root'])} files)")
        print("-" * 100)
        for f in sorted(results["root"], key=lambda x: x["name"]):
            print(f"  {f['name']:50s} | {f['size_kb']:8.2f} KB | {f['modified']}")
        print()
    
    # Backend files
    if results["backend"]:
        print("=" * 100)
        print(f"BACKEND DIRECTORY ({len(results['backend'])} files)")
        print("-" * 100)
        
        # Separate by type
        py_files = [f for f in results["backend"] if f["name"].endswith(".py")]
        md_files = [f for f in results["backend"] if f["name"].endswith(".md")]
        
        print(f"\nPython files: {len(py_files)}")
        print(f"Markdown files: {len(md_files)}")
        print()
    
    # Frontend files
    if results["frontend"]:
        print("=" * 100)
        print(f"FRONTEND DIRECTORY ({len(results['frontend'])} files)")
        print("-" * 100)
        for f in sorted(results["frontend"], key=lambda x: x["name"]):
            print(f"  {f['name']:50s} | {f['size_kb']:8.2f} KB | {f['modified']}")
        print()
    
    # PRD files specifically
    print("=" * 100)
    print("PRD FILES (Product Requirements Documents)")
    print("-" * 100)
    all_files = results["root"] + results["backend"] + results["frontend"]
    prd_files = [f for f in all_files if "prd" in f["name"].lower()]
    
    if prd_files:
        for f in sorted(prd_files, key=lambda x: x["modified"], reverse=True):
            print(f"  {f['path']:60s} | {f['size_kb']:8.2f} KB | {f['modified']}")
    else:
        print("  No PRD files found")
    print()

if __name__ == "__main__":
    results = audit_project()
    print_report(results)