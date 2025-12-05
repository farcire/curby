"""
Generate a list of CNNs that need manual verification of parking regulations.

This script identifies CNNs where:
1. Street cleaning data exists on only one side (L or R, not both)
2. The opposite side has blockface geometry but no parking rules available

Output: CSV file with CNN, street name, side, and address range for manual verification
"""
import os
import asyncio
import csv
from dotenv import load_dotenv
import motor.motor_asyncio
from collections import defaultdict

async def main():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    mongodb_uri = os.getenv("MONGODB_URI")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client["curby"]
    
    print("=== Generating Manual Verification List ===\n")
    print("Step 1: Finding CNNs with street cleaning on only one side...")
    
    # Get all street cleaning schedules
    all_schedules = await db.street_cleaning_schedules.find({}).to_list(None)
    
    # Group by CNN to find which sides have cleaning data
    cnn_cleaning_sides = defaultdict(set)
    for sched in all_schedules:
        cnn = sched.get('cnn')
        side = sched.get('cnnrightleft')
        if cnn and side:
            cnn_cleaning_sides[cnn].add(side)
    
    # Find CNNs with only one side having cleaning data
    cnns_missing_side = []
    for cnn, sides in cnn_cleaning_sides.items():
        if len(sides) == 1:
            has_side = list(sides)[0]
            missing_side = 'R' if has_side == 'L' else 'L'
            cnns_missing_side.append({
                'cnn': cnn,
                'has_cleaning': has_side,
                'missing_cleaning': missing_side
            })
    
    print(f"Found {len(cnns_missing_side)} CNNs with street cleaning on only one side\n")
    
    # Now check segments for these CNNs
    print("Step 2: Checking which missing sides have blockface but no parking rules...")
    
    manual_verification_needed = []
    
    for item in cnns_missing_side:
        cnn = item['cnn']
        missing_side = item['missing_cleaning']
        
        # Get both segments for this CNN
        segments = await db.street_segments.find({'cnn': cnn}).to_list(None)
        
        if len(segments) != 2:
            continue
        
        # Find the segment with missing cleaning
        missing_segment = None
        
        for seg in segments:
            if seg.get('side') == missing_side:
                missing_segment = seg
                break
        
        if not missing_segment:
            continue
        
        # Check if missing side has blockface but no rules
        has_blockface = missing_segment.get('blockfaceGeometry') is not None
        has_rules = len(missing_segment.get('rules', [])) > 0
        
        if has_blockface and not has_rules:
            manual_verification_needed.append({
                'cnn': cnn,
                'street_name': missing_segment.get('streetName', 'Unknown'),
                'side': missing_side,
                'from_address': missing_segment.get('fromAddress', ''),
                'to_address': missing_segment.get('toAddress', ''),
                'cardinal_direction': missing_segment.get('cardinalDirection', ''),
                'number_range': f"{missing_segment.get('fromAddress', '')}-{missing_segment.get('toAddress', '')}"
            })
    
    print(f"Found {len(manual_verification_needed)} blocks requiring manual verification\n")
    
    # Sort by street name for easier manual verification
    # Convert from_address to string for sorting to handle mixed types
    manual_verification_needed.sort(key=lambda x: (x['street_name'], str(x['from_address'])))
    
    # Write to CSV
    output_file = 'backend/manual_verification_list.csv'
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['cnn', 'street_name', 'side', 'cardinal_direction', 'from_address', 'to_address', 'number_range']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for item in manual_verification_needed:
            writer.writerow(item)
    
    print(f"✓ Manual verification list saved to: {output_file}\n")
    
    # Print summary statistics
    print("=== Summary ===")
    print(f"Total CNNs with unpaired street cleaning: {len(cnns_missing_side)}")
    print(f"CNNs with blockface but no rules on missing side: {len(manual_verification_needed)}")
    print(f"Percentage requiring manual verification: {(len(manual_verification_needed)/len(cnns_missing_side)*100):.1f}%\n")
    
    # Print first 10 examples
    print("First 10 blocks requiring manual verification:\n")
    for i, item in enumerate(manual_verification_needed[:10], 1):
        print(f"{i}. CNN {item['cnn']}: {item['street_name']} ({item['cardinal_direction']}) Side {item['side']}")
        print(f"   Address Range: {item['number_range']}")
        print()
    
    if len(manual_verification_needed) > 10:
        print(f"... and {len(manual_verification_needed) - 10} more blocks")
        print(f"\nFull list available in: {output_file}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())