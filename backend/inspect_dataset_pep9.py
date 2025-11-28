import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

def inspect_dataset():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    # Unknown dataset from user feedback
    dataset_id = "pep9-66vw"
    
    print("--- Investigating Mariposa St ---")
    
    # Check the other dataset ID mentioned in the link
    dataset_link_id = "4qnp-gcxs" # Map of Blockfaces
    
    print("--- Searching for ANY duplicate CNNs in pep9-66vw to confirm sides exist ---")
    try:
        # Fetch a larger batch
        results = client.get(dataset_id, limit=5000)
        if results:
            df = pd.DataFrame.from_records(results)
            
            if 'cnn_id' in df.columns:
                # Filter out NULL/empty CNNs
                df_clean = df[df['cnn_id'].notna() & (df['cnn_id'] != 'NULL') & (df['cnn_id'] != '')]
                
                counts = df_clean['cnn_id'].value_counts()
                duplicates = counts[counts > 1]
                
                print(f"Found {len(duplicates)} valid CNNs with multiple records.")
                
                if not duplicates.empty:
                    # Get the top 3 duplicated CNNs
                    top_dups = duplicates.head(3).index.tolist()
                    
                    for cnn in top_dups:
                        print(f"\n--- Duplicate CNN: {cnn} ---")
                        # Show columns that might indicate side
                        cols = ['cnn_id', 'street_nam', 'blockface_', 'cnnrightleft', 'side', 'shape']
                        present_cols = [c for c in cols if c in df_clean.columns]
                        print(df_clean[df_clean['cnn_id'] == cnn][present_cols].to_string())
                else:
                    print("No valid duplicates found in sample.")
            else:
                print("'cnn_id' column not found.")
        else:
            print("No results.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_dataset()