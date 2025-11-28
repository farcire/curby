#!/bin/bash

echo "Waiting for ingestion to complete..."
echo "Monitoring ingestion_output.log..."

# Wait for the ingestion to finish by checking if the process is still running
while pgrep -f "ingest_data.py" > /dev/null; do
    sleep 5
    echo -n "."
done

echo ""
echo "Ingestion completed! Checking results..."
echo ""

# Show last 30 lines of the log
echo "=== INGESTION LOG (last 30 lines) ==="
tail -30 ingestion_output.log
echo ""

# Run verification
echo "=== RUNNING VERIFICATION ==="
source ../.venv/bin/activate
python quick_check.py

echo ""
echo "=== CHECKING FOR 20TH STREET ==="
python3 << 'EOF'
import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio

async def check_20th():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = client.get_default_database() if hasattr(client, 'get_default_database') else client['curby']
    
    count = await db.blockfaces.count_documents({"streetName": {"$regex": "20TH", "$options": "i"}})
    print(f"20th Street blockfaces found: {count}")
    
    if count > 0:
        blockfaces = await db.blockfaces.find({"streetName": {"$regex": "20TH", "$options": "i"}}).to_list(None)
        for bf in blockfaces:
            rules = bf.get('rules', [])
            reg_rules = [r for r in rules if r.get('type') == 'parking-regulation']
            print(f"\n{bf.get('streetName')} - Side: {bf.get('side')}")
            print(f"  Total rules: {len(rules)}")
            print(f"  Parking regulations: {len(reg_rules)}")
            if reg_rules:
                print("  ✅ HAS PARKING REGULATIONS!")
    
    client.close()

asyncio.run(check_20th())
EOF

cat test_results.txt