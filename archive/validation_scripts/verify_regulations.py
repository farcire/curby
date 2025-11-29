import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
import json
from datetime import datetime

# Force unbuffered stdout
sys.stdout.reconfigure(line_buffering=True)

print("Starting verification script...")

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    print(f"Loading .env from {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}")

def verify_regulations():
    print("Connecting to MongoDB...")
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        print("Error: MONGODB_URI not found in environment variables.")
        return

    try:
        print(f"Using URI: {mongo_uri.split('@')[-1] if '@' in mongo_uri else '***'}") # Safe print
        client = MongoClient(mongo_uri)
        try:
            db = client.get_default_database()
        except Exception:
            print("Default database not found in URI, using 'curby'")
            db = client["curby"]
        
        collection_name = "parking_regulations"
        collection = db[collection_name]
        
        # 1. Count documents
        count = collection.count_documents({})
        print(f"\n--- Verification for '{collection_name}' ---")
        print(f"Total Documents: {count}")
        
        # 2. Retrieve and print one sample document
        if count > 0:
            sample = collection.find_one()
            
            # Helper to handle datetime objects for JSON serialization
            def default_converter(o):
                if isinstance(o, datetime):
                    return o.isoformat()
                return str(o)

            print("\n--- Sample Document ---")
            print(json.dumps(sample, default=default_converter, indent=2))
            
            # 3. Specific check for geometry and regulation fields
            print("\n--- Field Check ---")
            print(f"Has 'geometry': {'geometry' in sample}")
            print(f"Has 'regulation': {'regulation' in sample}")
            
        else:
            print(f"Collection '{collection_name}' is empty.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    verify_regulations()