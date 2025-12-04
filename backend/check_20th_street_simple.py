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
    
    print("Checking 20th Street data...")
    
    # Check street_cleaning_schedules
    sweeping = await db.street_cleaning_schedules.find({
        "streetname": {"$regex": "20TH", "$options": "i"}
    }).to_list(None)
    
    print(f"\nTotal sweeping records for 20TH ST: {len(sweeping)}")
    
    # Look for 2801-2899 range
    print("\nSearching for address range containing 28xx...")
    for s in sweeping:
        lf_fadd = str(s.get('lf_fadd', ''))
        lf_toadd = str(s.get('lf_toadd', ''))
        
        if '28' in lf_fadd or '28' in lf_toadd:
            print(f"\nFound:")
            print(f"  CNN: {s.get('cnn')}")
            print(f"  Side: {s.get('cnnrightleft')}")
            print(f"  Address: {lf_fadd} - {lf_toadd}")
            print(f"  Day: {s.get('weekday')}")
            print(f"  Blockside: {s.get('blockside')}")
    
    # Check street_segments
    print("\n" + "="*60)
    print("Checking street_segments collection...")
    segments = await db.street_segments.find({
        "streetName": {"$regex": "20TH", "$options": "i"}
    }).to_list(None)
    
    print(f"\nTotal segments for 20TH ST: {len(segments)}")
    
    # Look for 28xx addresses
    print("\nSegments with 28xx addresses:")
    for seg in segments:
        from_addr = str(seg.get('fromAddress', ''))
        to_addr = str(seg.get('toAddress', ''))
        
        if '28' in from_addr or '28' in to_addr:
            print(f"\nCNN {seg.get('cnn')} Side {seg.get('side')}:")
            print(f"  Address: {from_addr} - {to_addr}")
            print(f"  Cardinal: {seg.get('cardinalDirection')}")
            print(f"  Rules: {len(seg.get('rules', []))}")
            for rule in seg.get('rules', []):
                if rule.get('type') == 'street-sweeping':
                    print(f"    Sweeping: {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())