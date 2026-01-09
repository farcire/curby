#!/usr/bin/env python3
"""
Clean up street_segments collection schema and fix RPP matching issues.

This script:
1. Removes the unused 'street_name' field (always NULL)
2. Standardizes on 'streetName' as the canonical field
3. Identifies and reports segments with incorrect RPP rules
4. Optionally clears and rebuilds the collection if needed
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from typing import Dict, List

async def analyze_rpp_issues(db) -> Dict:
    """Analyze RPP matching issues in the collection."""
    print("\n=== Analyzing RPP Issues ===")
    
    # Find segments with conflicting rules (both no-parking and time-limit)
    pipeline = [
        {
            "$match": {
                "rules": {"$exists": True, "$ne": []}
            }
        },
        {
            "$project": {
                "cnn": 1,
                "side": 1,
                "streetName": 1,
                "has_no_parking": {
                    "$anyElementTrue": {
                        "$map": {
                            "input": "$rules",
                            "as": "rule",
                            "in": {"$eq": ["$$rule.type", "no-parking"]}
                        }
                    }
                },
                "has_time_limit": {
                    "$anyElementTrue": {
                        "$map": {
                            "input": "$rules",
                            "as": "rule",
                            "in": {"$eq": ["$$rule.type", "time-limit"]}
                        }
                    }
                },
                "has_rpp": {
                    "$anyElementTrue": {
                        "$map": {
                            "input": "$rules",
                            "as": "rule",
                            "in": {"$ne": ["$$rule.permitArea", None]}
                        }
                    }
                },
                "rule_count": {"$size": "$rules"}
            }
        },
        {
            "$match": {
                "has_no_parking": True,
                "has_time_limit": True
            }
        }
    ]
    
    conflicting_segments = await db.street_segments.aggregate(pipeline).to_list(None)
    
    print(f"Found {len(conflicting_segments)} segments with conflicting rules")
    
    # Sample some conflicts
    if conflicting_segments:
        print("\nSample conflicts:")
        for seg in conflicting_segments[:5]:
            print(f"  CNN {seg['cnn']} {seg['side']}: {seg.get('streetName', 'Unknown')}")
            print(f"    Has no-parking: {seg['has_no_parking']}")
            print(f"    Has time-limit: {seg['has_time_limit']}")
            print(f"    Has RPP: {seg['has_rpp']}")
            print(f"    Total rules: {seg['rule_count']}")
    
    return {
        "conflicting_count": len(conflicting_segments),
        "conflicting_segments": conflicting_segments
    }

async def remove_street_name_field(db):
    """Remove the unused street_name field from all documents."""
    print("\n=== Removing street_name Field ===")
    
    # Check how many have this field
    with_field = await db.street_segments.count_documents({"street_name": {"$exists": True}})
    print(f"Documents with street_name field: {with_field}")
    
    if with_field > 0:
        result = await db.street_segments.update_many(
            {"street_name": {"$exists": True}},
            {"$unset": {"street_name": ""}}
        )
        print(f"✓ Removed street_name field from {result.modified_count} documents")
    else:
        print("✓ No documents have street_name field")

async def verify_streetname_field(db):
    """Verify streetName field is populated."""
    print("\n=== Verifying streetName Field ===")
    
    total = await db.street_segments.count_documents({})
    with_streetname = await db.street_segments.count_documents({"streetName": {"$ne": None}})
    with_street = await db.street_segments.count_documents({"street": {"$ne": None}})
    
    print(f"Total segments: {total:,}")
    print(f"With streetName: {with_streetname:,} ({with_streetname/total*100:.1f}%)")
    print(f"With street: {with_street:,} ({with_street/total*100:.1f}%)")
    
    # Check if we need to copy from 'street' to 'streetName'
    missing_streetname = await db.street_segments.count_documents({
        "streetName": None,
        "street": {"$ne": None}
    })
    
    if missing_streetname > 0:
        print(f"\n⚠️  {missing_streetname} segments have 'street' but not 'streetName'")
        print("Copying 'street' to 'streetName'...")
        
        # Copy street to streetName where streetName is missing
        result = await db.street_segments.update_many(
            {"streetName": None, "street": {"$ne": None}},
            [{"$set": {"streetName": "$street"}}]
        )
        print(f"✓ Copied {result.modified_count} values")

async def main():
    load_dotenv()
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")
    
    client = AsyncIOMotorClient(mongodb_uri, serverSelectionTimeoutMS=30000)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    # Test connection
    try:
        await db.command('ping')
        print("✓ Connected to MongoDB")
    except Exception as e:
        print(f"ERROR: Failed to connect: {e}")
        client.close()
        return
    
    print("\n" + "=" * 80)
    print("STREET SEGMENTS SCHEMA CLEANUP")
    print("=" * 80)
    
    # Step 1: Analyze RPP issues
    rpp_analysis = await analyze_rpp_issues(db)
    
    # Step 2: Remove street_name field
    await remove_street_name_field(db)
    
    # Step 3: Verify and fix streetName field
    await verify_streetname_field(db)
    
    # Step 4: Provide recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if rpp_analysis["conflicting_count"] > 0:
        print(f"\n⚠️  Found {rpp_analysis['conflicting_count']} segments with conflicting rules")
        print("\nOptions to fix:")
        print("1. Run repopulate_segment_rules.py to rebuild rules arrays")
        print("2. Manually remove incorrect RPP rules from specific segments")
        print("3. Clear and rebuild entire collection (most thorough)")
        
        print("\nTo rebuild the collection:")
        print("  cd backend && python3 repopulate_segment_rules.py")
    else:
        print("\n✓ No conflicting rules found")
    
    print("\n✓ Schema cleanup complete!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())