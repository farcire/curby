import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import motor.motor_asyncio
from pathlib import Path

async def backup_database():
    """Backup current database before CNN migration"""
    load_dotenv()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path("./database_backups")
    backup_path = backup_dir / f"pre_cnn_migration_{timestamp}"
    backup_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Database Backup Before CNN Migration")
    print("=" * 60)
    print(f"\nBackup location: {backup_path}\n")
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("❌ MONGODB_URI not found in .env file")
        return False
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except:
        db = client["curby"]
    
    # Get all collections
    collections = await db.list_collection_names()
    
    print(f"Found {len(collections)} collections to backup:\n")
    
    total_docs = 0
    collection_info = {}
    
    for collection_name in collections:
        collection = db[collection_name]
        count = await collection.count_documents({})
        total_docs += count
        collection_info[collection_name] = count
        print(f"  {collection_name}: {count} documents")
        
        # Export collection to JSON
        cursor = collection.find({})
        docs = await cursor.to_list(None)
        
        # Convert ObjectId to string for JSON serialization
        for doc in docs:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        # Save to file
        output_file = backup_path / f"{collection_name}.json"
        with open(output_file, 'w') as f:
            json.dump(docs, f, indent=2, default=str)
    
    # Save backup metadata
    metadata = {
        "timestamp": timestamp,
        "mongodb_uri_host": mongodb_uri.split('@')[-1] if '@' in mongodb_uri else "local",
        "total_collections": len(collections),
        "total_documents": total_docs,
        "collections": collection_info,
        "purpose": "Pre CNN-segment migration",
        "current_system": "Blockface-based (7.4% coverage)",
        "next_step": "Migrate to CNN-segment architecture",
        "backup_format": "JSON per collection"
    }
    
    with open(backup_path / "backup_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Backup completed successfully!")
    print(f"{'='*60}")
    print(f"\nTotal documents backed up: {total_docs}")
    print(f"Backup saved to: {backup_path}")
    print(f"\nTo restore this backup if needed:")
    print(f"  python restore_database.py {backup_path}")
    print(f"\n{'='*60}")
    print("Ready to proceed with CNN segment migration")
    print(f"{'='*60}\n")
    
    client.close()
    return True

if __name__ == "__main__":
    success = asyncio.run(backup_database())
    exit(0 if success else 1)