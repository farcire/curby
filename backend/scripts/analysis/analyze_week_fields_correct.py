 #!/usr/bin/env python3
"""
Corrected Week-of-Month Analysis for Street Cleaning

Based on screenshot, the actual fields are:
- Week1, Week2, Week3, Week4, Week5 (not week1ofmon)
- Values are 1/0 (not Y/N)
- FullName contains text like "Tue 1st, 3rd, 5th"
"""

import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd
import json
from collections import Counter

load_dotenv()

def fetch_sample_data(limit=10000):
    """Fetch sample of street cleaning data"""
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    print("Fetching sample data...")
    records = client.get("yhqp-riqs", limit=limit)
    df = pd.DataFrame.from_records(records)
    print(f"✓ Loaded {len(df)} records")
    return df

def analyze_week_fields(df):
    """Analyze the actual week fields"""
    print("\n" + "="*80)
    print("WEEK-OF-MONTH FIELD ANALYSIS")
    print("="*80)
    
    # Check for correct field names
    week_fields = ['week1', 'week2', 'week3', 'week4', 'week5']
    available = [f for f in week_fields if f in df.columns]
    
    print(f"\n📋 Week Fields Found: {available}")
    
    if not available:
        print("⚠️  No week fields found!")
        return
    
    # Analyze patterns
    week_patterns = Counter()
    fullname_patterns = Counter()
    
    records_with_weeks = 0
    records_all_weeks = 0
    
    for idx, row in df.iterrows():
        # Extract which weeks are active
        active_weeks = []
        for i, field in enumerate(week_fields, 1):
            if field in df.columns:
                value = str(row.get(field, '0'))
                if value == '1':
                    active_weeks.append(i)
        
        fullname = row.get('fullname', '')
        
        if active_weeks:
            records_with_weeks += 1
            pattern = tuple(active_weeks)
            week_patterns[pattern] += 1
            fullname_patterns[fullname] += 1
        else:
            records_all_weeks += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total records: {len(df)}")
    print(f"   Records with specific weeks: {records_with_weeks} ({records_with_weeks/len(df)*100:.1f}%)")
    print(f"   Records for all weeks: {records_all_weeks} ({records_all_weeks/len(df)*100:.1f}%)")
    
    print(f"\n📈 Top 10 Week Patterns:")
    for pattern, count in week_patterns.most_common(10):
        weeks_str = ", ".join([f"{w}{'st' if w==1 else 'nd' if w==2 else 'rd' if w==3 else 'th'}" for w in pattern])
        pct = (count / records_with_weeks) * 100 if records_with_weeks > 0 else 0
        print(f"   {weeks_str:20} {count:6} records ({pct:5.1f}%)")
    
    print(f"\n📝 Top 10 FullName Patterns:")
    for fullname, count in fullname_patterns.most_common(10):
        pct = (count / records_with_weeks) * 100 if records_with_weeks > 0 else 0
        print(f"   {fullname:30} {count:6} records ({pct:5.1f}%)")
    
    # Check holidays field
    if 'holidays' in df.columns:
        holidays_counts = df['holidays'].value_counts()
        print(f"\n🎄 Holidays Field:")
        for value, count in holidays_counts.items():
            pct = (count / len(df)) * 100
            print(f"   {value}: {count:6} records ({pct:5.1f}%)")
    
    return {
        'records_with_weeks': records_with_weeks,
        'records_all_weeks': records_all_weeks,
        'week_patterns': dict(week_patterns.most_common(20)),
        'fullname_patterns': dict(fullname_patterns.most_common(20))
    }

def main():
    print("\n" + "="*80)
    print("CORRECTED WEEK-OF-MONTH ANALYSIS")
    print("="*80)
    
    df = fetch_sample_data(limit=10000)
    
    # Show actual column names
    print(f"\n📋 All Columns in Dataset:")
    for col in sorted(df.columns):
        print(f"   - {col}")
    
    results = analyze_week_fields(df)
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    if results:
        pct_with_weeks = (results['records_with_weeks'] / (results['records_with_weeks'] + results['records_all_weeks'])) * 100
        
        print(f"\n✅ Week-of-month scheduling is used in {pct_with_weeks:.1f}% of records")
        print(f"\n💡 IMPLEMENTATION:")
        print(f"   • Field names: week1, week2, week3, week4, week5")
        print(f"   • Values: 1 = active, 0 = not active")
        print(f"   • FullName contains human-readable text (e.g., 'Tue 1st, 3rd, 5th')")
        print(f"   • Holidays field: 0 = no cleaning on holidays")
        print(f"\n📋 Display Logic:")
        print(f"   • If all week fields are 0: Display 'Thu 8am-10am' (every week)")
        print(f"   • If specific weeks: Display '1st & 3rd Thu 8am-10am'")
        print(f"   • If holidays = 0: Add 'except holidays' suffix")
        print(f"\n🎯 Use week1-5 binary fields (more reliable than parsing FullName)")
    
    # Save results
    with open('week_analysis_corrected.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📄 Results saved to: week_analysis_corrected.json")

if __name__ == "__main__":
    main()