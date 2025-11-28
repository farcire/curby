import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from typing import Dict, List, Any

async def validate_cnn_segments():
    """Validate the new CNN segment architecture"""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]

    print("\n" + "="*70)
    print("CNN SEGMENT VALIDATION")
    print("="*70)

    # ==========================================
    # Test 1: Coverage Analysis
    # ==========================================
    print("\n--- Test 1: Coverage Analysis ---")
    
    segments = await db.street_segments.find({}).to_list(None)
    streets = await db.streets.find({}).to_list(None)
    
    unique_cnns = set(s.get("cnn") for s in streets if s.get("cnn"))
    expected_segments = len(unique_cnns) * 2  # 2 sides per CNN
    actual_segments = len(segments)
    
    print(f"Total CNNs in Active Streets: {len(unique_cnns)}")
    print(f"Expected segments (CNNs × 2): {expected_segments}")
    print(f"Actual segments created: {actual_segments}")
    print(f"Coverage: {(actual_segments/expected_segments*100):.1f}%")
    
    if actual_segments == expected_segments:
        print("✓ PASS: 100% coverage achieved!")
    else:
        print(f"✗ FAIL: Missing {expected_segments - actual_segments} segments")

    # ==========================================
    # Test 2: CNN 1046000 Validation (The Critical Test)
    # ==========================================
    print("\n--- Test 2: CNN 1046000 Validation ---")
    print("Testing: 20th St between York and Bryant")
    
    segment_1046_L = await db.street_segments.find_one({"cnn": "1046000", "side": "L"})
    segment_1046_R = await db.street_segments.find_one({"cnn": "1046000", "side": "R"})
    
    if not segment_1046_L:
        print("✗ FAIL: CNN 1046000 Left segment not found")
    else:
        print("✓ PASS: CNN 1046000 Left segment exists")
        print(f"  Street: {segment_1046_L.get('streetName')}")
        print(f"  From: {segment_1046_L.get('fromStreet')}")
        print(f"  To: {segment_1046_L.get('toStreet')}")
        
        # Check street sweeping
        left_sweeping = [r for r in segment_1046_L.get("rules", []) if r["type"] == "street-sweeping"]
        if left_sweeping:
            print(f"  Sweeping rules: {len(left_sweeping)}")
            for rule in left_sweeping:
                print(f"    - {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
            
            # Check for Tuesday 9-11am
            has_tuesday = any(r.get("day") == "Tuesday" and "9" in str(r.get("startTime")) for r in left_sweeping)
            if has_tuesday:
                print("  ✓ Has Tuesday 9-11am sweeping (EXPECTED)")
            else:
                print("  ✗ Missing Tuesday 9-11am sweeping")
        else:
            print("  ✗ No sweeping rules found")
        
        # Check parking regulations
        left_parking = [r for r in segment_1046_L.get("rules", []) if r["type"] == "parking-regulation"]
        print(f"  Parking regulations: {len(left_parking)}")
        if left_parking:
            for reg in left_parking[:3]:  # Show first 3
                print(f"    - {reg.get('regulation')} (confidence: {reg.get('matchConfidence', 0):.3f})")
    
    if not segment_1046_R:
        print("\n✗ FAIL: CNN 1046000 Right segment not found")
    else:
        print("\n✓ PASS: CNN 1046000 Right segment exists")
        right_sweeping = [r for r in segment_1046_R.get("rules", []) if r["type"] == "street-sweeping"]
        if right_sweeping:
            print(f"  Sweeping rules: {len(right_sweeping)}")
            for rule in right_sweeping:
                print(f"    - {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")

    # ==========================================
    # Test 3: Rule Distribution
    # ==========================================
    print("\n--- Test 3: Rule Distribution ---")
    
    total_sweeping = 0
    total_parking = 0
    total_meters = 0
    segments_with_sweeping = 0
    segments_with_parking = 0
    segments_with_meters = 0
    segments_with_blockface = 0
    
    for segment in segments:
        rules = segment.get("rules", [])
        sweeping = sum(1 for r in rules if r["type"] == "street-sweeping")
        parking = sum(1 for r in rules if r["type"] == "parking-regulation")
        
        total_sweeping += sweeping
        total_parking += parking
        
        if sweeping > 0:
            segments_with_sweeping += 1
        if parking > 0:
            segments_with_parking += 1
        if segment.get("schedules"):
            segments_with_meters += 1
            total_meters += len(segment.get("schedules"))
        if segment.get("blockfaceGeometry"):
            segments_with_blockface += 1
    
    print(f"Total street sweeping rules: {total_sweeping}")
    print(f"  Segments with sweeping: {segments_with_sweeping}/{actual_segments} ({segments_with_sweeping/actual_segments*100:.1f}%)")
    
    print(f"\nTotal parking regulations: {total_parking}")
    print(f"  Segments with parking regs: {segments_with_parking}/{actual_segments} ({segments_with_parking/actual_segments*100:.1f}%)")
    
    print(f"\nTotal meter schedules: {total_meters}")
    print(f"  Segments with meters: {segments_with_meters}/{actual_segments} ({segments_with_meters/actual_segments*100:.1f}%)")
    
    print(f"\nSegments with blockface geometry: {segments_with_blockface}/{actual_segments} ({segments_with_blockface/actual_segments*100:.1f}%)")

    # ==========================================
    # Test 4: Side Distribution Validation
    # ==========================================
    print("\n--- Test 4: Side Distribution ---")
    
    left_segments = sum(1 for s in segments if s.get("side") == "L")
    right_segments = sum(1 for s in segments if s.get("side") == "R")
    
    print(f"Left segments: {left_segments}")
    print(f"Right segments: {right_segments}")
    
    if left_segments == right_segments:
        print("✓ PASS: Equal distribution of Left and Right sides")
    else:
        print(f"✗ FAIL: Unequal distribution (diff: {abs(left_segments - right_segments)})")

    # ==========================================
    # Test 5: Sample Random Segments
    # ==========================================
    print("\n--- Test 5: Sample Random Segments ---")
    
    import random
    sample_size = min(5, len(segments))
    sample_segments = random.sample(segments, sample_size)
    
    for seg in sample_segments:
        print(f"\nCNN {seg.get('cnn')} ({seg.get('side')}): {seg.get('streetName')}")
        rules = seg.get("rules", [])
        print(f"  Rules: {len(rules)} ({sum(1 for r in rules if r['type']=='street-sweeping')} sweeping, "
              f"{sum(1 for r in rules if r['type']=='parking-regulation')} parking)")
        print(f"  Schedules: {len(seg.get('schedules', []))}")
        print(f"  Has blockface: {'Yes' if seg.get('blockfaceGeometry') else 'No'}")

    # ==========================================
    # Test 6: Verify Indexes
    # ==========================================
    print("\n--- Test 6: Database Indexes ---")
    
    indexes = await db.street_segments.list_indexes().to_list(None)
    index_names = [idx['name'] for idx in indexes]
    
    print(f"Indexes found: {len(indexes)}")
    for idx in indexes:
        print(f"  - {idx['name']}: {idx.get('key', {})}")
    
    required_indexes = ["cnn_1_side_1", "centerlineGeometry_2dsphere"]
    for req_idx in required_indexes:
        if any(req_idx in name for name in index_names):
            print(f"✓ Has required index: {req_idx}")
        else:
            print(f"✗ Missing index: {req_idx}")

    # ==========================================
    # Summary
    # ==========================================
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    checks = {
        "100% Coverage": actual_segments == expected_segments,
        "CNN 1046000 exists": segment_1046_L is not None and segment_1046_R is not None,
        "Has street sweeping": total_sweeping > 0,
        "Has parking regulations": total_parking > 0,
        "Equal L/R distribution": left_segments == right_segments,
    }
    
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    print(f"\nPassed: {passed}/{total} checks")
    for check, result in checks.items():
        symbol = "✓" if result else "✗"
        print(f"{symbol} {check}")
    
    if passed == total:
        print("\n✓✓✓ ALL VALIDATIONS PASSED ✓✓✓")
        print("The CNN segment architecture is working correctly!")
    else:
        print(f"\n⚠ {total - passed} validation(s) failed")
        print("Review the results above for details.")

    client.close()

if __name__ == "__main__":
    asyncio.run(validate_cnn_segments())