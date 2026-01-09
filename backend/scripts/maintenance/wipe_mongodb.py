#!/usr/bin/env python3
"""
Wipe MongoDB Database

Completely clears all collections in the MongoDB database.
Use this before starting a fresh ingestion.
"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio

async def wipe_database():
    """Wipe all collections from MongoDB database."""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")
    
    # Create client
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
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
    
    # Get all collection names
    collections = await db.list_collection_names()
    
    if not collections:
        print("Database is already empty - no collections found")
        client.close()
        return
    
    print(f"\nFound {len(collections)} collections:")
    for coll in collections:
        print(f"  - {coll}")
    
    # Confirm deletion
    print("\n⚠️  WARNING: This will DELETE ALL DATA from the database!")
    response = input("Type 'YES' to confirm deletion: ")
    
    if response != "YES":
        print("Aborted - no data was deleted")
        client.close()
        return
    
    # Delete all collections
    print("\nDeleting collections...")
    for coll in collections:
        await db[coll].drop()
        print(f"  ✓ Deleted {coll}")
    
    print(f"\n✓ Successfully wiped {len(collections)} collections from database")
    client.close()

if __name__ == "__main__":
    asyncio.run(wipe_database())