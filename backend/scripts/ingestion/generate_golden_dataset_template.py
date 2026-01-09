"""
Generate a human-reviewable template for creating golden interpretations.

This script creates a CSV/JSON file with all 292 unique regulation combinations
for manual human interpretation to serve as the golden dataset.
"""

import json
import csv
from datetime import datetime

def generate_golden_template():
    print("📋 Generating Golden Dataset Template")
    
    # Load unique regulations
    with open("unique_regulations.json", "r") as f:
        data = json.load(f)
        unique_combinations = data["unique_combinations"]
    
    print(f"✅ Loaded {len(unique_combinations)} unique combinations")
    
    # Create CSV for easy editing
    csv_file = "golden_dataset_template.csv"
    json_file = "golden_dataset_template.json"
    
    # CSV Headers
    csv_headers = [
        "unique_id",
        "usage_count",
        "regulation",
        "days",
        "hours",
        "hrs_begin",
        "hrs_end",
        "regdetails",
        "rpparea1",
        "exceptions",
        "from_time",
        "to_time",
        "hrlimit",
        # Golden interpretation fields (to be filled by human)
        "golden_action",
        "golden_summary",
        "golden_severity",
        "golden_days",
        "golden_hours",
        "golden_time_limit_minutes",
        "golden_exceptions",
        "golden_details",
        "notes"
    ]
    
    # Write CSV
    with open(csv_file, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        
        for item in unique_combinations:
            fields = item["fields"]
            row = {
                "unique_id": item["unique_id"],
                "usage_count": item["usage_count"],
                "regulation": fields.get("regulation") or "",
                "days": fields.get("days") or "",
                "hours": fields.get("hours") or "",
                "hrs_begin": fields.get("hrs_begin") or "",
                "hrs_end": fields.get("hrs_end") or "",
                "regdetails": fields.get("regdetails") or "",
                "rpparea1": fields.get("rpparea1") or "",
                "exceptions": fields.get("exceptions") or "",
                "from_time": fields.get("from_time") or "",
                "to_time": fields.get("to_time") or "",
                "hrlimit": fields.get("hrlimit") or "",
                # Empty fields for human to fill
                "golden_action": "",
                "golden_summary": "",
                "golden_severity": "",
                "golden_days": "",
                "golden_hours": "",
                "golden_time_limit_minutes": "",
                "golden_exceptions": "",
                "golden_details": "",
                "notes": ""
            }
            writer.writerow(row)
    
    # Write JSON (more structured, easier to import later)
    json_template = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "total_combinations": len(unique_combinations),
            "purpose": "Golden dataset for LLM evaluation",
            "instructions": {
                "action": "Choose: allowed, prohibited, time-limited, restricted, permit-required",
                "summary": "Clear, plain English summary of the parking rule",
                "severity": "Choose: critical, high, medium, low",
                "days": "List of days (e.g., ['Monday', 'Tuesday']) or empty array",
                "hours": "Time range (e.g., '9AM-6PM') or empty string",
                "time_limit_minutes": "Integer (e.g., 120 for 2 hours) or null",
                "exceptions": "List of exceptions (e.g., ['RPP exempt', 'Holidays']) or empty array",
                "details": "Any additional context or clarifications"
            }
        },
        "combinations": []
    }
    
    for item in unique_combinations:
        fields = item["fields"]
        entry = {
            "unique_id": item["unique_id"],
            "usage_count": item["usage_count"],
            "sample_object_ids": item.get("sample_object_ids", [])[:3],  # First 3 for reference
            "source_fields": fields,
            "golden_interpretation": {
                "action": "",
                "summary": "",
                "severity": "",
                "conditions": {
                    "days": [],
                    "hours": "",
                    "time_limit_minutes": None,
                    "exceptions": []
                },
                "details": "",
                "notes": ""
            }
        }
        json_template["combinations"].append(entry)
    
    with open(json_file, "w") as f:
        json.dump(json_template, f, indent=2)
    
    print(f"\n✅ Generated template files:")
    print(f"   📄 CSV: {csv_file} (for spreadsheet editing)")
    print(f"   📄 JSON: {json_file} (for structured editing)")
    print(f"\n📊 Statistics:")
    print(f"   Total combinations: {len(unique_combinations)}")
    print(f"   Fields to interpret: {len(csv_headers) - 13} per combination")
    print(f"\n💡 Next Steps:")
    print(f"   1. Open {csv_file} in Excel/Google Sheets")
    print(f"   2. Fill in the 'golden_*' columns for each row")
    print(f"   3. Save and use as reference for LLM evaluation")

if __name__ == "__main__":
    generate_golden_template()