"""
Mission Neighborhood Comprehensive Data Analysis

This script analyzes the complete data pipeline for San Francisco's Mission neighborhood,
showing how all datasets (Active Streets, Street Sweeping, Parking Regulations, Meters, 
and Intersections) are joined and integrated.
"""

import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from collections import defaultdict
import json
from datetime import datetime

load_dotenv()

async def analyze_mission_data():
    """Comprehensive analysis of Mission neighborhood data."""
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not found in .env file")
        return
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    print("=" * 100)
    print("MISSION NEIGHBORHOOD DATA ANALYSIS")
    print("=" * 100)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {db.name}")
    print("=" * 100)
    
    # ==========================================
    # PART 1: DATABASE OVERVIEW
    # ==========================================
    print("\n" + "=" * 100)
    print("PART 1: DATABASE COLLECTIONS OVERVIEW")
    print("=" * 100)
    
    collections = await db.list_collection_names()
    print(f"\nTotal Collections: {len(collections)}")
    print("\nCollections:")
    for coll in sorted(collections):
        count = await db[coll].count_documents({})
        print(f"  - {coll}: {count:,} documents")
    
    # ==========================================
    # PART 2: STREET SEGMENTS ANALYSIS
    # ==========================================
    print("\n" + "=" * 100)
    print("PART 2: STREET SEGMENTS ANALYSIS")
    print("=" * 100)
    
    total_segments = await db.street_segments.count_documents({})
    print(f"\nTotal Street Segments: {total_segments:,}")
    
    if total_segments == 0:
        print("\n⚠️  WARNING: No street segments found in database!")
        print("   You may need to run the ingestion script first:")
        print("   python3 ingest_data_cnn_segments.py")
        client.close()
        return
    
    # Segments by zip code
    print("\n--- Segments by Zip Code ---")
    zip_pipeline = [
        {"$group": {"_id": "$zip_code", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    async for doc in db.street_segments.aggregate(zip_pipeline):
        zip_code = doc["_id"] or "Unknown"
        print(f"  {zip_code}: {doc['count']:,} segments")
    
    # Segments by side
    print("\n--- Segments by Side ---")
    left_count = await db.street_segments.count_documents({"side": "L"})
    right_count = await db.street_segments.count_documents({"side": "R"})
    print(f"  Left (L): {left_count:,} segments")
    print(f"  Right (R): {right_count:,} segments")
    print(f"  Balance: {abs(left_count - right_count)} difference")
    
    # Geometry coverage
    print("\n--- Geometry Coverage ---")
    with_centerline = await db.street_segments.count_documents({"centerlineGeometry": {"$exists": True, "$ne": None}})
    with_blockface = await db.street_segments.count_documents({"blockfaceGeometry": {"$exists": True, "$ne": None}})
    print(f"  With Centerline Geometry: {with_centerline:,} ({with_centerline/total_segments*100:.1f}%)")
    print(f"  With Blockface Geometry: {with_blockface:,} ({with_blockface/total_segments*100:.1f}%)")
    
    # Address range coverage
    print("\n--- Address Range Coverage ---")
    with_from_addr = await db.street_segments.count_documents({"fromAddress": {"$exists": True, "$ne": None}})
    with_to_addr = await db.street_segments.count_documents({"toAddress": {"$exists": True, "$ne": None}})
    with_both_addr = await db.street_segments.count_documents({
        "fromAddress": {"$exists": True, "$ne": None},
        "toAddress": {"$exists": True, "$ne": None}
    })
    print(f"  With From Address: {with_from_addr:,} ({with_from_addr/total_segments*100:.1f}%)")
    print(f"  With To Address: {with_to_addr:,} ({with_to_addr/total_segments*100:.1f}%)")
    print(f"  With Both Addresses: {with_both_addr:,} ({with_both_addr/total_segments*100:.1f}%)")
    
    # ==========================================
    # PART 3: RULES AND SCHEDULES ANALYSIS
    # ==========================================
    print("\n" + "=" * 100)
    print("PART 3: RULES AND SCHEDULES ANALYSIS")
    print("=" * 100)
    
    # Count segments with different rule types
    with_sweeping = await db.street_segments.count_documents({
        "rules": {"$elemMatch": {"type": "street-sweeping"}}
    })
    with_parking_regs = await db.street_segments.count_documents({
        "rules": {"$elemMatch": {"type": "parking-regulation"}}
    })
    with_meters = await db.street_segments.count_documents({
        "schedules": {"$exists": True, "$ne": []}
    })
    with_any_rules = await db.street_segments.count_documents({
        "rules": {"$exists": True, "$ne": []}
    })
    
    print(f"\n--- Rule Coverage ---")
    print(f"  With Street Sweeping: {with_sweeping:,} ({with_sweeping/total_segments*100:.1f}%)")
    print(f"  With Parking Regulations: {with_parking_regs:,} ({with_parking_regs/total_segments*100:.1f}%)")
    print(f"  With Meter Schedules: {with_meters:,} ({with_meters/total_segments*100:.1f}%)")
    print(f"  With Any Rules: {with_any_rules:,} ({with_any_rules/total_segments*100:.1f}%)")
    print(f"  With No Rules: {total_segments - with_any_rules:,} ({(total_segments - with_any_rules)/total_segments*100:.1f}%)")
    
    # Total rules count
    pipeline = [
        {"$project": {"rule_count": {"$size": {"$ifNull": ["$rules", []]}}}},
        {"$group": {"_id": None, "total": {"$sum": "$rule_count"}}}
    ]
    result = await db.street_segments.aggregate(pipeline).to_list(1)
    total_rules = result[0]["total"] if result else 0
    print(f"\n--- Total Rules ---")
    print(f"  Total Rules Across All Segments: {total_rules:,}")
    print(f"  Average Rules per Segment: {total_rules/total_segments:.2f}")
    
    # ==========================================
    # PART 4: TOP STREETS ANALYSIS
    # ==========================================
    print("\n" + "=" * 100)
    print("PART 4: TOP STREETS ANALYSIS")
    print("=" * 100)
    
    print("\n--- Top 20 Streets by Segment Count ---")
    street_pipeline = [
        {"$group": {"_id": "$streetName", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    async for doc in db.street_segments.aggregate(street_pipeline):
        street_name = doc["_id"] or "Unknown"
        print(f"  {street_name}: {doc['count']} segments")
    
    # ==========================================
    # PART 5: SAMPLE SEGMENT DETAILS
    # ==========================================
    print("\n" + "=" * 100)
    print("PART 5: SAMPLE SEGMENT DETAILS")
    print("=" * 100)
    
    # Get a few interesting segments
    sample_streets = ["VALENCIA ST", "MISSION ST", "24TH ST", "BALMY ST"]
    
    for street_name in sample_streets:
        segments = await db.street_segments.find({
            "streetName": street_name
        }).limit(2).to_list(2)
        
        if segments:
            print(f"\n--- {street_name} (Sample) ---")
            for seg in segments:
                print(f"\n  CNN: {seg.get('cnn')} | Side: {seg.get('side')}")
                print(f"  Address Range: {seg.get('fromAddress', 'N/A')} - {seg.get('toAddress', 'N/A')}")
                print(f"  From/To: {seg.get('fromStreet', 'N/A')} to {seg.get('toStreet', 'N/A')}")
                
                rules = seg.get('rules', [])
                if rules:
                    print(f"  Rules ({len(rules)}):")
                    for rule in rules[:3]:  # Show first 3 rules
                        rule_type = rule.get('type', 'unknown')
                        if rule_type == 'street-sweeping':
                            print(f"    - Street Sweeping: {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
                        elif rule_type == 'parking-regulation':
                            print(f"    - Parking Reg: {rule.get('regulation', 'N/A')}")
                    if len(rules) > 3:
                        print(f"    ... and {len(rules) - 3} more rules")
                else:
                    print(f"  Rules: None")
                
                schedules = seg.get('schedules', [])
                if schedules:
                    print(f"  Meter Schedules: {len(schedules)}")
    
    # ==========================================
    # PART 6: INTERSECTION DATA
    # ==========================================
    print("\n" + "=" * 100)
    print("PART 6: INTERSECTION DATA")
    print("=" * 100)
    
    intersections_count = await db.intersections.count_documents({})
    perms_count = await db.intersection_permutations.count_documents({})
    nodes_count = await db.street_nodes.count_documents({})
    
    print(f"\n  Intersections: {intersections_count:,}")
    print(f"  Intersection Permutations: {perms_count:,}")
    print(f"  Street Nodes: {nodes_count:,}")
    
    # Sample intersection
    if perms_count > 0:
        print("\n--- Sample Intersection (24th & Mission) ---")
        sample_int = await db.intersection_permutations.find_one({
            "streets": {"$regex": "24TH.*MISSION|MISSION.*24TH", "$options": "i"}
        })
        if sample_int:
            print(f"  Streets: {sample_int.get('streets')}")
            print(f"  CNNs: {sample_int.get('cnn', [])}")
            if 'location' in sample_int:
                coords = sample_int['location'].get('coordinates', [])
                print(f"  Location: {coords}")
    
    # ==========================================
    # PART 7: RAW DATASET COLLECTIONS
    # ==========================================
    print("\n" + "=" * 100)
    print("PART 7: RAW DATASET COLLECTIONS")
    print("=" * 100)
    
    streets_count = await db.streets.count_documents({})
    sweeping_count = await db.street_cleaning_schedules.count_documents({})
    regs_count = await db.parking_regulations.count_documents({})
    
    print(f"\n  Active Streets (Raw): {streets_count:,}")
    print(f"  Street Cleaning Schedules (Raw): {sweeping_count:,}")
    print(f"  Parking Regulations (Raw): {regs_count:,}")
    
    # ==========================================
    # PART 8: DATA QUALITY SUMMARY
    # ==========================================
    print("\n" + "=" * 100)
    print("PART 8: DATA QUALITY SUMMARY")
    print("=" * 100)
    
    print("\n✅ STRENGTHS:")
    if with_centerline / total_segments > 0.99:
        print(f"  ✓ Excellent centerline geometry coverage ({with_centerline/total_segments*100:.1f}%)")
    if with_both_addr / total_segments > 0.90:
        print(f"  ✓ Strong address range coverage ({with_both_addr/total_segments*100:.1f}%)")
    if with_sweeping / total_segments > 0.70:
        print(f"  ✓ Good street sweeping coverage ({with_sweeping/total_segments*100:.1f}%)")
    if abs(left_count - right_count) < total_segments * 0.01:
        print(f"  ✓ Well-balanced L/R segment distribution")
    
    print("\n⚠️  AREAS FOR IMPROVEMENT:")
    if with_blockface / total_segments < 0.60:
        print(f"  ! Limited blockface geometry coverage ({with_blockface/total_segments*100:.1f}%)")
    if with_parking_regs / total_segments < 0.30:
        print(f"  ! Parking regulations coverage could be improved ({with_parking_regs/total_segments*100:.1f}%)")
    if (total_segments - with_any_rules) / total_segments > 0.20:
        print(f"  ! {(total_segments - with_any_rules)/total_segments*100:.1f}% of segments have no rules")
    
    # ==========================================
    # PART 9: SAMPLE QUERIES
    # ==========================================
    print("\n" + "=" * 100)
    print("PART 9: SAMPLE QUERY DEMONSTRATIONS")
    print("=" * 100)
    
    print("\n--- Query 1: Find segment by address ---")
    print("  Query: 3100 24TH ST")
    segment = await db.street_segments.find_one({
        "streetName": "24TH ST",
        "fromAddress": {"$lte": "3100"},
        "toAddress": {"$gte": "3100"}
    })
    if segment:
        print(f"  Result: CNN {segment.get('cnn')}-{segment.get('side')}")
        print(f"  Address Range: {segment.get('fromAddress')} - {segment.get('toAddress')}")
        print(f"  Rules: {len(segment.get('rules', []))}")
    else:
        print("  Result: No segment found")
    
    print("\n--- Query 2: Find all segments on Valencia St ---")
    valencia_count = await db.street_segments.count_documents({"streetName": "VALENCIA ST"})
    print(f"  Result: {valencia_count} segments found")
    
    print("\n--- Query 3: Segments with street sweeping on Tuesday ---")
    tuesday_count = await db.street_segments.count_documents({
        "rules": {"$elemMatch": {"type": "street-sweeping", "day": "Tuesday"}}
    })
    print(f"  Result: {tuesday_count} segments")
    
    # ==========================================
    # FINAL SUMMARY
    # ==========================================
    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)
    
    print(f"\n📊 Key Metrics:")
    print(f"  • Total Segments: {total_segments:,}")
    print(f"  • Coverage: {with_centerline/total_segments*100:.1f}% geometry, {with_both_addr/total_segments*100:.1f}% addresses")
    print(f"  • Rules: {total_rules:,} total ({total_rules/total_segments:.2f} avg per segment)")
    print(f"  • Data Quality: {'✅ Excellent' if with_centerline/total_segments > 0.99 else '⚠️ Good'}")
    
    print(f"\n📍 Geographic Coverage:")
    print(f"  • Mission District (94110, 94103)")
    print(f"  • {len(sample_streets)} major streets analyzed")
    print(f"  • {intersections_count:,} intersections mapped")
    
    print(f"\n🔗 Data Integration:")
    print(f"  • Active Streets → Street Segments: ✅ Complete")
    print(f"  • Street Sweeping Join: ✅ {with_sweeping/total_segments*100:.1f}%")
    print(f"  • Parking Regulations Join: {'✅' if with_parking_regs > 0 else '⚠️'} {with_parking_regs/total_segments*100:.1f}%")
    print(f"  • Meter Integration: {'✅' if with_meters > 0 else '⚠️'} {with_meters/total_segments*100:.1f}%")
    
    print("\n" + "=" * 100)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(analyze_mission_data())