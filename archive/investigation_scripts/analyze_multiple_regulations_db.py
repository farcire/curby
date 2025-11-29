#!/usr/bin/env python3
"""
Analyze multiple regulations at same location using our MongoDB database.
"""

from pymongo import MongoClient
from collections import defaultdict
import json

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['parking_data']

def analyze_regulations_by_cnn():
    """Analyze regulations grouped by CNN."""
    
    print("=" * 80)
    print("ANALYZING MULTIPLE REGULATIONS BY CNN")
    print("=" * 80)
    
    # Get all parking regulations
    regulations = list(db.parking_regulations.find({}))
    print(f"\nTotal parking regulations in database: {len(regulations)}")
    
    # Group by CNN
    by_cnn = defaultdict(list)
    for reg in regulations:
        cnn = reg.get('cnn_id')
        if cnn:
            by_cnn[cnn].append(reg)
    
    print(f"Unique CNNs with regulations: {len(by_cnn)}")
    
    # Find CNNs with multiple regulations
    multi_reg_cnns = {cnn: regs for cnn, regs in by_cnn.items() if len(regs) > 1}
    print(f"CNNs with multiple regulations: {len(multi_reg_cnns)}")
    print(f"Percentage: {len(multi_reg_cnns) / len(by_cnn) * 100:.1f}%")
    
    # Show distribution
    reg_counts = defaultdict(int)
    for cnn, regs in by_cnn.items():
        reg_counts[len(regs)] += 1
    
    print("\nDistribution of regulations per CNN:")
    for count in sorted(reg_counts.keys()):
        print(f"  {count} regulation(s): {reg_counts[count]} CNNs")
    
    # Show examples
    print("\n" + "=" * 80)
    print("EXAMPLES OF CNNS WITH MULTIPLE REGULATIONS")
    print("=" * 80)
    
    examples = list(multi_reg_cnns.items())[:5]
    for i, (cnn, regs) in enumerate(examples, 1):
        print(f"\nExample {i}: CNN {cnn} ({len(regs)} regulations)")
        print("-" * 80)
        
        # Get street segment info
        segment = db.street_segments.find_one({'cnn': cnn})
        if segment:
            print(f"Street: {segment.get('street_name', 'Unknown')}")
            print(f"From: {segment.get('from_street', 'Unknown')} to {segment.get('to_street', 'Unknown')}")
            print(f"Side: {segment.get('side', 'Unknown')}")
        
        print(f"\nRegulations:")
        for j, reg in enumerate(regs, 1):
            print(f"\n  Regulation {j}:")
            print(f"    Type: {reg.get('regulation_type', 'N/A')}")
            print(f"    Time Limit: {reg.get('time_limit_minutes', 'N/A')} minutes")
            print(f"    Days: {reg.get('days_of_week', 'N/A')}")
            print(f"    Hours: {reg.get('start_time', 'N/A')} - {reg.get('end_time', 'N/A')}")
            print(f"    Rate: ${reg.get('rate_per_hour', 'N/A')}/hour" if reg.get('rate_per_hour') else "    Rate: N/A")
            
            # Check geometry
            if 'geometry' in reg:
                geom = reg['geometry']
                if geom and 'coordinates' in geom:
                    coords = geom['coordinates']
                    if isinstance(coords, list) and len(coords) > 0:
                        print(f"    Geometry: {geom.get('type', 'Unknown')} with {len(coords)} points")
        
        # Analyze if regulations overlap or are complementary
        print(f"\n  Analysis:")
        analyze_regulation_relationships(regs)

def analyze_regulation_relationships(regs):
    """Analyze if regulations are complementary or conflicting."""
    
    # Check for temporal overlap
    has_time_restrictions = []
    no_time_restrictions = []
    
    for reg in regs:
        if reg.get('start_time') or reg.get('end_time') or reg.get('days_of_week'):
            has_time_restrictions.append(reg)
        else:
            no_time_restrictions.append(reg)
    
    if len(has_time_restrictions) > 1:
        print("    ✓ Multiple time-restricted regulations (likely complementary)")
        
        # Check if they cover different times
        times = set()
        for reg in has_time_restrictions:
            time_key = (reg.get('days_of_week'), reg.get('start_time'), reg.get('end_time'))
            times.add(time_key)
        
        if len(times) == len(has_time_restrictions):
            print("    ✓ All regulations have different time periods (complementary)")
        else:
            print("    ⚠️  Some regulations have overlapping time periods (potential conflict)")
    
    # Check regulation types
    reg_types = [reg.get('regulation_type') for reg in regs]
    unique_types = set(reg_types)
    
    if len(unique_types) > 1:
        print(f"    Multiple regulation types: {', '.join(unique_types)}")
        
        # Check for conflicting types
        if 'NO PARKING' in reg_types and any('PARKING' in t for t in reg_types if t != 'NO PARKING'):
            print("    ⚠️  Conflicting types detected (NO PARKING vs PARKING)")
    else:
        print(f"    Same regulation type: {list(unique_types)[0]}")

def find_specific_location_example():
    """Find a specific example near Mission district coordinates."""
    
    print("\n" + "=" * 80)
    print("SEARCHING FOR REGULATIONS NEAR MISSION DISTRICT")
    print("=" * 80)
    
    # Mission district coordinates
    lat = 37.7526
    lng = -122.4107
    radius_meters = 50
    
    # Convert to radians for MongoDB query
    radius_radians = radius_meters / 6378100.0
    
    # Find street segments near this location
    segments = list(db.street_segments.find({
        'geometry': {
            '$near': {
                '$geometry': {
                    'type': 'Point',
                    'coordinates': [lng, lat]
                },
                '$maxDistance': radius_meters
            }
        }
    }).limit(10))
    
    print(f"\nFound {len(segments)} street segments within {radius_meters}m")
    
    for segment in segments:
        cnn = segment.get('cnn')
        if cnn:
            # Get regulations for this CNN
            regs = list(db.parking_regulations.find({'cnn_id': cnn}))
            
            if len(regs) > 1:
                print(f"\n{segment.get('street_name', 'Unknown')} ({segment.get('side', 'Unknown')} side)")
                print(f"CNN: {cnn}")
                print(f"Regulations: {len(regs)}")
                
                for i, reg in enumerate(regs, 1):
                    print(f"  {i}. {reg.get('regulation_type', 'N/A')}")
                    if reg.get('time_limit_minutes'):
                        print(f"     Time Limit: {reg.get('time_limit_minutes')} min")
                    if reg.get('days_of_week'):
                        print(f"     Days: {reg.get('days_of_week')}")
                    if reg.get('start_time') and reg.get('end_time'):
                        print(f"     Hours: {reg.get('start_time')} - {reg.get('end_time')}")

def main():
    try:
        analyze_regulations_by_cnn()
        find_specific_location_example()
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()