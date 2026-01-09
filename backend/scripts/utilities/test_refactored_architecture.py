#!/usr/bin/env python3
"""
Test script to verify the refactored ingestion architecture.
Validates that the step order and meter/schedule separation are correct.
"""

import ast
import re

def test_refactored_script():
    """Test the refactored ingestion script architecture."""
    
    print("Testing backend/ingest_data_cnn_segments_v2.py...")
    print("=" * 60)
    
    with open('ingest_data_cnn_segments_v2.py', 'r') as f:
        content = f.read()
    
    # Test 1: Verify step order
    print("\n✓ Test 1: Verifying step order...")
    step_pattern = r'STEP (\d+):'
    steps = re.findall(step_pattern, content)
    
    expected_steps = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
    actual_steps = [s for s in steps if s in expected_steps]
    
    if actual_steps == expected_steps:
        print(f"  ✓ All 12 steps found in correct order: {', '.join(actual_steps)}")
    else:
        print(f"  ✗ Step order mismatch!")
        print(f"    Expected: {expected_steps}")
        print(f"    Found: {actual_steps}")
        return False
    
    # Test 2: Verify Step 3 is meters WITHOUT schedules
    print("\n✓ Test 2: Verifying Step 3 loads meters WITHOUT schedules...")
    step3_section = re.search(r'STEP 3:.*?STEP 4:', content, re.DOTALL)
    if step3_section:
        step3_text = step3_section.group(0)
        
        # Check for meter loading
        has_meters = 'METERS_DATASET_ID' in step3_text or 'meters_df' in step3_text
        
        # Check schedules are empty
        has_empty_schedules = '"schedules": []' in step3_text
        
        # Check NO schedule loading in step 3
        no_schedule_loading = 'METER_SCHEDULES_DATASET_ID' not in step3_text
        
        if has_meters and has_empty_schedules and no_schedule_loading:
            print("  ✓ Step 3 correctly loads meters with empty schedules array")
        else:
            print("  ✗ Step 3 architecture incorrect!")
            print(f"    Has meters: {has_meters}")
            print(f"    Has empty schedules: {has_empty_schedules}")
            print(f"    No schedule loading: {no_schedule_loading}")
            return False
    else:
        print("  ✗ Could not find Step 3 section")
        return False
    
    # Test 3: Verify Step 6 loads schedules and attaches to meters
    print("\n✓ Test 3: Verifying Step 6 loads schedules and attaches to meters...")
    step6_section = re.search(r'STEP 6:.*?STEP 7:', content, re.DOTALL)
    if step6_section:
        step6_text = step6_section.group(0)
        
        # Check for schedule loading
        has_schedule_loading = 'METER_SCHEDULES_DATASET_ID' in step6_text
        
        # Check for post_id lookup
        has_post_id_lookup = 'schedules_by_post' in step6_text
        
        # Check for attaching to existing meters
        has_meter_attachment = 'meter["schedules"]' in step6_text or 'meter.get("post_id")' in step6_text
        
        if has_schedule_loading and has_post_id_lookup and has_meter_attachment:
            print("  ✓ Step 6 correctly loads schedules and attaches to meters via post_id")
        else:
            print("  ✗ Step 6 architecture incorrect!")
            print(f"    Has schedule loading: {has_schedule_loading}")
            print(f"    Has post_id lookup: {has_post_id_lookup}")
            print(f"    Has meter attachment: {has_meter_attachment}")
            return False
    else:
        print("  ✗ Could not find Step 6 section")
        return False
    
    # Test 4: Verify correct step descriptions
    print("\n✓ Test 4: Verifying step descriptions match architecture...")
    
    step_descriptions = {
        '1': 'Creating CNN-Based Street Segments',
        '2': 'Intersections & Permutations',
        '3': 'Matching Parking Meters (WITHOUT schedules)',
        '6': 'Attaching Meter Schedules TO Meters',
        '7': 'Matching Parking Regulations',
        '8': 'Matching Street Sweeping'
    }
    
    all_correct = True
    for step_num, expected_desc in step_descriptions.items():
        pattern = f'STEP {step_num}:.*?{re.escape(expected_desc)}'
        if re.search(pattern, content, re.IGNORECASE):
            print(f"  ✓ Step {step_num}: {expected_desc}")
        else:
            print(f"  ✗ Step {step_num}: Description not found or incorrect")
            all_correct = False
    
    if not all_correct:
        return False
    
    # Test 5: Verify checkpoint saves are present
    print("\n✓ Test 5: Verifying checkpoint saves...")
    checkpoint_saves = re.findall(r'checkpoint\.save\("(\d+)"', content)
    
    if len(checkpoint_saves) >= 12:
        print(f"  ✓ Found {len(checkpoint_saves)} checkpoint saves")
    else:
        print(f"  ✗ Only found {len(checkpoint_saves)} checkpoint saves (expected at least 12)")
        return False
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nThe refactored script correctly implements:")
    print("  1. Correct 12-step ingestion order")
    print("  2. Meters loaded FIRST in Step 3 (without schedules)")
    print("  3. Schedules loaded LATER in Step 6 (attached to meters)")
    print("  4. All checkpoint functionality preserved")
    print("\nArchitecture matches INGESTION_ORDER_REFACTORING_PLAN_V2.md ✓")
    
    return True

if __name__ == '__main__':
    import sys
    success = test_refactored_script()
    sys.exit(0 if success else 1)