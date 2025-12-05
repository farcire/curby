"""
Get detailed parking information for 18th St North 2700-2798
CNN: 868000, Side: R
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

async def get_details():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.curby
    
    print("=" * 80)
    print("18TH STREET NORTH SIDE (2700-2798) - DETAILED PARKING INFORMATION")
    print("=" * 80)
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
    
    # Basic Information
    print("BASIC INFORMATION:")
    print("-" * 80)
    print(f"CNN: {doc.get('cnn')}")
    print(f"Side: {doc.get('side')}")
    print(f"Street Name: {doc.get('streetName')}")
    print(f"Cardinal Direction: {doc.get('cardinalDirection')}")
    print(f"Display Name: {doc.get('displayName')}")
    print(f"Display Cardinal: {doc.get('displayCardinal')}")
    print(f"From Street: {doc.get('fromStreet')}")
    print(f"To Street: {doc.get('toStreet')}")
    print(f"Address Range: {doc.get('fromAddress')}-{doc.get('toAddress')}")
    print(f"Zip Code: {doc.get('zip_code')}")
    print()
    
    # Rules
    rules = doc.get("rules", [])
    print(f"PARKING RULES ({len(rules)} total):")
    print("=" * 80)
    print()
    
    for i, rule in enumerate(rules, 1):
        print(f"RULE #{i}")
        print("-" * 80)
        print(f"Type: {rule.get('type')}")
        print()
        
        # Source text
        source_text = rule.get('source_text')
        if source_text:
            print(f"Source Text: {source_text}")
            print()
        
        # Source fields (raw data from dataset)
        source_fields = rule.get('source_fields', {})
        if source_fields:
            print("Source Fields (Raw Data):")
            for key, value in source_fields.items():
                if value:
                    print(f"  {key}: {value}")
            print()
        
        # Interpreted data (AI-generated human-readable)
        interpreted = rule.get('interpreted')
        if interpreted:
            print("AI Interpretation:")
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
            print(f"Description: {description}")
            print()
        
        time_ranges = rule.get('timeRanges', [])
        if time_ranges:
            print(f"Time Ranges:")
            for tr in time_ranges:
                print(f"  {json.dumps(tr, indent=4)}")
            print()
        
        metadata = rule.get('metadata', {})
        if metadata:
            print(f"Metadata:")
            print(json.dumps(metadata, indent=2))
            print()
        
        print()
    
    # Meter Schedules
    schedules = doc.get("schedules", [])
    print(f"METER SCHEDULES ({len(schedules)} total):")
    print("=" * 80)
    
    if schedules:
        for i, schedule in enumerate(schedules, 1):
            print(f"\nSchedule #{i}:")
            print(f"  Begin Time: {schedule.get('beginTime')}")
            print(f"  End Time: {schedule.get('endTime')}")
            print(f"  Rate: {schedule.get('rate')}")
            print(f"  Rate Qualifier: {schedule.get('rateQualifier')}")
            print(f"  Rate Unit: {schedule.get('rateUnit')}")
    else:
        print("No meter schedules found for this location.")
    
    print()
    print()
    
    # Export to JSON
    output_data = {
        "location": "18th Street North (2700-2798)",
        "cnn": doc.get("cnn"),
        "side": doc.get("side"),
        "basic_info": {
            "street_name": doc.get("streetName"),
            "cardinal_direction": doc.get("cardinalDirection"),
            "display_name": doc.get("displayName"),
            "from_street": doc.get("fromStreet"),
            "to_street": doc.get("toStreet"),
            "address_range": f"{doc.get('fromAddress')}-{doc.get('toAddress')}",
            "zip_code": doc.get("zip_code")
        },
        "rules": rules,
        "schedules": schedules
    }
    
    # Remove MongoDB _id
    if "_id" in doc:
        del doc["_id"]
    
    with open("backend/18th_st_north_details.json", "w") as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Location: 18th Street North (2700-2798)")
    print(f"Total Parking Rules: {len(rules)}")
    print(f"Total Meter Schedules: {len(schedules)}")
    print()
    print("Detailed data exported to: backend/18th_st_north_details.json")
    print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(get_details())