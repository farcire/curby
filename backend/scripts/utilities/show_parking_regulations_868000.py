"""
Show ONLY parking regulations for CNN 868000, Side R (18th St North 2700-2798)
Excludes street cleaning rules
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

async def show_parking_regulations():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.curby
    
    print("=" * 100)
    print("PARKING REGULATIONS FOR CNN 868000, SIDE R (18TH STREET NORTH 2700-2798)")
    print("=" * 100)
    print()
    
    # Query for the specific segment
    doc = await db.street_segments.find_one({
        "cnn": "868000",
        "side": "R"
    })
    
    if not doc:
        print("ERROR: Segment not found!")
        client.close()
        return
    
    # Get all rules
    rules = doc.get("rules", [])
    
    # Filter for parking regulations only (exclude street-sweeping)
    parking_regs = [r for r in rules if r.get('type') != 'street-sweeping']
    
    print(f"Total rules: {len(rules)}")
    print(f"Parking regulations (excluding street cleaning): {len(parking_regs)}")
    print()
    
    if not parking_regs:
        print("No parking regulations found (only street cleaning rules exist)")
        client.close()
        return
    
    # Display each parking regulation
    for i, rule in enumerate(parking_regs, 1):
        print("=" * 100)
        print(f"PARKING REGULATION #{i}")
        print("=" * 100)
        print()
        
        print(f"Type: {rule.get('type')}")
        print()
        
        # Source text
        source_text = rule.get('source_text')
        if source_text:
            print(f"Source Text: {source_text}")
            print()
        
        # Source fields (ALL raw fields from the parking regulations dataset)
        source_fields = rule.get('source_fields', {})
        if source_fields:
            print("SOURCE FIELDS (Raw Data from Dataset):")
            print("-" * 100)
            for key, value in sorted(source_fields.items()):
                if value is not None:
                    print(f"  {key:20}: {value}")
            print()
        
        # Interpreted data (AI-generated)
        interpreted = rule.get('interpreted')
        if interpreted:
            print("AI INTERPRETATION:")
            print("-" * 100)
            print(f"  Action: {interpreted.get('action')}")
            print(f"  Summary: {interpreted.get('summary')}")
            print(f"  Severity: {interpreted.get('severity')}")
            print()
            
            conditions = interpreted.get('conditions', {})
            if conditions:
                print("  Conditions:")
                if conditions.get('days'):
                    print(f"    Days: {', '.join(conditions['days'])}")
                if conditions.get('hours'):
                    print(f"    Hours: {conditions['hours']}")
                if conditions.get('time_limit_minutes'):
                    hours = conditions['time_limit_minutes'] // 60
                    minutes = conditions['time_limit_minutes'] % 60
                    if hours > 0:
                        print(f"    Time Limit: {hours} hour(s) {minutes} minute(s)")
                    else:
                        print(f"    Time Limit: {minutes} minute(s)")
                if conditions.get('exceptions'):
                    print(f"    Exceptions: {', '.join(conditions['exceptions'])}")
                print()
            
            if interpreted.get('details'):
                print(f"  Additional Details: {interpreted['details']}")
                print()
            
            if interpreted.get('confidence_score') is not None:
                print(f"  Confidence Score: {interpreted['confidence_score']:.2f}")
            
            if interpreted.get('judge_verified'):
                print(f"  Judge Verified: Yes")
            print()
        
        # Legacy fields
        description = rule.get('description')
        if description:
            print(f"Legacy Description: {description}")
            print()
        
        time_ranges = rule.get('timeRanges', [])
        if time_ranges:
            print(f"Legacy Time Ranges:")
            for tr in time_ranges:
                print(f"  {json.dumps(tr, indent=4)}")
            print()
        
        metadata = rule.get('metadata', {})
        if metadata:
            print(f"Metadata:")
            print(json.dumps(metadata, indent=2))
            print()
        
        # Show complete rule as JSON
        print("COMPLETE RULE DATA (JSON):")
        print("-" * 100)
        print(json.dumps(rule, indent=2, default=str))
        print()
        print()
    
    # Save to file
    output_data = {
        "location": "18th Street North (2700-2798)",
        "cnn": "868000",
        "side": "R",
        "total_rules": len(rules),
        "parking_regulations_count": len(parking_regs),
        "parking_regulations": parking_regs
    }
    
    with open("backend/parking_regulations_868000.json", "w") as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Location: 18th Street North (2700-2798)")
    print(f"Total Rules: {len(rules)}")
    print(f"Parking Regulations: {len(parking_regs)}")
    print()
    print("Complete parking regulation data saved to: backend/parking_regulations_868000.json")
    print("=" * 100)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(show_parking_regulations())