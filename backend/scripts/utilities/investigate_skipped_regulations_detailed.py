#!/usr/bin/env python3
"""
Investigate the 12 skipped regulations from skipped_regulation_ids.txt
Query SFMTA dataset (hi6h-neyh) to understand why they were skipped
"""

import requests
import json
import os
from dotenv import load_dotenv
from typing import Dict, List, Any

# Load environment variables
load_dotenv()

# SFMTA Parking Regulations dataset - CORRECT DATASET ID
PARKING_REGS_URL = "https://data.sfgov.org/resource/hi6h-neyh.json"
SFMTA_APP_TOKEN = os.getenv("SFMTA_APP_TOKEN")

def fetch_regulation_by_objectid(object_id: int) -> Dict[str, Any]:
    """Fetch a single regulation by OBJECTID from SFMTA dataset"""
    # Use simpler query format
    params = {
        "objectid": object_id,
        "$limit": 1
    }
    
    headers = {}
    if SFMTA_APP_TOKEN:
        headers["X-App-Token"] = SFMTA_APP_TOKEN
        print(f"  Using API token: {SFMTA_APP_TOKEN[:10]}...")
    else:
        print(f"  WARNING: No SFMTA_APP_TOKEN found in environment")
    
    try:
        print(f"  Query URL: {PARKING_REGS_URL}")
        print(f"  Query params: {params}")
        response = requests.get(PARKING_REGS_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data[0] if data else None
    except Exception as e:
        print(f"  Error: {e}")
        print(f"  Response status: {response.status_code if 'response' in locals() else 'N/A'}")
        if 'response' in locals():
            print(f"  Response text: {response.text[:200]}")
        return None

def analyze_regulation(reg: Dict[str, Any], category: str) -> Dict[str, Any]:
    """Analyze a regulation and extract key information"""
    if not reg:
        return None
    
    analysis = {
        "objectid": reg.get("objectid"),
        "category": category,
        "has_geometry": "the_geom" in reg or "geometry" in reg,
        "supervisor_district": reg.get("supervisor_district"),
        "street_name": reg.get("street_name"),
        "cnn": reg.get("cnn"),
        "regulation_text": reg.get("regulation_text", "")[:100],  # First 100 chars
        "days": reg.get("days"),
        "start_time": reg.get("start_time"),
        "end_time": reg.get("end_time"),
        "from_street": reg.get("from_street"),
        "to_street": reg.get("to_street"),
        "side": reg.get("side"),
        "all_fields": list(reg.keys())
    }
    
    return analysis

def main():
    print("=" * 80)
    print("INVESTIGATING SKIPPED REGULATIONS")
    print("=" * 80)
    
    # Read skipped regulation IDs (these are SFMTA OBJECTID values)
    without_geometry = [1551, 2303, 2353, 3295, 3948, 3561, 3949, 17287, 3947]
    no_segment_match = [4973, 64, 2191]
    
    results = {
        "without_geometry": [],
        "no_segment_match": [],
        "summary": {
            "total_analyzed": 0,
            "with_district": 0,
            "without_district": 0,
            "district_fallback_possible": 0,
            "not_found": 0
        }
    }
    
    print("\n1. ANALYZING REGULATIONS WITHOUT GEOMETRY")
    print("-" * 80)
    for obj_id in without_geometry:
        print(f"\nFetching OBJECTID {obj_id}...")
        reg = fetch_regulation_by_objectid(obj_id)
        
        if not reg:
            print(f"  ✗ Not found in SFMTA dataset")
            results["summary"]["not_found"] += 1
            continue
            
        analysis = analyze_regulation(reg, "without_geometry")
        
        if analysis:
            results["without_geometry"].append(analysis)
            results["summary"]["total_analyzed"] += 1
            
            if analysis["supervisor_district"]:
                results["summary"]["with_district"] += 1
                results["summary"]["district_fallback_possible"] += 1
                print(f"  ✓ Has district: {analysis['supervisor_district']}")
                print(f"    Street: {analysis['street_name']}")
                print(f"    Regulation: {analysis['regulation_text']}")
            else:
                results["summary"]["without_district"] += 1
                print(f"  ✗ No district field")
                print(f"    Street: {analysis['street_name']}")
    
    print("\n\n2. ANALYZING REGULATIONS WITH NO SEGMENT MATCH")
    print("-" * 80)
    for obj_id in no_segment_match:
        print(f"\nFetching OBJECTID {obj_id}...")
        reg = fetch_regulation_by_objectid(obj_id)
        
        if not reg:
            print(f"  ✗ Not found in SFMTA dataset")
            results["summary"]["not_found"] += 1
            continue
            
        analysis = analyze_regulation(reg, "no_segment_match")
        
        if analysis:
            results["no_segment_match"].append(analysis)
            results["summary"]["total_analyzed"] += 1
            
            if analysis["supervisor_district"]:
                results["summary"]["with_district"] += 1
                results["summary"]["district_fallback_possible"] += 1
                print(f"  ✓ Has district: {analysis['supervisor_district']}")
                print(f"    Street: {analysis['street_name']}")
                print(f"    CNN: {analysis['cnn']}")
                print(f"    Regulation: {analysis['regulation_text']}")
            else:
                results["summary"]["without_district"] += 1
                print(f"  ✗ No district field")
                print(f"    Street: {analysis['street_name']}")
    
    # Save detailed results
    output_file = "skipped_regulations_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total regulations analyzed: {results['summary']['total_analyzed']}")
    print(f"Not found in SFMTA dataset: {results['summary']['not_found']}")
    print(f"With supervisor_district: {results['summary']['with_district']}")
    print(f"Without supervisor_district: {results['summary']['without_district']}")
    print(f"District-based fallback possible: {results['summary']['district_fallback_possible']}")
    print(f"\nDetailed results saved to: {output_file}")
    
    if results['summary']['district_fallback_possible'] > 0:
        print("\n✓ RECOMMENDATION: Implement district-based fallback for regulations with supervisor_district")
        print("  This will allow these regulations to be applied to all segments in their district")
    else:
        print("\n✗ District-based fallback not possible - no regulations have supervisor_district field")
    
    if results['summary']['not_found'] > 0:
        print(f"\n⚠️  WARNING: {results['summary']['not_found']} regulations not found in SFMTA dataset")
        print("  These IDs may be incorrect or the API query needs adjustment")

if __name__ == "__main__":
    main()