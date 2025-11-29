import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
import json

async def inspect():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print("=" * 80)
    print("PARKING REGULATIONS RAW DATA")
    print("=" * 80)
    
    # Get a sample regulation from the raw collection
    reg = await db.parking_regulations.find_one({})
    
    if reg:
        print("\nAvailable fields in parking_regulations collection:")
        print("-" * 80)
        for key in sorted(reg.keys()):
            value = reg[key]
            if key in ['shape', 'geometry', 'the_geom']:
                print(f"  {key}: <GeoJSON geometry>")
            elif isinstance(value, str) and len(value) > 80:
                print(f"  {key}: {value[:80]}...")
            else:
                print(f"  {key}: {value}")
        
        print("\n" + "=" * 80)
        print("SAMPLE REGULATION (JSON)")
        print("=" * 80)
        
        # Remove geometry fields for cleaner output
        sample = {k: v for k, v in reg.items() if k not in ['shape', 'geometry', 'the_geom', '_id']}
        print(json.dumps(sample, indent=2, default=str))
        
        print("\n" + "=" * 80)
        print("FIELDS WE'RE TRYING TO EXTRACT")
        print("=" * 80)
        print(f"time_limit: {reg.get('time_limit')}")
        print(f"rpp_area: {reg.get('rpp_area')}")
        print(f"street_parking_description: {reg.get('street_parking_description')}")
        print(f"description: {reg.get('description')}")
        
        print("\n" + "=" * 80)
        print("ALTERNATIVE FIELD NAMES TO CHECK")
        print("=" * 80)
        
        # Check for alternative field names
        alt_fields = [
            'timelimit', 'time', 'limit', 'hours',
            'rpp', 'permit', 'area',
            'desc', 'details', 'regulation', 'parking',
            'street_name', 'location'
        ]
        
        for field in alt_fields:
            matching = [k for k in reg.keys() if field.lower() in k.lower()]
            if matching:
                print(f"Fields containing '{field}':")
                for k in matching:
                    print(f"  {k}: {reg.get(k)}")
    else:
        print("No regulations found in database")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(inspect())