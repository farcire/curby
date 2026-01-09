"""
Fix street names in street_segments collection by re-joining with streets collection
"""
import os
import asyncio
from pymongo import MongoClient
from dotenv import load_dotenv

async def fix_street_names():
    load_dotenv()
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client.curby
    
    print("Fixing street names in street_segments collection...")
    print("=" * 60)
    
    # Build lookup from streets collection: CNN -> street name
    print("\n1. Building CNN -> street name lookup from streets collection...")
    cnn_to_name = {}
    streets_cursor = db.streets.find({}, {"cnn": 1, "streetname_gc": 1})
    
    for street in streets_cursor:
        cnn = street.get("cnn")
        street_name = street.get("streetname_gc")
        if cnn and street_name:
            cnn_to_name[cnn] = street_name
    
    print(f"   ✓ Built lookup for {len(cnn_to_name)} CNNs")
    
    # Update street_segments collection
    print("\n2. Updating street_segments with correct street names...")
    segments_cursor = db.street_segments.find({}, {"_id": 1, "cnn": 1, "streetName": 1})
    
    updated_count = 0
    missing_count = 0
    batch_updates = []
    
    for segment in segments_cursor:
        segment_id = segment["_id"]
        cnn = segment.get("cnn")
        current_name = segment.get("streetName")
        
        # Only update if currently null
        if current_name is None or current_name == "None":
            if cnn in cnn_to_name:
                new_name = cnn_to_name[cnn]
                batch_updates.append({
                    "filter": {"_id": segment_id},
                    "update": {"$set": {"streetName": new_name}}
                })
                updated_count += 1
                
                # Execute batch updates every 1000 records
                if len(batch_updates) >= 1000:
                    for update in batch_updates:
                        db.street_segments.update_one(update["filter"], update["update"])
                    print(f"   Updated {updated_count} segments...")
                    batch_updates = []
            else:
                missing_count += 1
    
    # Execute remaining batch updates
    if batch_updates:
        for update in batch_updates:
            db.street_segments.update_one(update["filter"], update["update"])
    
    print(f"\n✓ Update complete!")
    print(f"   - Updated: {updated_count} segments")
    print(f"   - Missing CNNs: {missing_count} segments")
    
    # Verify the fix
    print("\n3. Verifying fix...")
    null_count = db.street_segments.count_documents({"streetName": None})
    total_count = db.street_segments.count_documents({})
    
    print(f"   Total segments: {total_count}")
    print(f"   Segments with null streetName: {null_count}")
    print(f"   Segments with streetName: {total_count - null_count}")
    
    if null_count == 0:
        print("\n✅ SUCCESS: All segments now have street names!")
    else:
        print(f"\n⚠️  WARNING: {null_count} segments still have null street names")
    
    # Show sample
    print("\n4. Sample updated segments:")
    samples = list(db.street_segments.find({"streetName": {"$ne": None}}).limit(5))
    for sample in samples:
        print(f"   CNN {sample['cnn']} ({sample['side']}): {sample['streetName']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_street_names())