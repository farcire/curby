#!/usr/bin/env python3
"""Quick Mission Neighborhood Analysis - Direct MongoDB Query"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

def main():
    # Connect to MongoDB
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not found")
        sys.exit(1)
    
    client = MongoClient(mongodb_uri)
    db = client['curby']
    
    print("=" * 100)
    print("MISSION NEIGHBORHOOD DATA ANALYSIS - COMPREHENSIVE REPORT")
    print("=" * 100)
    
    # Part 1: Collections Overview
    print("\n### PART 1: DATABASE COLLECTIONS ###\n")
    collections = db.list_collection_names()
    print(f"Total Collections: {len(collections)}\n")
    
    for coll in sorted(collections):
        count = db[coll].count_documents({})
        print(f"  {coll:.<40} {count:>10,} documents")
    
    # Part 2: Street Segments Analysis
    print("\n\n### PART 2: STREET SEGMENTS ANALYSIS ###\n")
    total_segments = db.street_segments.count_documents({})
    print(f"Total Street Segments: {total_segments:,}\n")
    
    # By zip code
    print("Segments by Zip Code:")
    zip_counts = {}
    for doc in db.street_segments.find({}, {"zip_code": 1}):
        zip_code = doc.get("zip_code", "Unknown")
        zip_counts[zip_code] = zip_counts.get(zip_code, 0) + 1
    
    for zip_code in sorted(zip_counts.keys()):
        print(f"  {zip_code}: {zip_counts[zip_code]:,} segments")
    
    # By side
    print("\nSegments by Side:")
    left_count = db.street_segments.count_documents({"side": "L"})
    right_count = db.street_segments.count_documents({"side": "R"})
    print(f"  Left (L):  {left_count:,}")
    print(f"  Right (R): {right_count:,}")
    print(f"  Balance:   {abs(left_count - right_count)} difference")
    
    # Geometry coverage
    print("\nGeometry Coverage:")
    with_centerline = db.street_segments.count_documents({"centerlineGeometry": {"$exists": True, "$ne": None}})
    with_blockface = db.street_segments.count_documents({"blockfaceGeometry": {"$exists": True, "$ne": None}})
    print(f"  Centerline: {with_centerline:,} ({with_centerline/total_segments*100:.1f}%)")
    print(f"  Blockface:  {with_blockface:,} ({with_blockface/total_segments*100:.1f}%)")
    
    # Address ranges
    print("\nAddress Range Coverage:")
    with_from = db.street_segments.count_documents({"fromAddress": {"$exists": True, "$ne": None}})
    with_to = db.street_segments.count_documents({"toAddress": {"$exists": True, "$ne": None}})
    with_both = db.street_segments.count_documents({
        "fromAddress": {"$exists": True, "$ne": None},
        "toAddress": {"$exists": True, "$ne": None}
    })
    print(f"  From Address: {with_from:,} ({with_from/total_segments*100:.1f}%)")
    print(f"  To Address:   {with_to:,} ({with_to/total_segments*100:.1f}%)")
    print(f"  Both:         {with_both:,} ({with_both/total_segments*100:.1f}%)")
    
    # Part 3: Rules Analysis
    print("\n\n### PART 3: RULES AND REGULATIONS ###\n")
    
    # Count segments with rules
    segments_with_rules = 0
    segments_with_sweeping = 0
    segments_with_parking_regs = 0
    segments_with_meters = 0
    total_rules = 0
    
    for seg in db.street_segments.find({}, {"rules": 1, "schedules": 1}):
        rules = seg.get("rules", [])
        schedules = seg.get("schedules", [])
        
        if rules:
            segments_with_rules += 1
            total_rules += len(rules)
            
            for rule in rules:
                if rule.get("type") == "street-sweeping":
                    segments_with_sweeping += 1
                    break
            
            for rule in rules:
                if rule.get("type") == "parking-regulation":
                    segments_with_parking_regs += 1
                    break
        
        if schedules:
            segments_with_meters += 1
    
    print(f"Rule Coverage:")
    print(f"  With Any Rules:         {segments_with_rules:,} ({segments_with_rules/total_segments*100:.1f}%)")
    print(f"  With Street Sweeping:   {segments_with_sweeping:,} ({segments_with_sweeping/total_segments*100:.1f}%)")
    print(f"  With Parking Regs:      {segments_with_parking_regs:,} ({segments_with_parking_regs/total_segments*100:.1f}%)")
    print(f"  With Meter Schedules:   {segments_with_meters:,} ({segments_with_meters/total_segments*100:.1f}%)")
    print(f"  With No Rules:          {total_segments - segments_with_rules:,} ({(total_segments - segments_with_rules)/total_segments*100:.1f}%)")
    print(f"\nTotal Rules: {total_rules:,}")
    print(f"Average Rules per Segment: {total_rules/total_segments:.2f}")
    
    # Part 4: Top Streets
    print("\n\n### PART 4: TOP 20 STREETS BY SEGMENT COUNT ###\n")
    street_counts = Counter()
    for seg in db.street_segments.find({}, {"streetName": 1}):
        street_counts[seg.get("streetName", "Unknown")] += 1
    
    for street, count in street_counts.most_common(20):
        print(f"  {street:.<50} {count:>3} segments")
    
    # Part 5: Sample Segments
    print("\n\n### PART 5: SAMPLE SEGMENT DETAILS ###\n")
    
    sample_streets = ["VALENCIA ST", "MISSION ST", "24TH ST", "BALMY ST"]
    
    for street_name in sample_streets:
        segments = list(db.street_segments.find({"streetName": street_name}).limit(2))
        
        if segments:
            print(f"\n{street_name}:")
            print("-" * 80)
            for seg in segments:
                print(f"  CNN: {seg.get('cnn')} | Side: {seg.get('side')}")
                print(f"  Address: {seg.get('fromAddress', 'N/A')} - {seg.get('toAddress', 'N/A')}")
                print(f"  From/To: {seg.get('fromStreet', 'N/A')} to {seg.get('toStreet', 'N/A')}")
                
                rules = seg.get('rules', [])
                if rules:
                    print(f"  Rules ({len(rules)}):")
                    for rule in rules[:2]:
                        rtype = rule.get('type', 'unknown')
                        if rtype == 'street-sweeping':
                            print(f"    • Sweeping: {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
                        elif rtype == 'parking-regulation':
                            print(f"    • Parking: {rule.get('regulation', 'N/A')[:60]}")
                    if len(rules) > 2:
                        print(f"    ... and {len(rules) - 2} more")
                else:
                    print(f"  Rules: None")
                print()
    
    # Part 6: Data Quality Summary
    print("\n### PART 6: DATA QUALITY SUMMARY ###\n")
    
    print("✅ STRENGTHS:")
    if with_centerline / total_segments > 0.99:
        print(f"  ✓ Excellent centerline coverage ({with_centerline/total_segments*100:.1f}%)")
    if with_both / total_segments > 0.90:
        print(f"  ✓ Strong address range coverage ({with_both/total_segments*100:.1f}%)")
    if segments_with_sweeping / total_segments > 0.70:
        print(f"  ✓ Good street sweeping coverage ({segments_with_sweeping/total_segments*100:.1f}%)")
    if abs(left_count - right_count) < total_segments * 0.01:
        print(f"  ✓ Well-balanced L/R distribution")
    
    print("\n⚠️  AREAS FOR IMPROVEMENT:")
    if with_blockface / total_segments < 0.60:
        print(f"  ! Limited blockface geometry ({with_blockface/total_segments*100:.1f}%)")
    if segments_with_parking_regs / total_segments < 0.30:
        print(f"  ! Parking regulations coverage ({segments_with_parking_regs/total_segments*100:.1f}%)")
    
    # Final Summary
    print("\n\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)
    
    print(f"\n📊 Key Metrics:")
    print(f"  • Total Segments: {total_segments:,}")
    print(f"  • Coverage: {with_centerline/total_segments*100:.1f}% geometry, {with_both/total_segments*100:.1f}% addresses")
    print(f"  • Rules: {total_rules:,} total ({total_rules/total_segments:.2f} avg per segment)")
    
    print(f"\n🔗 Data Integration:")
    print(f"  • Active Streets → Segments: ✅ Complete")
    print(f"  • Street Sweeping: ✅ {segments_with_sweeping/total_segments*100:.1f}%")
    print(f"  • Parking Regulations: {'✅' if segments_with_parking_regs > 0 else '⚠️'} {segments_with_parking_regs/total_segments*100:.1f}%")
    print(f"  • Meters: {'✅' if segments_with_meters > 0 else '⚠️'} {segments_with_meters/total_segments*100:.1f}%")
    
    print("\n" + "=" * 100)
    
    client.close()

if __name__ == "__main__":
    main()