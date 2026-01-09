"""
Python-based MongoDB Backup Script

Creates a JSON backup of the cnn_segments collection before running fixes.
This doesn't require mongodump to be installed.
"""

import os
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = "curby"
COLLECTION_NAME = "street_segments"

def backup_collection():
    """Backup the cnn_segments collection to JSON"""
    
    # Create backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"./database_backups/backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    print("=" * 80)
    print("DATABASE BACKUP")
    print("=" * 80)
    print(f"Backup location: {backup_dir}")
    print(f"Collection: {COLLECTION_NAME}")
    print()
    
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    try:
        # Count documents
        total_docs = collection.count_documents({})
        print(f"Total documents to backup: {total_docs:,}")
        
        if total_docs == 0:
            print("⚠ Warning: Collection is empty!")
            return
        
        # Export to JSON
        backup_file = os.path.join(backup_dir, f"{COLLECTION_NAME}.json")
        print(f"Exporting to: {backup_file}")
        print("This may take a few minutes...")
        
        # Stream documents to file
        with open(backup_file, 'w') as f:
            f.write('[\n')
            
            cursor = collection.find({})
            first = True
            count = 0
            
            for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                doc['_id'] = str(doc['_id'])
                
                if not first:
                    f.write(',\n')
                else:
                    first = False
                
                json.dump(doc, f, default=str)
                count += 1
                
                if count % 1000 == 0:
                    print(f"Backed up {count:,} documents...")
            
            f.write('\n]')
        
        # Get file size
        file_size = os.path.getsize(backup_file)
        size_mb = file_size / (1024 * 1024)
        
        print()
        print("=" * 80)
        print("BACKUP COMPLETE")
        print("=" * 80)
        print(f"Documents backed up: {count:,}")
        print(f"Backup file: {backup_file}")
        print(f"File size: {size_mb:.2f} MB")
        print()
        print("To restore from this backup, use:")
        print(f"  python restore_database.py {backup_file}")
        print()
        
    except Exception as e:
        print(f"❌ Error during backup: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    backup_collection()