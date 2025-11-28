import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
from shapely.geometry import shape, Point
import math

def calculate_distance(coord1, coord2):
    """Calculate approximate distance in degrees between two coordinates"""
    return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

async def verify():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print("=" * 80)
    print("VERIFYING CNN-TO-BLOCKFACE MAPPINGS")
    print("=" * 80)
    
    # Get all 20th Street data
    streets_20th = await db.streets.find(
        {"streetname": {"$regex": "^20TH", "$options": "i"}}
    ).sort("cnn", 1).to_list(None)
    
    blockfaces_20th = await db.blockfaces.find(
        {"streetName": {"$regex": "^20TH", "$options": "i"}}
    ).to_list(None)
    
    print(f"\n20th Street: {len(streets_20th)} CNN segments, {len(blockfaces_20th)} blockfaces")
    
    # For each blockface, verify it's associated with the correct CNN
    print("\n--- BLOCKFACE CNN VERIFICATION ---")
    for bf in blockfaces_20th:
        bf_cnn = bf.get('cnn')
        bf_side = bf.get('side')
        bf_geom = bf.get('geometry')
        
        if not bf_geom:
            continue
            
        print(f"\nBlockface claims CNN: {bf_cnn}, Side: {bf_side}")
        
        # Get the geometry
        try:
            bf_line = shape(bf_geom)
            bf_coords = list(bf_line.coords)
            bf_center = bf_line.interpolate(0.5, normalized=True)
            print(f"  Blockface center point: ({bf_center.x:.6f}, {bf_center.y:.6f})")
        except Exception as e:
            print(f"  Error parsing geometry: {e}")
            continue
        
        # Find which CNN centerline this blockface is closest to
        closest_cnn = None
        closest_distance = float('inf')
        
        for street in streets_20th:
            street_cnn = street.get('cnn')
            street_geom = street.get('line')
            
            if not street_geom:
                continue
                
            try:
                street_line = shape(street_geom)
                # Calculate distance from blockface center to this street centerline
                distance = street_line.distance(bf_center)
                
                if distance < closest_distance:
                    closest_distance = distance
                    closest_cnn = street_cnn
            except:
                continue
        
        print(f"  Closest CNN by geometry: {closest_cnn}")
        print(f"  Distance: {closest_distance:.8f} degrees (~{closest_distance * 111000:.1f} meters)")
        
        if closest_cnn != bf_cnn:
            print(f"  ⚠️  MISMATCH! Blockface claims {bf_cnn} but is closest to {closest_cnn}")
            
            # Show street sweeping data for both CNNs
            claimed_sweeping = await db.street_cleaning_schedules.find({"cnn": bf_cnn}).to_list(None)
            actual_sweeping = await db.street_cleaning_schedules.find({"cnn": closest_cnn}).to_list(None)
            
            print(f"\n  Street sweeping for claimed CNN {bf_cnn}:")
            for s in claimed_sweeping[:3]:
                print(f"    {s.get('weekday')} {s.get('fromhour')}-{s.get('tohour')} Side {s.get('cnnrightleft')}")
                print(f"    Limits: {s.get('limits')}")
            
            print(f"\n  Street sweeping for actual CNN {closest_cnn}:")
            for s in actual_sweeping[:3]:
                print(f"    {s.get('weekday')} {s.get('fromhour')}-{s.get('tohour')} Side {s.get('cnnrightleft')}")
                print(f"    Limits: {s.get('limits')}")
        else:
            print(f"  ✓ CORRECT mapping")
    
    # Check if CNN 1046000 geometry is near CNN 1055000 blockface
    print("\n" + "=" * 80)
    print("CNN 1046000 vs 1055000 PROXIMITY CHECK")
    print("=" * 80)
    
    street_1046 = await db.streets.find_one({"cnn": "1046000"})
    street_1055 = await db.streets.find_one({"cnn": "1055000"})
    
    if street_1046 and street_1055:
        try:
            line_1046 = shape(street_1046.get('line'))
            line_1055 = shape(street_1055.get('line'))
            
            distance = line_1046.distance(line_1055)
            print(f"\nDistance between CNN 1046000 and 1055000: {distance:.6f} degrees")
            print(f"Approximately {distance * 111000:.1f} meters")
            
            coords_1046 = list(line_1046.coords)
            coords_1055 = list(line_1055.coords)
            
            print(f"\nCNN 1046000 location:")
            print(f"  Start: {coords_1046[0]}")
            print(f"  End: {coords_1046[-1]}")
            
            print(f"\nCNN 1055000 location:")
            print(f"  Start: {coords_1055[0]}")
            print(f"  End: {coords_1055[-1]}")
            
            if distance < 0.01:  # If they're very close (< ~1km)
                print("\n⚠️  These CNNs are very close to each other!")
                print("    Spatial join may have incorrectly matched regulations")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("\nThe issue is:")
    print("  1. Only 7.4% of streets have blockface geometries from pep9-66vw")
    print("  2. Regulations/sweeping join via CNN when blockface exists")
    print("  3. For missing CNNs (like 1046000), we need to:")
    print("     a) Generate synthetic blockfaces from centerline + offset, OR")
    print("     b) Use direct CNN matching without requiring blockface geometry")
    
    print("\nRECOMMENDED FIX:")
    print("  Create blockfaces for ALL CNNs by offsetting centerline geometry")
    print("  This will enable proper regulation matching across all street segments")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(verify())