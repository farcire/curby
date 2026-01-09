"""
Inspect SFMTA Street Sweeping Schedule Dataset (pu5n-qu5c)
Understand the data structure and how it relates to CNN segments
"""

from sodapy import Socrata
import os
from dotenv import load_dotenv
import json

load_dotenv()

def inspect_sweeping_schedule():
    """Fetch and analyze street sweeping schedule data"""
    
    client = Socrata('data.sfgov.org', os.getenv('SFMTA_APP_TOKEN'))
    
    # Get a sample of records
    print("Fetching sample records...")
    results = client.get('pu5n-qu5c', limit=10)
    
    print(f"\n{'='*80}")
    print(f"DATASET: Street Sweeping Schedule (pu5n-qu5c)")
    print(f"{'='*80}\n")
    
    print(f"Total records fetched: {len(results)}")
    print(f"\nColumns: {list(results[0].keys()) if results else 'No data'}\n")
    
    # Display sample records
    print(f"{'='*80}")
    print("SAMPLE RECORDS")
    print(f"{'='*80}\n")
    
    for i, record in enumerate(results[:5], 1):
        print(f"Record {i}:")
        for key, value in record.items():
            print(f"  {key:15s}: {value}")
        print()
    
    # Analyze CNN values
    print(f"{'='*80}")
    print("CNN ANALYSIS")
    print(f"{'='*80}\n")
    
    cnn_values = [r.get('cnn') for r in results if r.get('cnn')]
    print(f"Sample CNN values: {cnn_values[:10]}")
    print(f"CNN value types: {set(type(c).__name__ for c in cnn_values)}")
    
    # Check for specific streets we know about
    print(f"\n{'='*80}")
    print("SEARCHING FOR KNOWN STREETS")
    print(f"{'='*80}\n")
    
    # Search for King St (CNN 783420)
    king_st_results = client.get('pu5n-qu5c', 
                                  where="cnn='783420'",
                                  limit=5)
    print(f"King St (CNN 783420) records: {len(king_st_results)}")
    if king_st_results:
        print("Sample King St record:")
        print(json.dumps(king_st_results[0], indent=2))
    
    # Search for 20th St (CNN 868000)
    print(f"\n{'-'*80}\n")
    twentieth_st_results = client.get('pu5n-qu5c',
                                       where="cnn='868000'",
                                       limit=5)
    print(f"20th St (CNN 868000) records: {len(twentieth_st_results)}")
    if twentieth_st_results:
        print("Sample 20th St record:")
        print(json.dumps(twentieth_st_results[0], indent=2))
    
    # Get unique street names
    print(f"\n{'='*80}")
    print("UNIQUE STREETS SAMPLE")
    print(f"{'='*80}\n")
    
    unique_streets = client.get('pu5n-qu5c',
                                select="streetname",
                                group="streetname",
                                limit=20)
    print(f"Sample unique street names ({len(unique_streets)} shown):")
    for street in unique_streets:
        print(f"  - {street.get('streetname')}")
    
    # Check data completeness
    print(f"\n{'='*80}")
    print("DATA COMPLETENESS CHECK")
    print(f"{'='*80}\n")
    
    total_count = client.get('pu5n-qu5c', select="COUNT(*)")
    print(f"Total records in dataset: {total_count[0].get('COUNT_cnn', 'Unknown')}")
    
    # Check for null values
    for field in ['cnn', 'streetname', 'from_st', 'limits', 'theorder']:
        null_count = client.get('pu5n-qu5c',
                               where=f"{field} IS NULL",
                               select="COUNT(*)")
        count = null_count[0].get('COUNT_cnn', 0) if null_count else 0
        print(f"  {field:15s}: {count} null values")
    
    client.close()

if __name__ == "__main__":
    inspect_sweeping_schedule()