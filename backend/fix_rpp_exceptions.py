"""
Fix missing RPP exceptions in golden dataset.
Adds "except residential permit" to summaries where RPP area is present but not mentioned.
"""

import csv

def fix_rpp_exceptions():
    """Add 'except residential permit' to summaries missing it."""
    
    # Read the CSV
    with open('golden_dataset_partial.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    
    fixed_count = 0
    
    for row in rows:
        rpparea1 = row.get('rpparea1', '').strip()
        golden_summary = row.get('golden_summary', '').strip()
        golden_action = row.get('golden_action', '').strip()
        
        # Check if RPP area exists and summary doesn't mention permit
        if rpparea1 and golden_summary:
            if 'except' not in golden_summary.lower() and 'permit' not in golden_summary.lower():
                # Add "except residential permit" to the end
                if golden_summary.endswith('.'):
                    row['golden_summary'] = golden_summary[:-1] + ' except residential permit.'
                else:
                    row['golden_summary'] = golden_summary + ' except residential permit'
                
                fixed_count += 1
                print(f"Fixed: {row['unique_id']}")
                print(f"  Old: {golden_summary}")
                print(f"  New: {row['golden_summary']}\n")
    
    # Write back to CSV
    with open('golden_dataset_partial.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✅ Fixed {fixed_count} entries")
    print(f"Updated file: golden_dataset_partial.csv")

if __name__ == "__main__":
    fix_rpp_exceptions()