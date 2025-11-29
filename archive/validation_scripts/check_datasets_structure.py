import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

sys.stdout.reconfigure(line_buffering=True)
load_dotenv()

def check_structure():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    if not app_token:
        print("No token")
        return
        
    client = Socrata("data.sfgov.org", app_token)
    
    datasets = {
        "Active Streets": "3psu-pn9h",
        "Parking Meters": "8vzz-qzz9",
        "Metered Blockfaces": "mk27-a5x2"
    }
    
    for name, pid in datasets.items():
        print(f"\n--- Checking {name} ({pid}) ---")
        try:
            results = client.get(pid, limit=1)
            if results:
                rec = results[0]
                print(f"Columns: {list(rec.keys())}")
                if name == "Parking Meters":
                    print(f"street_seg_ctrln_id: {rec.get('street_seg_ctrln_id')}")
                if name == "Metered Blockfaces":
                    print(f"cnn: {rec.get('cnn')}")
            else:
                print("Empty result")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_structure()