"""
Find fields containing cardinal direction values (N, S, E, W, etc.)
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import asyncio

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.curby

# Cardinal direction patterns to look for
CARDINAL_PATTERNS = ['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW', 
                     'NORTH', 'SOUTH', 'EAST', 'WEST',
                     'NORTHEAST', 'NORTHWEST', 'SOUTHEAST', 'SOUTHWEST']

async def find_cardinals():
    """Find fields with cardinal direction values"""
    
    # Focus on street_segments collection
    print("Checking street_segments collection for cardinal directions...")
    print("=" * 80)
    
    # Get a few sample documents
    cursor = db.street_segments.find().limit(10)
    docs = await cursor.to_list(length=10)
    
    print(f"Examining {len(docs)} sample documents\n")
    
    for idx, doc in enumerate(docs, 1):
        print(f"\n📄 Document {idx}: CNN {doc.get('cnn')}, Street: {doc.get('streetName')}, Side: {doc.get('side')}")
        print("-" * 80)
        
        # Check all fields recursively
        def check_value(obj, path=""):
            findings = []
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check if value is a cardinal direction
                    if isinstance(value, str):
                        value_upper = value.strip().upper()
                        if value_upper in CARDINAL_PATTERNS:
                            findings.append(f"   ✅ {current_path} = '{value}'")
                    
                    # Recurse
                    if isinstance(value, dict):
                        findings.extend(check_value(value, current_path))
                    elif isinstance(value, list):
                        for i, item in enumerate(value[:3]):  # Check first 3 items
                            if isinstance(item, dict):
                                findings.extend(check_value(item, f"{current_path}[{i}]"))
            return findings
        
        findings = check_value(doc)
        if findings:
            for finding in findings:
                print(finding)
        else:
            print("   No cardinal directions found")
        
        # Also print the rules structure to see what's there
        rules = doc.get('rules', [])
        if rules:
            print(f"\n   Rules structure (first rule):")
            if rules:
                first_rule = rules[0]
                for key, value in first_rule.items():
                    print(f"      {key}: {value}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(find_cardinals())