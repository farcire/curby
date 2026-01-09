"""
Python-based MongoDB Restore Script

Restores the cnn_segments collection from a JSON backup.
"""

import os
import json
import sys
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = "curby"
COLLECTION_NAME = "street_segments"


def restore_collection(backup_file):
    """Restore the cnn_segments collection from JSON backup"""
    
    if not os.path.exists(backup_file):
        print(f"❌ Error: Backup file not found: {backup_file}")
        return
    
    print("=" * 80)
    print("DATABASE RESTORE")
    print("=" * 80)
    print(f"Restoring from: {backup_file}")
    print()
    
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    try:
        # Load backup data
        print("Loading backup file...")
        with open(backup_file, 'r') as f:
            documents = json.load(f)
        
        print(f"Found {len(documents):,} documents in backup")
        
        # Confirm before dropping
        print()
        print("⚠️  WARNING: This will DROP the existing collection and restore from backup!")
        response = input("Type 'yes' to continue: ")
        
        if response.lower() != 'yes':
            print("Restore cancelled.")
            return
        
        # Drop existing collection
        print("\nDropping existing collection...")
        collection.drop()
        
        # Restore documents
        print("Restoring documents...")
        
        # Convert _id strings back to ObjectId
        for doc in documents:
            if '_id' in doc and isinstance(doc['_id'], str):
                try:
                    doc['_id'] = ObjectId(doc['_id'])
                except:
                    # If conversion fails, let MongoDB generate new ID
                    del doc['_id']
        
        # Insert in batches
        batch_size = 1000
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            collection.insert_many(batch)
            print(f"Restored {min(i + batch_size, len(documents)):,} / {len(documents):,} documents...")
        
        # Verify
        restored_count = collection.count_documents({})
        
        print()
        print("=" * 80)
        print("RESTORE COMPLETE")
        print("=" * 80)
        print(f"Documents restored: {restored_count:,}")
        print()
        
    except Exception as e:
        print(f"❌ Error during restore: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python restore_database.py <backup_file.json>")
        print("\nExample:")
        print("  python restore_database.py ./database_backups/backup_20251205_022617/cnn_segments.json")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    restore_collection(backup_file)