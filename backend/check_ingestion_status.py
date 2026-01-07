#!/usr/bin/env python3
"""
Quick status checker for ingestion progress
Run this in a separate terminal while ingestion is running
"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from datetime import datetime

async def check_status():
    load_dotenv()
    mongodb_uri = os.getenv('MONGODB_URI')
    
    if not mongodb_uri:
        print('ERROR: MONGODB_URI not found in .env')
        return
    
    client = motor.motor_asyncio.AsyncIOMotorClient(
        mongodb_uri,
        serverSelectionTimeoutMS=5000
    )
    
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print(f"\n{'='*60}")
    print(f"INGESTION STATUS CHECK - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        # Quick ping
        await db.command('ping')
        print("✓ MongoDB connected")
        
        # Count segments
        total = await db.street_segments.count_documents({})
        print(f"✓ Street segments: {total:,}")
        
        if total > 0:
            # Count with data
            with_meters = await db.street_segments.count_documents({
                'meters': {'$exists': True, '$ne': []}
            })
            with_rules = await db.street_segments.count_documents({
                'rules': {'$exists': True, '$ne': []}
            })
            with_sweeping = await db.street_segments.count_documents({
                'rules.type': 'street-sweeping'
            })
            
            print(f"  - With meters: {with_meters:,}")
            print(f"  - With rules: {with_rules:,}")
            print(f"  - With street sweeping: {with_sweeping:,}")
            
            # Progress estimate (target ~35,000)
            progress = (total / 35000) * 100
            print(f"\n  Progress: ~{progress:.1f}% (target: 35,000 segments)")
            
            if total >= 35000:
                print("\n  ✓ INGESTION APPEARS COMPLETE!")
        else:
            print("\n  ⏳ Ingestion in progress... (no segments yet)")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        client.close()
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(check_status())