"""
Find the CNN for 19th Street and check for missing opposite sides in street cleaning data
"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from collections import defaultdict

async def main():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    mongodb_uri = os.getenv("MONGODB_URI")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client["curby"]
    
    print("=== Finding 19th Street CNN ===\n")
    
    # Find the street with address 2700-2799
    streets = await db.streets.find({
        "streetname": {"$regex": "19TH", "$options": "i"},
        "$or": [
            {"lf_fadd": {"$in": ["2700", "2701"]}},
            {"rt_fadd": {"$in": ["2700", "2701"]}}
        ]
    }).to_list(None)
    
    target_cnn = None
    for street in streets:
        print(f"CNN: {street.get('cnn')}")
        print(f"Street: {street.get('streetname')}")
        print(f"Left: {street.get('lf_fadd')} - {street.get('lf_toadd')}")
        print(f"Right: {street.get('rt_fadd')} - {street.get('rt_toadd')}")
        print()
        
        # Check if this matches our target
        if street.get('rt_fadd') == '2700' and street.get('rt_toadd') == '2798':
            target_cnn = street.get('cnn')
            print(f"✓ Found target CNN: {target_cnn}")
    
    if target_cnn:
        print(f"\n=== Checking street cleaning for CNN {target_cnn} ===\n")
        
        schedules = await db.street_cleaning_schedules.find({
            "cnn": target_cnn
        }).to_list(None)
        
        if schedules:
            for sched in schedules:
                print(f"Side: {sched.get('cnnrightleft')}")
                print(f"Blockside (cardinal): {sched.get('blockside')}")
                print(f"Day: {sched.get('weekday')}")
                print(f"Time: {sched.get('fromhour')} - {sched.get('tohour')}")
                print()
        else:
            print(f"❌ No street cleaning schedules found for CNN {target_cnn}")
    
    print("\n=== Analyzing Missing Opposite Sides Pattern ===\n")
    
    # Get all CNNs with street cleaning
    all_schedules = await db.street_cleaning_schedules.find({}).to_list(None)
    
    # Group by CNN
    cnn_sides = defaultdict(set)
    for sched in all_schedules:
        cnn = sched.get('cnn')
        side = sched.get('cnnrightleft')
        if cnn and side:
            cnn_sides[cnn].add(side)
    
    # Find CNNs with only one side
    missing_opposite = []
    for cnn, sides in cnn_sides.items():
        if len(sides) == 1:
            missing_opposite.append((cnn, list(sides)[0]))
    
    print(f"Total CNNs with street cleaning: {len(cnn_sides)}")
    print(f"CNNs with only one side (missing opposite): {len(missing_opposite)}")
    print(f"\nFirst 20 examples:")
    for cnn, side in missing_opposite[:20]:
        missing_side = 'R' if side == 'L' else 'L'
        print(f"  CNN {cnn}: Has {side}, Missing {missing_side}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())