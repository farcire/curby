import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
import json

async def inspect():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = client['curby']
    
    # Get a sample regulation
    reg = await db.parking_regulations.find_one({})
    
    if reg:
        print("=== PARKING REGULATION FIELDS ===\n")
        print("Available fields:")
        for key in sorted(reg.keys()):
            value = reg[key]
            if key == 'shape' or key == 'geometry':
                print(f"  {key}: <GeoJSON geometry>")
            elif isinstance(value, str) and len(value) > 50:
                print(f"  {key}: {value[:50]}...")
            else:
                print(f"  {key}: {value}")
        
        print("\n=== SAMPLE REGULATION ===")
        sample = {k: v for k, v in reg.items() if k not in ['shape', 'geometry', '_id']}
        print(json.dumps(sample, indent=2))
        
        # Check if CNN-related fields exist
        print("\n=== CNN-RELATED FIELDS ===")
        cnn_fields = [k for k in reg.keys() if 'cnn' in k.lower() or 'street' in k.lower()]
        if cnn_fields:
            print("Found potential join fields:")
            for field in cnn_fields:
                print(f"  {field}: {reg[field]}")
        else:
            print("NO CNN fields found!")
            print("\nThis means we need to use SPATIAL JOIN instead of CNN-based join")
    else:
        print("No regulations found in database")
    
    client.close()

asyncio.run(inspect())