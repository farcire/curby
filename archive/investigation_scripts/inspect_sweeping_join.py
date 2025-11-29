import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

def inspect_join():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    # 1. Fetch a few Active Streets (3psu-pn9h)
    print("Fetching Active Streets...")
    streets_results = client.get("3psu-pn9h", limit=5)
    streets_df = pd.DataFrame.from_records(streets_results)
    
    if streets_df.empty:
        print("No streets found.")
        return

    print("\n--- Active Streets Sample (CNNs) ---")
    print(streets_df[['cnn', 'streetname', 'lf_fadd', 'rt_fadd']].head())
    
    # Pick a CNN to query sweeping for
    sample_cnn = streets_df.iloc[0]['cnn']
    print(f"\nQuerying Street Cleaning for CNN: {sample_cnn}")
    
    # 2. Fetch Street Cleaning for that CNN (yhqp-riqs)
    sweeping_results = client.get("yhqp-riqs", cnn=sample_cnn)
    
    if sweeping_results:
        sweeping_df = pd.DataFrame.from_records(sweeping_results)
        print(f"\n--- Street Cleaning for CNN {sample_cnn} ---")
        print(sweeping_df[['cnn', 'fullname', 'weekday', 'fromhour', 'tohour', 'cnnrightleft', 'blockside']].head())
    else:
        print(f"No sweeping schedules found for CNN {sample_cnn}")
        
    # 3. General inspection of Sweeping Columns
    print("\n--- All Street Cleaning Columns ---")
    # Fetch one record just to get columns if previous query failed
    if not sweeping_results:
        one_result = client.get("yhqp-riqs", limit=1)
        if one_result:
            print(pd.DataFrame.from_records(one_result).columns.tolist())

if __name__ == "__main__":
    inspect_join()