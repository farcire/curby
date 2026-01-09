"""
Re-process meter schedules only - updates existing segments with schedule_type field.
This script fetches meter schedules again and updates the existing segments in MongoDB.
"""
import os
import asyncio
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
import motor.motor_asyncio
from typing import List, Dict, Any
from regulation_normalizer import (
    normalize_cap_color,
    aggregate_blockface_cap_colors,
    aggregate_blockface_tow_schedules,
    prioritize_meter_schedules
)
from apply_manual_overrides import apply_manual_overrides_to_segments

# Constants
SFMTA_DOMAIN = "data.sfgov.org"
METER_SCHEDULES_DATASET_ID = "6cqg-dxku"

async def main():
    """Re-process meter schedules and update existing segments"""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")

    # Connect to MongoDB
    client = motor.motor_asyncio.AsyncIOMotorClient(
        mongodb_uri,
        serverSelectionTimeoutMS=60000,
        connectTimeoutMS=60000,
        socketTimeoutMS=60000
    )
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    # Test connection
    try:
        await db.command('ping')
        print("✓ Successfully connected to MongoDB")
    except Exception as e:
        print(f"ERROR: Failed to connect to MongoDB: {e}")
        client.close()
        return

    print("\n=== Re-processing Meter Schedules ===")
    
    # Step 1: Fetch meter schedules with schedule_type
    print("\nStep 1: Fetching meter schedules from Socrata...")
    socrata_client = Socrata(SFMTA_DOMAIN, app_token, timeout=60)
    schedules_results = socrata_client.get(METER_SCHEDULES_DATASET_ID, limit=200000)
    schedules_df = pd.DataFrame.from_records(schedules_results)
    print(f"✓ Fetched {len(schedules_df)} meter schedules")
    
    # Group by post_id
    schedules_by_post = {}
    for _, row in schedules_df.iterrows():
        post_id = row.get("post_id")
        if post_id:
            if post_id not in schedules_by_post:
                schedules_by_post[post_id] = []
            schedules_by_post[post_id].append({
                "beginTime": row.get("beg_time_dt"),
                "endTime": row.get("end_time_dt"),
                "rate": row.get("rate"),
                "rateQualifier": None,
                "rateUnit": "per hour",
                "schedule_type": row.get("schedule_type")  # NOW INCLUDED!
            })
    
    print(f"✓ Grouped schedules for {len(schedules_by_post)} unique post_ids")
    
    # Step 2: Load all segments from MongoDB
    print("\nStep 2: Loading segments from MongoDB...")
    segments = await db.street_segments.find({}).to_list(length=None)
    print(f"✓ Loaded {len(segments)} segments")
    
    # Step 3: Update meter schedules in segments
    print("\nStep 3: Updating meter schedules in segments...")
    updated_count = 0
    segments_with_tow = 0
    
    for segment in segments:
        meters = segment.get('meters', [])
        if not meters:
            continue
        
        segment_updated = False
        for meter in meters:
            post_id = meter.get('post_id')
            if post_id and post_id in schedules_by_post:
                # Update schedules with new data including schedule_type
                new_schedules = schedules_by_post[post_id]
                prioritized = prioritize_meter_schedules(new_schedules)
                meter['base_schedules'] = prioritized
                segment_updated = True
        
        if segment_updated:
            # Re-aggregate TOW schedules
            tow_agg = aggregate_blockface_tow_schedules(meters)
            segment["towScheduleAggregation"] = tow_agg
            
            if tow_agg['has_tow']:
                segments_with_tow += 1
            
            # Re-aggregate cap colors
            cap_agg = aggregate_blockface_cap_colors(meters)
            segment["capColorAggregation"] = cap_agg
            
            # Update flags
            segment["hasHomogeneousTow"] = tow_agg['all_have_tow']
            segment["hasHomogeneousCapColor"] = (cap_agg['majority_rule'] in ['ALL_ELIGIBLE', 'ALL_INELIGIBLE'])
            segment["blockfaceRestriction"] = cap_agg['restriction_type']
            segment["eligibleForStandardUser"] = cap_agg['eligible_for_curby_user']
            
            # Update in database
            await db.street_segments.update_one(
                {'_id': segment['_id']},
                {'$set': {
                    'meters': meters,
                    'towScheduleAggregation': segment.get('towScheduleAggregation'),
                    'capColorAggregation': segment.get('capColorAggregation'),
                    'hasHomogeneousTow': segment.get('hasHomogeneousTow'),
                    'hasHomogeneousCapColor': segment.get('hasHomogeneousCapColor'),
                    'blockfaceRestriction': segment.get('blockfaceRestriction'),
                    'eligibleForStandardUser': segment.get('eligibleForStandardUser')
                }}
            )
            updated_count += 1
    
    print(f"✓ Updated {updated_count} segments with new meter schedules")
    print(f"✓ Found {segments_with_tow} segments with TOW schedules")
    
    # Step 4: Re-apply manual overrides
    print("\nStep 4: Re-applying manual overrides...")
    override_stats = apply_manual_overrides_to_segments(segments)
    
    # Update segments with overrides in database
    for segment in segments:
        if any(r.get('source') == 'manual_override' for r in segment.get('rules', [])):
            await db.street_segments.update_one(
                {'_id': segment['_id']},
                {'$set': {'rules': segment['rules'], 'cardinalDirection': segment.get('cardinalDirection')}}
            )
    
    print(f"\n✓ Re-processing complete!")
    print(f"  - Segments updated: {updated_count}")
    print(f"  - Segments with TOW: {segments_with_tow}")
    print(f"  - Manual overrides applied: {override_stats['applied']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())