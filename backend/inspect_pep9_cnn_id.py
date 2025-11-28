#!/usr/bin/env python3
"""
Investigate pep9-66vw (Blockface Geometries) dataset for cnn_id field coverage
"""

import requests
import json
from collections import Counter

def investigate_pep9_cnn_id():
    """Check cnn_id field in pep9-66vw dataset"""
    
    dataset_id = "pep9-66vw"
    base_url = f"https://data.sfgov.org/resource/{dataset_id}.json"
    
    results = []
    results.append("=" * 80)
    results.append("PEP9-66VW (Blockface Geometries) CNN_ID Investigation")
    results.append("=" * 80)
    results.append("")
    
    # First, get total count
    try:
        count_response = requests.get(f"{base_url}?$select=count(*)")
        total_count = int(count_response.json()[0]['count'])
        results.append(f"Total records in dataset: {total_count:,}")
        results.append("")
    except Exception as e:
        results.append(f"Error getting total count: {e}")
        total_count = None
    
    # Get sample of records with cnn_id
    results.append("Fetching records with cnn_id populated...")
    try:
        with_cnn_response = requests.get(
            f"{base_url}?$where=cnn_id IS NOT NULL&$limit=10"
        )
        with_cnn = with_cnn_response.json()
        results.append(f"Found {len(with_cnn)} sample records WITH cnn_id")
        results.append("")
        
        if with_cnn:
            results.append("Sample records WITH cnn_id:")
            results.append("-" * 80)
            for i, record in enumerate(with_cnn[:5], 1):
                results.append(f"\nRecord {i}:")
                results.append(f"  cnn_id: {record.get('cnn_id', 'N/A')}")
                results.append(f"  street_name: {record.get('street_name', 'N/A')}")
                results.append(f"  lf_fadd: {record.get('lf_fadd', 'N/A')}")
                results.append(f"  lf_toadd: {record.get('lf_toadd', 'N/A')}")
                results.append(f"  rt_fadd: {record.get('rt_fadd', 'N/A')}")
                results.append(f"  rt_toadd: {record.get('rt_toadd', 'N/A')}")
                results.append(f"  geometry type: {record.get('geometry', {}).get('type', 'N/A')}")
                
                # Show all available fields for first record
                if i == 1:
                    results.append(f"\n  All fields in record: {list(record.keys())}")
            results.append("")
    except Exception as e:
        results.append(f"Error fetching records with cnn_id: {e}")
        with_cnn = []
    
    # Get sample of records without cnn_id
    results.append("Fetching records without cnn_id...")
    try:
        without_cnn_response = requests.get(
            f"{base_url}?$where=cnn_id IS NULL&$limit=10"
        )
        without_cnn = without_cnn_response.json()
        results.append(f"Found {len(without_cnn)} sample records WITHOUT cnn_id")
        results.append("")
        
        if without_cnn:
            results.append("Sample records WITHOUT cnn_id:")
            results.append("-" * 80)
            for i, record in enumerate(without_cnn[:5], 1):
                results.append(f"\nRecord {i}:")
                results.append(f"  cnn_id: {record.get('cnn_id', 'N/A')}")
                results.append(f"  street_name: {record.get('street_name', 'N/A')}")
                results.append(f"  lf_fadd: {record.get('lf_fadd', 'N/A')}")
                results.append(f"  lf_toadd: {record.get('lf_toadd', 'N/A')}")
                results.append(f"  rt_fadd: {record.get('rt_fadd', 'N/A')}")
                results.append(f"  rt_toadd: {record.get('rt_toadd', 'N/A')}")
                results.append(f"  geometry type: {record.get('geometry', {}).get('type', 'N/A')}")
            results.append("")
    except Exception as e:
        results.append(f"Error fetching records without cnn_id: {e}")
        without_cnn = []
    
    # Try to get count of records with cnn_id
    results.append("Calculating coverage statistics...")
    try:
        with_cnn_count_response = requests.get(
            f"{base_url}?$select=count(*)&$where=cnn_id IS NOT NULL"
        )
        with_cnn_count = int(with_cnn_count_response.json()[0]['count'])
        results.append(f"Records WITH cnn_id: {with_cnn_count:,}")
        
        without_cnn_count_response = requests.get(
            f"{base_url}?$select=count(*)&$where=cnn_id IS NULL"
        )
        without_cnn_count = int(without_cnn_count_response.json()[0]['count'])
        results.append(f"Records WITHOUT cnn_id: {without_cnn_count:,}")
        results.append("")
        
        if total_count and total_count > 0:
            percentage_with = (with_cnn_count / total_count) * 100
            percentage_without = (without_cnn_count / total_count) * 100
            results.append(f"Coverage: {percentage_with:.2f}% have cnn_id")
            results.append(f"Missing: {percentage_without:.2f}% lack cnn_id")
        results.append("")
    except Exception as e:
        results.append(f"Error calculating coverage: {e}")
        results.append("")
    
    # Get a larger sample to analyze cnn_id patterns
    results.append("Analyzing cnn_id patterns (sample of 100 records)...")
    try:
        sample_response = requests.get(f"{base_url}?$limit=100")
        sample_records = sample_response.json()
        
        cnn_ids = [r.get('cnn_id') for r in sample_records if r.get('cnn_id')]
        results.append(f"Sample size: {len(sample_records)}")
        results.append(f"Records with cnn_id in sample: {len(cnn_ids)}")
        
        if cnn_ids:
            results.append(f"Sample cnn_id values: {cnn_ids[:10]}")
            results.append(f"cnn_id data type: {type(cnn_ids[0])}")
        results.append("")
    except Exception as e:
        results.append(f"Error analyzing patterns: {e}")
        results.append("")
    
    # Check for alternative CNN fields
    results.append("Checking for alternative CNN-related fields...")
    try:
        sample_response = requests.get(f"{base_url}?$limit=1")
        if sample_response.json():
            sample_record = sample_response.json()[0]
            cnn_related_fields = [k for k in sample_record.keys() if 'cnn' in k.lower()]
            results.append(f"CNN-related fields found: {cnn_related_fields}")
            results.append("")
            
            if cnn_related_fields:
                results.append("Sample values for CNN-related fields:")
                for field in cnn_related_fields:
                    results.append(f"  {field}: {sample_record.get(field, 'N/A')}")
                results.append("")
    except Exception as e:
        results.append(f"Error checking alternative fields: {e}")
        results.append("")
    
    results.append("=" * 80)
    results.append("Investigation Complete")
    results.append("=" * 80)
    
    return "\n".join(results)

if __name__ == "__main__":
    output = investigate_pep9_cnn_id()
    print(output)
    
    # Save to file
    output_file = "pep9_cnn_investigation.txt"
    with open(output_file, "w") as f:
        f.write(output)
    print(f"\nResults saved to {output_file}")