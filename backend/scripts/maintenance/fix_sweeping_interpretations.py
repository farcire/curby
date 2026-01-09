"""
Fix Street Sweeping Interpretations

This script addresses two systemic issues:
1. Street sweeping rules with "None None" interpretations (22,573 segments)
2. "No parking any time" + sweeping combinations requiring special display (116 segments)
"""

import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = "curby"
COLLECTION_NAME = "street_segments"


def create_sweeping_interpretation(sweeping_rule: Dict) -> Dict:
    """
    Create proper interpretation for street sweeping rules.
    
    Args:
        sweeping_rule: The street-sweeping rule with day, startTime, endTime
    
    Returns:
        Proper interpretation dictionary
    """
    day = sweeping_rule.get('day', '')
    start_time = sweeping_rule.get('startTime', '')
    end_time = sweeping_rule.get('endTime', '')
    description = sweeping_rule.get('description', '')
    
    # Parse time for display
    def format_time(time_str):
        """Convert '9' to '9:00 AM', '13' to '1:00 PM'"""
        try:
            hour = int(time_str)
            if hour == 0:
                return "12:00 AM"
            elif hour < 12:
                return f"{hour}:00 AM"
            elif hour == 12:
                return "12:00 PM"
            else:
                return f"{hour - 12}:00 PM"
        except:
            return time_str
    
    start_display = format_time(start_time)
    end_display = format_time(end_time)
    
    # Create interpretation
    return {
        "type": "street-sweeping",
        "display": {
            "summary": "Street Cleaning",
            "details": f"No parking {day} {start_display}-{end_display} for street cleaning.",
            "severity": "medium",
            "icon": "street-cleaning"
        },
        "logic": {
            "time_ranges": [{
                "days": sweeping_rule.get('activeDays', []),
                "start": f"{int(start_time):02d}:00" if start_time else "00:00",
                "end": f"{int(end_time):02d}:00" if end_time else "00:00"
            }]
        },
        "conditions": {},
        "meta": {
            "interpreted_at": datetime.utcnow().isoformat(),
            "original_text": description,
            "fixed_by": "fix_sweeping_interpretations.py"
        }
    }


def create_no_parking_plus_sweeping_interpretation(
    no_parking_rule: Dict,
    sweeping_rules: List[Dict]
) -> List[Dict]:
    """
    Create special two-line interpretation for "No parking any time" + sweeping.
    
    This clarifies that parking is prohibited at ALL times, not just during sweeping.
    
    Args:
        no_parking_rule: The no-parking rule
        sweeping_rules: List of sweeping rules
    
    Returns:
        List of interpreted rules with proper display logic
    """
    interpretations = []
    
    # First line: No parking any time (primary restriction)
    no_parking_interp = {
        "type": "no-parking",
        "display": {
            "summary": "No Parking Any Time",
            "details": "Parking is prohibited at all times on this block.",
            "severity": "high",
            "icon": "no-parking"
        },
        "logic": {
            "time_ranges": [{
                "days": [0, 1, 2, 3, 4, 5, 6],  # All days
                "start": "00:00",
                "end": "23:59"
            }]
        },
        "conditions": {},
        "meta": {
            "interpreted_at": datetime.utcnow().isoformat(),
            "original_text": no_parking_rule.get('description', 'No parking any time'),
            "fixed_by": "fix_sweeping_interpretations.py",
            "display_priority": 1  # Show first
        }
    }
    interpretations.append(no_parking_interp)
    
    # Second line(s): Street cleaning schedule (informational)
    for sweeping_rule in sweeping_rules:
        sweeping_interp = create_sweeping_interpretation(sweeping_rule)
        sweeping_interp['meta']['display_priority'] = 2  # Show after no-parking
        sweeping_interp['meta']['note'] = "Informational only - parking already prohibited"
        interpretations.append(sweeping_interp)
    
    return interpretations


async def fix_sweeping_interpretations():
    """Fix all street sweeping interpretations with 'None None' summaries"""
    print("=" * 80)
    print("FIXING STREET SWEEPING INTERPRETATIONS")
    print("=" * 80)
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    try:
        # Find all segments with sweeping rules that have "None None" interpretations
        cursor = collection.find({
            'rules.type': 'street-sweeping',
            'rules.interpretation.display.summary': 'None None'
        })
        
        segments = await cursor.to_list(length=None)
        print(f"Found {len(segments)} segments with broken sweeping interpretations")
        
        fixed_count = 0
        
        for segment in segments:
            rules = segment.get('rules', [])
            updated_rules = []
            segment_fixed = False
            
            for rule in rules:
                if (rule.get('type') == 'street-sweeping' and 
                    rule.get('interpretation', {}).get('display', {}).get('summary') == 'None None'):
                    
                    # Create proper interpretation
                    new_interpretation = create_sweeping_interpretation(rule)
                    rule['interpretation'] = new_interpretation
                    segment_fixed = True
                
                updated_rules.append(rule)
            
            if segment_fixed:
                # Update segment
                await collection.update_one(
                    {'_id': segment['_id']},
                    {
                        '$set': {
                            'rules': updated_rules,
                            'updated_at': datetime.utcnow()
                        }
                    }
                )
                fixed_count += 1
                
                if fixed_count % 100 == 0:
                    print(f"Fixed {fixed_count} segments...")
        
        print(f"\n✓ Fixed {fixed_count} segments with sweeping interpretations")
        
    finally:
        client.close()


async def fix_no_parking_plus_sweeping():
    """Fix segments with 'No parking any time' + sweeping combinations"""
    print("\n" + "=" * 80)
    print("FIXING NO PARKING + SWEEPING COMBINATIONS")
    print("=" * 80)
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    try:
        # Load the 116 segments that need special handling
        with open('backend/segments_no_parking_plus_sweeping.json', 'r') as f:
            problem_segments = json.load(f)
        
        print(f"Found {len(problem_segments)} segments needing special interpretation")
        
        fixed_count = 0
        
        for problem_seg in problem_segments:
            cnn = problem_seg['cnn']
            side = problem_seg['side']
            
            # Fetch the actual segment
            segment = await collection.find_one({'cnn': cnn, 'side': side})
            
            if not segment:
                continue
            
            rules = segment.get('rules', [])
            
            # Find no-parking and sweeping rules
            no_parking_rules = [r for r in rules if 'no parking' in r.get('description', '').lower() 
                               and 'any time' in r.get('description', '').lower()]
            sweeping_rules = [r for r in rules if r.get('type') == 'street-sweeping']
            
            if no_parking_rules and sweeping_rules:
                # Create special two-line interpretation
                updated_rules = []
                
                # Add the no-parking rule with proper interpretation
                for rule in rules:
                    if rule in no_parking_rules:
                        # Update no-parking interpretation
                        rule['interpretation'] = {
                            "type": "no-parking",
                            "display": {
                                "summary": "No Parking Any Time",
                                "details": "Parking is prohibited at all times on this block.",
                                "severity": "high",
                                "icon": "no-parking"
                            },
                            "logic": {
                                "time_ranges": [{
                                    "days": [0, 1, 2, 3, 4, 5, 6],
                                    "start": "00:00",
                                    "end": "23:59"
                                }]
                            },
                            "conditions": {},
                            "meta": {
                                "interpreted_at": datetime.utcnow().isoformat(),
                                "original_text": rule.get('description', ''),
                                "fixed_by": "fix_sweeping_interpretations.py",
                                "display_priority": 1
                            }
                        }
                    elif rule in sweeping_rules:
                        # Update sweeping interpretation with note
                        rule['interpretation'] = create_sweeping_interpretation(rule)
                        rule['interpretation']['meta']['display_priority'] = 2
                        rule['interpretation']['meta']['note'] = "Informational - parking already prohibited"
                    
                    updated_rules.append(rule)
                
                # Update segment
                await collection.update_one(
                    {'_id': segment['_id']},
                    {
                        '$set': {
                            'rules': updated_rules,
                            'updated_at': datetime.utcnow()
                        }
                    }
                )
                fixed_count += 1
                
                if fixed_count % 10 == 0:
                    print(f"Fixed {fixed_count} segments...")
        
        print(f"\n✓ Fixed {fixed_count} segments with no-parking + sweeping combinations")
        
    finally:
        client.close()


async def verify_fixes():
    """Verify that fixes were applied correctly"""
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    try:
        # Count segments with "None None" interpretations
        none_none_count = await collection.count_documents({
            'rules.interpretation.display.summary': 'None None'
        })
        print(f"Segments with 'None None' interpretations: {none_none_count:,}")
        
        # Count segments with proper sweeping interpretations
        proper_sweeping = await collection.count_documents({
            'rules.type': 'street-sweeping',
            'rules.interpretation.display.summary': 'Street Cleaning'
        })
        print(f"Segments with proper sweeping interpretations: {proper_sweeping:,}")
        
        # Sample a fixed segment
        sample = await collection.find_one({
            'rules.type': 'street-sweeping',
            'rules.interpretation.meta.fixed_by': 'fix_sweeping_interpretations.py'
        })
        
        if sample:
            print(f"\nSample fixed segment:")
            print(f"  CNN: {sample['cnn']}")
            print(f"  Side: {sample['side']}")
            print(f"  Display: {sample.get('displayName', 'N/A')}")
            
            sweeping_rules = [r for r in sample.get('rules', []) if r.get('type') == 'street-sweeping']
            if sweeping_rules:
                rule = sweeping_rules[0]
                print(f"  Sweeping interpretation:")
                print(f"    Summary: {rule['interpretation']['display']['summary']}")
                print(f"    Details: {rule['interpretation']['display']['details']}")
        
    finally:
        client.close()


async def main():
    """Main execution function"""
    print("Starting street sweeping interpretation fixes...\n")
    
    # Fix regular sweeping interpretations
    await fix_sweeping_interpretations()
    
    # Fix no-parking + sweeping combinations
    await fix_no_parking_plus_sweeping()
    
    # Verify fixes
    await verify_fixes()
    
    print("\n" + "=" * 80)
    print("FIXES COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())