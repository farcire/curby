"""
Check what fields are available in the meter schedules dataset
"""
import os
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METER_SCHEDULES_DATASET_ID = "6cqg-dxku"
app_token = os.getenv("SFMTA_APP_TOKEN")

print("Fetching meter schedules dataset...")
client = Socrata(SFMTA_DOMAIN, app_token, timeout=60)
results = client.get(METER_SCHEDULES_DATASET_ID, limit=10)
df = pd.DataFrame.from_records(results)

print(f"\n✓ Fetched {len(df)} sample records")
print(f"\nAvailable fields ({len(df.columns)}):")
print("=" * 80)
for col in sorted(df.columns):
    print(f"  - {col}")

print("\n" + "=" * 80)
print("Sample record (first row):")
print("=" * 80)
if len(df) > 0:
    first_row = df.iloc[0]
    for col in sorted(df.columns):
        value = first_row[col]
        print(f"  {col}: {value}")

print("\n" + "=" * 80)
print("Sample records with different schedule types:")
print("=" * 80)
if 'schedule_type' in df.columns:
    for schedule_type in df['schedule_type'].unique():
        print(f"\n{schedule_type}:")
        sample = df[df['schedule_type'] == schedule_type].iloc[0]
        print(f"  post_id: {sample.get('post_id')}")
        print(f"  beg_time_dt: {sample.get('beg_time_dt')}")
        print(f"  end_time_dt: {sample.get('end_time_dt')}")
        print(f"  rate: {sample.get('rate')}")
        # Check for day/time fields
        for field in ['days_applied', 'from_time', 'to_time', 'weekday', 'day_of_week']:
            if field in df.columns:
                print(f"  {field}: {sample.get(field)}")