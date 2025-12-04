"""
Street Cleaning Data Completeness Validator

This script identifies potential missing street cleaning records by finding CNNs
where only one side has cleaning data. Based on the CNN 961000 investigation,
this pattern often indicates missing data in the Socrata dataset.

Usage:
    python validate_street_cleaning_completeness.py

Output:
    - Console report of findings
    - JSON file with detailed results
    - CSV file for easy review
"""

import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from sodapy import Socrata
import pandas as pd
import json
from collections import defaultdict
from datetime import datetime

# Load environment
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

SFMTA_DOMAIN = "data.sfgov.org"
STREET_CLEANING_SCHEDULES_ID = "yhqp-riqs"
STREETS_DATASET_ID = "3psu-pn9h"

async def validate_street_cleaning_completeness():
    """
    Validate street cleaning data completeness by identifying CNNs with
    asymmetric cleaning schedules (only one side has data).
    """
    
    print("=" * 80)
    print("STREET CLEANING DATA COMPLETENESS VALIDATION")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    mongodb_uri = os.getenv("MONGODB_URI")
    
    # ==========================================
    # 1. Load data from MongoDB
    # ==========================================
    print("Step 1: Loading data from MongoDB...")
    
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not found in .env file")
        return
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except:
        db = client["curby"]
    
    # Get all street segments
    segments = await db.street_segments.find({}).to_list(length=None)
    print(f"✓ Loaded {len(segments)} street segments from database\n")
    
    # ==========================================
    # 2. Analyze cleaning coverage by CNN
    # ==========================================
    print("Step 2: Analyzing street cleaning coverage...")
    
    cnn_cleaning_data = defaultdict(lambda: {"L": None, "R": None, "street_name": None})
    
    for segment in segments:
        cnn = segment.get("cnn")
        side = segment.get("side")
        street_name = segment.get("streetName")
        
        if not cnn or not side:
            continue
        
        cnn_cleaning_data[cnn]["street_name"] = street_name
        
        # Check if this segment has street cleaning
        has_cleaning = any(
            rule.get("type") == "street-sweeping" 
            for rule in segment.get("rules", [])
        )
        
        if has_cleaning:
            # Extract cleaning details
            cleaning_rules = [
                rule for rule in segment.get("rules", [])
                if rule.get("type") == "street-sweeping"
            ]
            
            if cleaning_rules:
                rule = cleaning_rules[0]  # Take first cleaning rule
                cnn_cleaning_data[cnn][side] = {
                    "day": rule.get("day"),
                    "startTime": rule.get("startTime"),
                    "endTime": rule.get("endTime"),
                    "cardinal": rule.get("blockside"),
                    "limits": rule.get("limits")
                }
    
    # ==========================================
    # 3. Identify asymmetric CNNs
    # ==========================================
    print("Step 3: Identifying CNNs with asymmetric cleaning data...\n")
    
    asymmetric_cnns = []
    symmetric_cnns = []
    no_cleaning_cnns = []
    
    for cnn, data in cnn_cleaning_data.items():
        has_left = data["L"] is not None
        has_right = data["R"] is not None
        
        if has_left and has_right:
            symmetric_cnns.append(cnn)
        elif has_left or has_right:
            # Asymmetric - only one side has cleaning
            asymmetric_cnns.append({
                "cnn": cnn,
                "street_name": data["street_name"],
                "left_side": data["L"],
                "right_side": data["R"],
                "missing_side": "R" if has_left else "L",
                "present_side": "L" if has_left else "R"
            })
        else:
            no_cleaning_cnns.append(cnn)
    
    # ==========================================
    # 4. Generate Report
    # ==========================================
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print(f"\nTotal CNNs analyzed: {len(cnn_cleaning_data)}")
    print(f"  ✓ Both sides have cleaning: {len(symmetric_cnns)} ({len(symmetric_cnns)/len(cnn_cleaning_data)*100:.1f}%)")
    print(f"  ⚠️  Only one side has cleaning: {len(asymmetric_cnns)} ({len(asymmetric_cnns)/len(cnn_cleaning_data)*100:.1f}%)")
    print(f"  ○ No cleaning on either side: {len(no_cleaning_cnns)} ({len(no_cleaning_cnns)/len(cnn_cleaning_data)*100:.1f}%)")
    
    # ==========================================
    # 5. Show examples of asymmetric CNNs
    # ==========================================
    if asymmetric_cnns:
        print(f"\n{'=' * 80}")
        print("POTENTIALLY MISSING RECORDS (First 10 examples)")
        print("=" * 80)
        
        for i, cnn_data in enumerate(asymmetric_cnns[:10]):
            print(f"\n{i+1}. CNN {cnn_data['cnn']} - {cnn_data['street_name']}")
            print(f"   Missing Side: {cnn_data['missing_side']}")
            print(f"   Present Side: {cnn_data['present_side']}")
            
            present_data = cnn_data['left_side'] if cnn_data['present_side'] == 'L' else cnn_data['right_side']
            if present_data:
                print(f"   Present Schedule: {present_data['day']} {present_data['startTime']}-{present_data['endTime']}")
                print(f"   Cardinal: {present_data['cardinal']}")
                print(f"   Limits: {present_data['limits']}")
    
    # ==========================================
    # 6. Export results
    # ==========================================
    print(f"\n{'=' * 80}")
    print("EXPORTING RESULTS")
    print("=" * 80)
    
    output_dir = os.path.join(os.path.dirname(__file__), "validation_results")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export asymmetric CNNs to JSON
    json_file = os.path.join(output_dir, f"asymmetric_cleaning_{timestamp}.json")
    with open(json_file, 'w') as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_cnns": len(cnn_cleaning_data),
            "symmetric_count": len(symmetric_cnns),
            "asymmetric_count": len(asymmetric_cnns),
            "no_cleaning_count": len(no_cleaning_cnns),
            "asymmetric_cnns": asymmetric_cnns
        }, f, indent=2)
    print(f"✓ Exported detailed results to: {json_file}")
    
    # Export to CSV for easy review
    if asymmetric_cnns:
        csv_data = []
        for cnn_data in asymmetric_cnns:
            present_data = cnn_data['left_side'] if cnn_data['present_side'] == 'L' else cnn_data['right_side']
            csv_data.append({
                "CNN": cnn_data['cnn'],
                "Street Name": cnn_data['street_name'],
                "Missing Side": cnn_data['missing_side'],
                "Present Side": cnn_data['present_side'],
                "Present Day": present_data['day'] if present_data else None,
                "Present Time": f"{present_data['startTime']}-{present_data['endTime']}" if present_data else None,
                "Present Cardinal": present_data['cardinal'] if present_data else None,
                "Limits": present_data['limits'] if present_data else None
            })
        
        df = pd.DataFrame(csv_data)
        csv_file = os.path.join(output_dir, f"asymmetric_cleaning_{timestamp}.csv")
        df.to_csv(csv_file, index=False)
        print(f"✓ Exported CSV report to: {csv_file}")
    
    # ==========================================
    # 7. Generate recommendations
    # ==========================================
    print(f"\n{'=' * 80}")
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if len(asymmetric_cnns) > 0:
        print(f"\n⚠️  Found {len(asymmetric_cnns)} CNNs with asymmetric cleaning data")
        print("\nRecommended Actions:")
        print("1. Review the exported CSV file for detailed list")
        print("2. Manually verify a sample of these CNNs (check street signs)")
        print("3. Report confirmed missing records to SFMTA data team")
        print("4. Implement cardinal direction inference as workaround")
        print("5. Add data quality warnings in user interface")
        
        print(f"\nHigh Priority CNNs (for manual verification):")
        # Show CNNs where the pattern matches known issue (opposite days)
        priority_cnns = []
        for cnn_data in asymmetric_cnns[:20]:
            present_data = cnn_data['left_side'] if cnn_data['present_side'] == 'L' else cnn_data['right_side']
            if present_data and present_data['day'] in ['Thu', 'Fri']:
                priority_cnns.append(f"  - CNN {cnn_data['cnn']} ({cnn_data['street_name']})")
        
        for cnn in priority_cnns[:5]:
            print(cnn)
    else:
        print("\n✓ No asymmetric cleaning patterns found")
        print("  All CNNs either have cleaning on both sides or neither side")
    
    print(f"\n{'=' * 80}")
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(validate_street_cleaning_completeness())