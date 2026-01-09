"""Quick script to check the actual street name for CNN 961000"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio

async def main():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    mongodb_uri = os.getenv("MONGODB_URI")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except:
        db = client["curby"]
    
    # Find the segment
    segment = await db.street_segments.find_one({
        "cnn": "961000",
        "side": "R"
    })
    
    if segment:
        print(f"Found segment for CNN 961000, side R:")
        print(f"  streetName: '{segment.get('streetName')}'")
        print(f"  fromAddress: '{segment.get('fromAddress')}'")
        print(f"  toAddress: '{segment.get('toAddress')}'")
        print(f"  side: '{segment.get('side')}'")
        print(f"  Number of rules: {len(segment.get('rules', []))}")
        
        # Check if it has street sweeping
        has_sweeping = any(r.get('type') == 'street-sweeping' for r in segment.get('rules', []))
        print(f"  Has street sweeping: {has_sweeping}")
    else:
        print("Segment not found!")
    
    # Also check the L side for comparison
    segment_l = await db.street_segments.find_one({
        "cnn": "961000",
        "side": "L"
    })
    
    if segment_l:
        print(f"\nFor comparison, CNN 961000, side L:")
        print(f"  streetName: '{segment_l.get('streetName')}'")
        print(f"  fromAddress: '{segment_l.get('fromAddress')}'")
        print(f"  toAddress: '{segment_l.get('toAddress')}'")
        has_sweeping_l = any(r.get('type') == 'street-sweeping' for r in segment_l.get('rules', []))
        print(f"  Has street sweeping: {has_sweeping_l}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())