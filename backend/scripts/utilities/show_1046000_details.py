import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio

async def main():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print("CNN 1046000 Analysis")
    print("="*60)
    
    # Get segments
    segments = await db.street_segments.find({"cnn": "1046000"}).to_list(None)
    
    print(f"\nFound {len(segments)} segments for CNN 1046000\n")
    
    for seg in segments:
        side = seg.get('side')
        print(f"Side {side}:")
        print(f"  Address: {seg.get('fromAddress')} - {seg.get('toAddress')}")
        print(f"  Cardinal: {seg.get('cardinalDirection')}")
        print(f"  Display: {seg.get('displayName')}")
        
        rules = seg.get('rules', [])
        print(f"  Total Rules: {len(rules)}")
        
        sweeping = [r for r in rules if r.get('type') == 'street-sweeping']
        parking = [r for r in rules if r.get('type') == 'parking-regulation']
        
        print(f"    Sweeping: {len(sweeping)}")
        for r in sweeping:
            print(f"      - {r.get('day')} {r.get('startTime')}-{r.get('endTime')}")
        
        print(f"    Parking Regs: {len(parking)}")
        for r in parking:
            print(f"      - {r.get('regulation')}")
            print(f"        Days: {r.get('days')}, Time: {r.get('fromTime')}-{r.get('toTime')}")
            print(f"        Limit: {r.get('timeLimit')}hrs, Permit: {r.get('permitArea')}")
        
        print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())