#!/usr/bin/env python3
"""
Automated Meter Policies Ingestion

Runs every 3 days to keep meter policies current.
Filters for active policies only (startdate <= TODAY <= enddate).

Current Status (Dec 2024): All policies are future-dated (start: 2026-01-12)
so this will return 0 active policies until January 2026.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sodapy import Socrata
from pymongo import MongoClient, ASCENDING
import logging

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('meter_policies_ingestion.log'),
        logging.StreamHandler()
    ]
)

SFMTA_DOMAIN = "data.sfgov.org"
METER_POLICIES_ID = "qq7v-hds4"

def ingest_meter_policies():
    """Fetch and store active meter policies in MongoDB"""
    
    logging.info("="*80)
    logging.info("METER POLICIES INGESTION STARTED")
    logging.info("="*80)
    
    # Connect to SFMTA
    sfmta_token = os.getenv("SFMTA_APP_TOKEN")
    if not sfmta_token:
        logging.error("SFMTA_APP_TOKEN not found in environment")
        sys.exit(1)
    
    client = Socrata(SFMTA_DOMAIN, sfmta_token)
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    mongo_client = MongoClient(mongo_uri)
    db = mongo_client.curby
    
    try:
        # Fetch all meter policies
        logging.info("Fetching Meter Policies from SFMTA...")
        policies = client.get(METER_POLICIES_ID, limit=100000)
        logging.info(f"✓ Fetched {len(policies)} total policy records")
        
        # Filter for active policies only
        today = datetime.now().date()
        active_policies = []
        future_policies = []
        expired_policies = []
        
        for policy in policies:
            try:
                # Parse dates
                start_date = datetime.strptime(
                    policy['startdate'], 
                    '%Y-%m-%dT%H:%M:%S.%f'
                ).date()
                end_date = datetime.strptime(
                    policy['enddate'], 
                    '%Y-%m-%dT%H:%M:%S.%f'
                ).date()
                
                # Classify by temporal status
                if start_date <= today <= end_date:
                    # Active policy
                    policy['_ingested_at'] = datetime.now()
                    policy['_is_active'] = True
                    policy['_temporal_status'] = 'active'
                    active_policies.append(policy)
                elif start_date > today:
                    # Future policy
                    future_policies.append(policy)
                else:
                    # Expired policy
                    expired_policies.append(policy)
                    
            except (KeyError, ValueError) as e:
                logging.warning(f"Skipping policy due to date error: {e}")
                continue
        
        logging.info(f"✓ Temporal classification complete:")
        logging.info(f"  - Active policies: {len(active_policies)}")
        logging.info(f"  - Future policies: {len(future_policies)}")
        logging.info(f"  - Expired policies: {len(expired_policies)}")
        
        # Clear existing collection and insert new data
        db.meter_policies.delete_many({})
        
        if active_policies:
            db.meter_policies.insert_many(active_policies)
            logging.info(f"✓ Inserted {len(active_policies)} active policies into MongoDB")
            
            # Create indexes for fast querying
            db.meter_policies.create_index([("postid", ASCENDING)])
            db.meter_policies.create_index([("parkingspaceid", ASCENDING)])
            db.meter_policies.create_index([("_temporal_status", ASCENDING)])
            logging.info("✓ Created indexes on postid, parkingspaceid, and temporal_status")
        else:
            logging.info("ℹ No active policies found (all may be future-dated)")
            if len(future_policies) > 0:
                logging.info(f"  Note: {len(future_policies)} future policies exist")
                # Show when they will activate
                if future_policies:
                    sample = future_policies[0]
                    start_date = datetime.strptime(
                        sample['startdate'], 
                        '%Y-%m-%dT%H:%M:%S.%f'
                    ).date()
                    logging.info(f"  Future policies will activate on: {start_date}")
        
        # Store metadata about this ingestion
        db.ingestion_metadata.update_one(
            {"dataset": "meter_policies"},
            {
                "$set": {
                    "last_ingestion": datetime.now(),
                    "total_policies": len(policies),
                    "active_policies": len(active_policies),
                    "future_policies": len(future_policies),
                    "expired_policies": len(expired_policies),
                    "next_scheduled": datetime.now() + timedelta(days=3)
                }
            },
            upsert=True
        )
        
        logging.info("="*80)
        logging.info("METER POLICIES INGESTION COMPLETED SUCCESSFULLY")
        logging.info("="*80)
        
        return {
            "success": True,
            "total": len(policies),
            "active": len(active_policies),
            "future": len(future_policies),
            "expired": len(expired_policies)
        }
        
    except Exception as e:
        logging.error(f"ERROR during ingestion: {e}")
        raise
    finally:
        client.close()
        mongo_client.close()

if __name__ == "__main__":
    try:
        result = ingest_meter_policies()
        logging.info(f"Ingestion result: {result}")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)