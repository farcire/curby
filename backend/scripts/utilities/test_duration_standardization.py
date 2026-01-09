"""
Test Duration Standardization Implementation
=============================================

Tests the new duration parsing and formatting functionality in regulation_normalizer.py
"""

from regulation_normalizer import (
    parse_duration,
    format_duration_display,
    format_duration_long,
    DurationParser,
    normalize_regulation
)


def test_duration_parsing():
    """Test various duration parsing scenarios"""
    print("=" * 80)
    print("DURATION PARSING TESTS")
    print("=" * 80)
    
    test_cases = [
        # (value, unit_hint, permit_area, expected_minutes, description)
        ("2", "hours", None, 120, "2 hours as string"),
        (2, "hours", None, 120, "2 hours as int"),
        (2.0, "hours", None, 120, "2 hours as float"),
        ("0.5", "hours", None, 30, "0.5 hours (30 min)"),
        (0.5, "hours", None, 30, "0.5 hours as float"),
        ("0.25", "hours", None, 15, "0.25 hours (15 min)"),
        ("1.5", "hours", None, 90, "1.5 hours (90 min)"),
        ("72", "hours", None, 4320, "72 hours without RPP"),
        ("72", "hours", "W", None, "72 hours with RPP (filtered out)"),
        (72, "hours", "HV", None, "72 hours with RPP area HV (filtered out)"),
        ("120", "minutes", None, 120, "120 minutes as string"),
        (120, "minutes", None, 120, "120 minutes as int"),
        ("30", "minutes", None, 30, "30 minutes"),
        ("240", "minutes", None, 240, "240 minutes (4 hours)"),
        ("0", None, None, None, "Zero string (no limit)"),
        (0, None, None, None, "Zero int (no limit)"),
        (None, None, None, None, "None value (no limit)"),
        ("", None, None, None, "Empty string (no limit)"),
        # Auto-detect tests (no unit_hint)
        ("2", None, None, 120, "Auto-detect: 2 → 2 hours"),
        ("30", None, None, 30, "Auto-detect: 30 → 30 minutes (>24)"),
        ("120", None, None, 120, "Auto-detect: 120 → 120 minutes (>24)"),
    ]
    
    passed = 0
    failed = 0
    
    for value, unit_hint, permit_area, expected, description in test_cases:
        result = parse_duration(value, unit_hint, permit_area)
        status = "✓" if result == expected else "✗"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} {description}")
        print(f"  Input: {value!r} (unit: {unit_hint}, permit: {permit_area})")
        print(f"  Expected: {expected}, Got: {result}")
        print()
    
    print(f"Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_duration_formatting():
    """Test duration formatting for display"""
    print("=" * 80)
    print("DURATION FORMATTING TESTS")
    print("=" * 80)
    
    test_cases = [
        # (minutes, expected_display, expected_long, description)
        (15, "15min", "15 minute limit", "15 minutes"),
        (30, "30min", "30 minute limit", "30 minutes"),
        (45, "45min", "45 minute limit", "45 minutes"),
        (60, "1hr", "1 hour limit", "1 hour"),
        (90, "1.5hr", "1.5 hour limit", "1.5 hours"),
        (120, "2hr", "2 hour limit", "2 hours"),
        (150, "2.5hr", "2.5 hour limit", "2.5 hours"),
        (180, "3hr", "3 hour limit", "3 hours"),
        (240, "4hr", "4 hour limit", "4 hours"),
        (None, "No", "No time limit", "No limit"),
    ]
    
    passed = 0
    failed = 0
    
    for minutes, expected_display, expected_long, description in test_cases:
        display = format_duration_display(minutes)
        long_format = format_duration_long(minutes)
        
        display_ok = display == expected_display
        long_ok = long_format == expected_long
        
        status = "✓" if (display_ok and long_ok) else "✗"
        
        if display_ok and long_ok:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} {description}")
        print(f"  Input: {minutes} minutes")
        print(f"  Display: Expected '{expected_display}', Got '{display}' {'✓' if display_ok else '✗'}")
        print(f"  Long: Expected '{expected_long}', Got '{long_format}' {'✓' if long_ok else '✗'}")
        print()
    
    print(f"Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_dataset_adapters():
    """Test dataset-specific duration adapters"""
    print("=" * 80)
    print("DATASET ADAPTER TESTS")
    print("=" * 80)
    
    all_passed = True
    
    # Test Parking Regulations adapter
    print("Parking Regulations (hi6h-neyh):")
    parking_reg_cases = [
        ({"hrlimit": "2"}, 120, "2 hour limit"),
        ({"hrlimit": 2.0}, 120, "2 hour limit (float)"),
        ({"hrlimit": "0.5"}, 30, "30 minute limit"),
        ({"hrlimit": "0.25"}, 15, "15 minute limit"),
        ({"hrlimit": "72", "rpparea1": "W"}, None, "72hr RPP → filtered out"),
        ({"hrlimit": 72, "rpparea2": "HV"}, None, "72hr RPP area HV → filtered out"),
        ({"hrlimit": "72"}, 4320, "72hr without RPP area"),
    ]
    
    for row, expected, description in parking_reg_cases:
        result = DurationParser.parse_parking_reg(row)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"  {status} {description}: {result} minutes (expected {expected})")
    print()
    
    # Test Meter Schedules adapter
    print("Meter Schedules (6cqg-dxku):")
    meter_schedule_cases = [
        ({"time_limit_minutes": 120}, 120, "2 hour limit"),
        ({"time_limit_minutes": 30}, 30, "30 minute limit"),
        ({"time_limit_minutes": 240}, 240, "4 hour limit"),
        ({"time_limit_minutes": 0}, None, "No limit"),
    ]
    
    for row, expected, description in meter_schedule_cases:
        result = DurationParser.parse_meter_schedule(row)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"  {status} {description}: {result} minutes (expected {expected})")
    print()
    
    # Test Meter Policies adapter
    print("Meter Policies (qq7v-hds4):")
    meter_policy_cases = [
        ({"timelimitminutes": 120}, 120, "2 hour limit"),
        ({"timelimitminutes": 30}, 30, "30 minute limit"),
        ({"timelimitminutes": 240}, 240, "4 hour limit"),
    ]
    
    for row, expected, description in meter_policy_cases:
        result = DurationParser.parse_meter_policy(row)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"  {status} {description}: {result} minutes (expected {expected})")
    print()
    
    return all_passed


def test_normalize_regulation_with_duration():
    """Test full normalization with duration"""
    print("=" * 80)
    print("FULL NORMALIZATION WITH DURATION")
    print("=" * 80)
    
    all_passed = True
    
    # Test 1: Parking regulation with 2hr duration
    print("\n1. Parking Regulation with 2hr limit:")
    parking_reg = {
        "days": "MON-FRI",
        "from_time": "8:00 AM",
        "to_time": "6:00 PM",
        "hrlimit": "2",
        "regulation": "2 HR PARKING"
    }
    
    result = normalize_regulation(parking_reg, "parking_reg")
    
    print(f"  Canonical duration: {result['canonical']['duration_minutes']} minutes")
    print(f"  Has limit: {result['canonical']['has_limit']}")
    print(f"  Display duration: {result['display']['duration']}")
    print(f"  Display long: {result['display']['duration_long']}")
    print(f"  Is RPP 72hr: {result['canonical']['is_rpp_72hr']}")
    
    if result['canonical']['duration_minutes'] != 120:
        print(f"  ✗ FAILED: Expected 120 minutes, got {result['canonical']['duration_minutes']}")
        all_passed = False
    elif result['display']['duration'] != "2hr":
        print(f"  ✗ FAILED: Expected '2hr', got '{result['display']['duration']}'")
        all_passed = False
    elif result['display']['duration_long'] != "2 hour limit":
        print(f"  ✗ FAILED: Expected '2 hour limit', got '{result['display']['duration_long']}'")
        all_passed = False
    else:
        print("  ✓ PASSED")
    
    # Test 2: 72hr RPP rule (should be filtered)
    print("\n2. 72hr RPP Rule (should be filtered):")
    rpp_reg = {
        "days": "DAILY",
        "from_time": "12:00 AM",
        "to_time": "11:59 PM",
        "hrlimit": "72",
        "rpparea1": "W",
        "regulation": "RPP AREA W"
    }
    
    result = normalize_regulation(rpp_reg, "parking_reg")
    
    print(f"  Canonical duration: {result['canonical']['duration_minutes']}")
    print(f"  Has limit: {result['canonical']['has_limit']}")
    print(f"  Display duration: {result['display']['duration']}")
    print(f"  Is RPP 72hr: {result['canonical']['is_rpp_72hr']}")
    
    if result['canonical']['duration_minutes'] is not None:
        print(f"  ✗ FAILED: Expected None (filtered), got {result['canonical']['duration_minutes']}")
        all_passed = False
    elif result['canonical']['is_rpp_72hr'] != True:
        print(f"  ✗ FAILED: Expected is_rpp_72hr=True, got {result['canonical']['is_rpp_72hr']}")
        all_passed = False
    elif result['display']['duration'] != "No":
        print(f"  ✗ FAILED: Expected 'No', got '{result['display']['duration']}'")
        all_passed = False
    else:
        print("  ✓ PASSED")
    
    # Test 3: Meter with 30min limit
    print("\n3. Meter with 30min limit:")
    meter = {
        "days_applied": "Mo-Fr",
        "beg_time_dt": "9:00 AM",
        "end_time_dt": "6:00 PM",
        "time_limit_minutes": 30
    }
    
    result = normalize_regulation(meter, "meter")
    
    print(f"  Canonical duration: {result['canonical']['duration_minutes']} minutes")
    print(f"  Display duration: {result['display']['duration']}")
    
    if result['canonical']['duration_minutes'] != 30:
        print(f"  ✗ FAILED: Expected 30 minutes, got {result['canonical']['duration_minutes']}")
        all_passed = False
    elif result['display']['duration'] != "30min":
        print(f"  ✗ FAILED: Expected '30min', got '{result['display']['duration']}'")
        all_passed = False
    else:
        print("  ✓ PASSED")
    
    print()
    return all_passed


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DURATION STANDARDIZATION TEST SUITE")
    print("=" * 80 + "\n")
    
    results = []
    
    results.append(("Duration Parsing", test_duration_parsing()))
    results.append(("Duration Formatting", test_duration_formatting()))
    results.append(("Dataset Adapters", test_dataset_adapters()))
    results.append(("Full Normalization", test_normalize_regulation_with_duration()))
    
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed. Please review the output above.")
    
    print()