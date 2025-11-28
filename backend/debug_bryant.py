import os
import asyncio
from dotenv import load_dotenv
from sodapy import Socrata
import motor.motor_asyncio

async def debug():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    # 1. Find CNN for Bryant St near 18th/Mariposa
    # We'll fetch Bryant St records and look for block numbers or cross streets if available,
    # or just list a few to pick one.
    print("--- Fetching Bryant St Segments ---")
    results = client.get("3psu-pn9h", where="streetname='Bryant St' AND zip_code='94110'", limit=20)
    
    target_cnn = None
    for row in results:
        print(f"CNN: {row.get('cnn')}, From: {row.get('f_st')}, To: {row.get('t_st')}")
        if row.get('f_st') == '18th St' or row.get('t_st') == '18th St':
            target_cnn = row.get('cnn')
            
    if not target_cnn:
        print("Could not pinpoint exact segment, using first one found.")
        if results:
            target_cnn = results[0].get('cnn')
    
    if target_cnn:
        print(f"\n--- Investigating CNN {target_cnn} ---")
        
        # 2. Check pep9 for this CNN
        pep9_results = client.get("pep9-66vw", where=f"cnn_id='{target_cnn}'")
        print(f"Found {len(pep9_results)} records in pep9-66vw for CNN {target_cnn}")
        for r in pep9_results:
            print(f"  - ID: {r.get('globalid')}, Shape Len: {r.get('shape_leng')}")
            
        # 3. Check MongoDB for this CNN
        mongodb_uri = os.getenv("MONGODB_URI")
        mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
        db = mongo_client.get_default_database() or mongo_client["curby"]
        
        db_results = await db.blockfaces.find({"cnn": target_cnn}).to_list(length=100)
        print(f"\nFound {len(db_results)} blockfaces in MongoDB for CNN {target_cnn}")
        for doc in db_results:
            print(f"  - Side: {doc.get('side')}, Rules: {len(doc.get('rules', []))}, ID: {doc.get('id')}")
            
        mongo_client.close()

if __name__ == "__main__":
    asyncio.run(debug())