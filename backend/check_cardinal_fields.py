"""
Check all database collections for fields that might contain cardinal directions
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import asyncio

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.curby

async def check_collections():
    """Check all collections for cardinal direction fields"""
    
    collections = await db.list_collection_names()
    print(f"Found {len(collections)} collections")
    print("=" * 80)
    
    for coll_name in collections:
        print(f"\n📁 Collection: {coll_name}")
        print("-" * 80)
        
        # Get a sample document
        sample = await db[coll_name].find_one()
        
        if sample:
            # Look for fields that might contain cardinal directions
            cardinal_fields = []
            
            def check_fields(obj, prefix=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        key_lower = key.lower()
                        
                        # Check if field name suggests cardinal direction
                        if any(term in key_lower for term in ['cardinal', 'direction', 'side', 'block']):
                            cardinal_fields.append({
                                'field': full_key,
                                'value': value,
                                'type': type(value).__name__
                            })
                        
                        # Recursively check nested objects
                        if isinstance(value, dict):
                            check_fields(value, full_key)
                        elif isinstance(value, list) and value and isinstance(value[0], dict):
                            check_fields(value[0], f"{full_key}[0]")
            
            check_fields(sample)
            
            if cardinal_fields:
                print(f"✅ Found {len(cardinal_fields)} potential cardinal direction fields:")
                for field_info in cardinal_fields:
                    print(f"   • {field_info['field']}: {field_info['value']} ({field_info['type']})")
            else:
                print("   No cardinal direction fields found")
        else:
            print("   (Empty collection)")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_collections())