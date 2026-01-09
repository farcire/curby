"""
Test script for RuleDisplayFormatter
Demonstrates the new centralized rule display logic
"""

from regulation_normalizer import (
    format_segment_for_modal,
    format_rule_for_modal,
    sort_rules_for_modal,
    calculate_next_restriction
)
from datetime import datetime

# Sample segment data (as it would come from MongoDB)
sample_segment = {
    "cnn": "961000",
    "side": "R",
    "streetName": "19TH ST",
    "cardinalDirection": "North",
    "fromAddress": "2700",
    "toAddress": "2798",
    "fromStreet": "York St",
    "toStreet": "Bryant St",
    "rules": [
        {
            "type": "street-sweeping",
            "activeDays": [3],  # Thursday
            "startTimeMin": 0,   # 12:00 AM
            "endTimeMin": 360,   # 6:00 AM
            "displayDays": "Thu",
            "displayTime": "12:00 AM-6:00 AM"
        },
        {
            "type": "time-limit",
            "activeDays": [0, 1, 2, 3, 4],  # Mon-Fri
            "startTimeMin": 480,  # 8:00 AM
            "endTimeMin": 1080,   # 6:00 PM
            "durationMinutes": 120,
            "displayDays": "Weekdays",
            "displayTime": "8:00 AM-6:00 PM",
            "displayDuration": "2hr",
            "permitArea": "W"  # RPP Zone W - time limit applies to non-permit holders
        },
        {
            "type": "rpp-zone",
            "permitArea": "W",
            "activeDays": [0, 1, 2, 3, 4, 5, 6],
            "displayDays": "Daily"
        }
    ]
}

# Sample segment with metered parking
sample_metered_segment = {
    "cnn": "868000",
    "side": "L",
    "streetName": "YORK ST",
    "cardinalDirection": "West",
    "fromAddress": "700",
    "toAddress": "798",
    "fromStreet": "19th St",
    "toStreet": "20th St",
    "rules": [
        {
            "type": "street-sweeping",
            "activeDays": [2],  # Wednesday
            "startTimeMin": 0,
            "endTimeMin": 360,
            "displayDays": "Wed",
            "displayTime": "12:00 AM-6:00 AM"
        },
        {
            "type": "time-limit",
            "activeDays": [0, 1, 2, 3, 4],
            "startTimeMin": 480,
            "endTimeMin": 1080,
            "durationMinutes": 480,  # 8 hours
            "displayDays": "Weekdays",
            "displayTime": "8:00 AM-6:00 PM",
            "displayDuration": "8hr"
        },
        {
            "type": "metered",
            "activeDays": [0, 1, 2, 3, 4, 5],  # Mon-Sat
            "startTimeMin": 540,  # 9:00 AM
            "endTimeMin": 1080,   # 6:00 PM
            "displayDays": "Mon-Sat",
            "displayTime": "9:00 AM-6:00 PM",
            "rate": "4.00"
        }
    ]
}

def test_individual_rule_formatting():
    """Test formatting individual rules"""
    print("=" * 80)
    print("TEST 1: Individual Rule Formatting")
    print("=" * 80)
    
    for rule in sample_segment["rules"]:
        display_text = format_rule_for_modal(rule)
        print(f"\nRule Type: {rule['type']}")
        print(f"Display Text: {display_text}")

def test_rule_sorting():
    """Test rule sorting (frequency → Monday-first)"""
    print("\n" + "=" * 80)
    print("TEST 2: Rule Sorting")
    print("=" * 80)
    
    print("\nOriginal order:")
    for i, rule in enumerate(sample_segment["rules"], 1):
        print(f"{i}. {rule['type']}")
    
    sorted_rules = sort_rules_for_modal(sample_segment["rules"])
    
    print("\nSorted order (frequency → Monday-first):")
    for i, rule in enumerate(sorted_rules, 1):
        has_monday = 0 in rule.get('activeDays', [])
        print(f"{i}. {rule['type']} (has Monday: {has_monday})")

def test_next_restriction():
    """Test next restriction calculation"""
    print("\n" + "=" * 80)
    print("TEST 3: Next Restriction Calculation")
    print("=" * 80)
    
    # Test with current time
    current = datetime.now()
    print(f"\nCurrent time: {current.strftime('%A %I:%M %p')}")
    
    next_restriction = calculate_next_restriction(sample_segment["rules"], current)
    
    if next_restriction:
        print(f"\nNext restriction found:")
        print(f"  Type: {next_restriction['type']}")
        print(f"  Display: {next_restriction['display']}")
        print(f"  Days until: {next_restriction['days_until']}")
    else:
        print("\nNo upcoming restrictions found")

def test_complete_modal_formatting():
    """Test complete modal content generation"""
    print("\n" + "=" * 80)
    print("TEST 4: Complete Modal Content (Non-Metered)")
    print("=" * 80)
    
    modal_content = format_segment_for_modal(sample_segment)
    
    print(f"\nLocation: {modal_content['location_text']}")
    print(f"Cross Streets: {modal_content['cross_streets_text']}")
    print(f"\nRules ({len(modal_content['rules'])} total):")
    for i, rule in enumerate(modal_content['rules'], 1):
        prohibition = "🚫" if rule['is_absolute_prohibition'] else "ℹ️"
        print(f"  {i}. {prohibition} {rule['display_text']}")
    
    if modal_content['next_restriction']:
        print(f"\nNext Restriction: {modal_content['next_restriction']['display']}")
    
    print("\n" + "=" * 80)
    print("TEST 5: Complete Modal Content (Metered)")
    print("=" * 80)
    
    modal_content_metered = format_segment_for_modal(sample_metered_segment)
    
    print(f"\nLocation: {modal_content_metered['location_text']}")
    print(f"Cross Streets: {modal_content_metered['cross_streets_text']}")
    print(f"\nRules ({len(modal_content_metered['rules'])} total):")
    for i, rule in enumerate(modal_content_metered['rules'], 1):
        prohibition = "🚫" if rule['is_absolute_prohibition'] else "ℹ️"
        print(f"  {i}. {prohibition} {rule['display_text']}")
    
    if modal_content_metered['next_restriction']:
        print(f"\nNext Restriction: {modal_content_metered['next_restriction']['display']}")

def show_modal_ui_example():
    """Show how the modal UI would look"""
    print("\n" + "=" * 80)
    print("MODAL UI EXAMPLE (as it would appear in app)")
    print("=" * 80)
    
    modal_content = format_segment_for_modal(sample_segment)
    
    print("""
╔════════════════════════════════════════════════════════╗
║  ✅ You can park here!                            [X]  ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  📍 """ + modal_content['location_text'] + """
║                                                        ║
║  """ + (modal_content['cross_streets_text'] or '') + """
║                                                        ║
║  RULES:                                                ║""")
    
    for rule in modal_content['rules']:
        print(f"║    • {rule['display_text']:<48}║")
    
    if modal_content['next_restriction']:
        print(f"""║                                                        ║
║  ⚠️  Next restriction: {modal_content['next_restriction']['display']:<28}║""")
    
    print("""║                                                        ║
║  Report Error              🧭 Get Directions         ║
╚════════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    test_individual_rule_formatting()
    test_rule_sorting()
    test_next_restriction()
    test_complete_modal_formatting()
    show_modal_ui_example()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  ✅ Individual rule formatting")
    print("  ✅ Rule sorting (frequency → Monday-first)")
    print("  ✅ Next restriction calculation")
    print("  ✅ Complete modal content generation")
    print("  ✅ Backend owns ALL text content")
    print("  ✅ Frontend owns design/layout only")