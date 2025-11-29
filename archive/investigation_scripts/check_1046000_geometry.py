import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
import json

async def check():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    mongodb_uri = os.getenv("MONGODB_URI")
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    target_cnn = "1046000"
    print(f"Checking geometries for CNN {target_cnn}...")
    
    segments = await db.street_segments.find({"cnn": target_cnn}).to_list(length=10)
    
    for seg in segments:
        side = seg['side']
        bf_geo = seg.get('blockfaceGeometry')
        cl_geo = seg.get('centerlineGeometry')
        
        print(f"\nSide: {side}")
        if bf_geo:
            coords = bf_geo['coordinates']
            print(f"  Blockface Geometry (Start): {coords[0]}")
            print(f"  Blockface Geometry (End):   {coords[-1]}")
        else:
            print("  NO BLOCKFACE GEOMETRY!")
            
        if cl_geo:
            coords = cl_geo['coordinates']
            print(f"  Centerline Geometry (Start): {coords[0]}")
            
    client.close()

if __name__ == "__main__":
    asyncio.run(check())