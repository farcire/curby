#!/usr/bin/env python3
"""
Week-of-Month Pattern Analysis for Street Cleaning

Analyzes whether FullName/description fields contain week-of-month information
that can be extracted, or if we must rely on week1-5 fields.

Answers: Can we parse "2nd Thursday" from text, or do we need the binary week fields?
"""

import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd
import json
import re
from collections import Counter

load_dotenv()

STREET_CLEANING_ID = "yhqp-riqs"

def fetch_sample_data(limit=5000):
    """Fetch sample of street cleaning data"""
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    print("Fetching sample data...")
    records = client.get(STREET_CLEANING_ID, limit=limit)
    return pd.DataFrame.from_records(records)

def extract_week_from_text(text):
    """
    Try to extract week-of-month from text.
    Returns: list of week numbers [1-5] or None
    """
    if not text or not isinstance(text, str):
        return None
    
    text_lower = text.lower()
    
    # Patterns to match
    patterns = {
        1: [r'\b1st\b', r'\bfirst\b', r'\b1\s*st\b'],
        2: [r'\b2nd\b', r'\bsecond\b', r'\b2\s*nd\b'],
        3: [r'\b3rd\b', r'\bthird\b', r'\b3\s*rd\b'],
        4: [r'\b4th\b', r'\bfourth\b', r'\b4\s*th\b'],
        5: [r'\b5th\b', r'\bfifth\b', r'\b5\s*th\b']
    }
    
    found_weeks = []
    for week_num, week_patterns in patterns.items():
        for pattern in week_patterns:
            if re.search(pattern, text_lower):
                found_weeks.append(week_num)
                break
    
    return found_weeks if found_weeks else None

def analyze_week_fields_vs_text(df):
    """
    Compare week1-5 binary fields with text field content.
    Determine if text parsing is sufficient or if we need binary fields.
    """
    print("\n" + "="*80)
    print("WEEK-OF-MONTH ANALYSIS: Text vs Binary Fields")
    print("="*80)
    
    # Check which fields exist
    week_binary_fields = [f'week{i}ofmon' for i in range(1, 6)]
    text_fields = ['fullname', 'corridor', 'streetname', 'limits']
    
    available_week_fields = [f for f in week_binary_fields if f in df.columns]
    available_text_fields = [f for f in text_fields if f in df.columns]
    
    print(f"\n📋 Available Fields:")
    print(f"   Week binary fields: {available_week_fields}")
    print(f"   Text fields: {available_text_fields}")
    
    if not available_week_fields:
        print("\n⚠️  No week1-5 fields found in dataset!")
        print("   Must rely on text parsing or assume all weeks.")
        return None
    
    # Analyze records with week-of-month scheduling
    results = {
        'total_records': len(df),
        'records_with_week_scheduling': 0,
        'text_parsing_successful': 0,
        'text_parsing_failed': 0,
        'week_patterns': Counter(),
        'examples': {
            'text_match': [],
            'text_mismatch': [],
            'no_text_info': []
        }
    }
    
    for idx, row in df.iterrows():
        # Extract week info from binary fields
        weeks_from_binary = []
        for i in range(1, 6):
            field = f'week{i}ofmon'
            if field in df.columns:
                value = str(row.get(field, '')).upper()
                if value in ['Y', '1', 'TRUE']:
                    weeks_from_binary.append(i)
        
        # If no specific weeks, it's all weeks (skip analysis)
        if not weeks_from_binary:
            continue
        
        results['records_with_week_scheduling'] += 1
        
        # Track pattern
        pattern = tuple(sorted(weeks_from_binary))
        results['week_patterns'][pattern] += 1
        
        # Try to extract from text fields
        weeks_from_text = None
        text_source = None
        
        for text_field in available_text_fields:
            text_value = row.get(text_field)
            if text_value:
                extracted = extract_week_from_text(text_value)
                if extracted:
                    weeks_from_text = extracted
                    text_source = text_field
                    break
        
        # Compare binary vs text
        if weeks_from_text:
            if set(weeks_from_text) == set(weeks_from_binary):
                results['text_parsing_successful'] += 1
                if len(results['examples']['text_match']) < 5:
                    results['examples']['text_match'].append({
                        'text': row.get(text_source),
                        'weeks_binary': weeks_from_binary,
                        'weeks_text': weeks_from_text,
                        'weekday': row.get('weekday')
                    })
            else:
                results['text_parsing_failed'] += 1
                if len(results['examples']['text_mismatch']) < 5:
                    results['examples']['text_mismatch'].append({
                        'text': row.get(text_source) if text_source else 'N/A',
                        'weeks_binary': weeks_from_binary,
                        'weeks_text': weeks_from_text,
                        'weekday': row.get('weekday')
                    })
        else:
            # No text info found
            if len(results['examples']['no_text_info']) < 5:
                text_samples = {field: row.get(field) for field in available_text_fields}
                results['examples']['no_text_info'].append({
                    'text_fields': text_samples,
                    'weeks_binary': weeks_from_binary,
                    'weekday': row.get('weekday')
                })
    
    # Print results
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"   Total records analyzed: {results['total_records']}")
    print(f"   Records with week-of-month scheduling: {results['records_with_week_scheduling']}")
    
    if results['records_with_week_scheduling'] > 0:
        success_rate = (results['text_parsing_successful'] / results['records_with_week_scheduling']) * 100
        print(f"\n   Text parsing SUCCESS: {results['text_parsing_successful']} ({success_rate:.1f}%)")
        print(f"   Text parsing FAILED: {results['text_parsing_failed']}")
        print(f"   No text info available: {len(results['examples']['no_text_info'])}")
        
        print(f"\n📈 Week-of-Month Patterns:")
        for pattern, count in results['week_patterns'].most_common(10):
            weeks_str = ", ".join([f"{w}{'st' if w==1 else 'nd' if w==2 else 'rd' if w==3 else 'th'}" for w in pattern])
            print(f"      {weeks_str} week(s): {count} records")
    
    # Show examples
    if results['examples']['text_match']:
        print(f"\n✅ Examples where text parsing MATCHED binary fields:")
        for i, ex in enumerate(results['examples']['text_match'], 1):
            print(f"   {i}. Text: '{ex['text']}'")
            print(f"      Binary weeks: {ex['weeks_binary']}, Parsed weeks: {ex['weeks_text']}")
            print(f"      Day: {ex['weekday']}")
    
    if results['examples']['text_mismatch']:
        print(f"\n❌ Examples where text parsing MISMATCHED binary fields:")
        for i, ex in enumerate(results['examples']['text_mismatch'], 1):
            print(f"   {i}. Text: '{ex['text']}'")
            print(f"      Binary weeks: {ex['weeks_binary']}, Parsed weeks: {ex['weeks_text']}")
            print(f"      Day: {ex['weekday']}")
    
    if results['examples']['no_text_info']:
        print(f"\n⚠️  Examples where NO text info was found:")
        for i, ex in enumerate(results['examples']['no_text_info'], 1):
            print(f"   {i}. Binary weeks: {ex['weeks_binary']}, Day: {ex['weekday']}")
            print(f"      Text fields: {ex['text_fields']}")
    
    return results

def generate_recommendation(results):
    """Generate recommendation based on analysis"""
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    if not results:
        print("\n⚠️  Cannot analyze - week fields not found in dataset")
        print("\n📋 RECOMMENDATION:")
        print("   • Assume ALL weeks for street cleaning schedules")
        print("   • Display as: 'Street Cleaning Thu 8am-10am'")
        print("   • No week-of-month specificity available")
        return
    
    total_week_scheduled = results['records_with_week_scheduling']
    text_success = results['text_parsing_successful']
    
    if total_week_scheduled == 0:
        print("\n✅ All street cleaning occurs EVERY week")
        print("\n📋 RECOMMENDATION:")
        print("   • No week-of-month logic needed")
        print("   • Display as: 'Street Cleaning Thu 8am-10am'")
    else:
        success_rate = (text_success / total_week_scheduled) * 100 if total_week_scheduled > 0 else 0
        
        print(f"\n📊 Text Parsing Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 95:
            print("\n✅ Text parsing is HIGHLY RELIABLE")
            print("\n📋 RECOMMENDATION:")
            print("   • Use text parsing to extract week-of-month")
            print("   • Fallback to week1-5 binary fields if parsing fails")
            print("   • Display as: 'Street Cleaning 2nd Thu 8am-10am'")
        elif success_rate >= 70:
            print("\n⚠️  Text parsing is MODERATELY RELIABLE")
            print("\n📋 RECOMMENDATION:")
            print("   • Prefer week1-5 binary fields (more accurate)")
            print("   • Use text parsing only as validation/fallback")
            print("   • Display as: 'Street Cleaning 2nd Thu 8am-10am'")
        else:
            print("\n❌ Text parsing is UNRELIABLE")
            print("\n📋 RECOMMENDATION:")
            print("   • MUST use week1-5 binary fields")
            print("   • Text fields do not contain sufficient week-of-month info")
            print("   • Display as: 'Street Cleaning 2nd Thu 8am-10am'")
        
        print(f"\n💡 IMPLEMENTATION:")
        print(f"   • Extract weeks from week1-5 fields (Y/1 = active)")
        print(f"   • If all weeks empty/N, assume every week")
        print(f"   • Format display: '2nd & 4th Thu' for multiple weeks")
        print(f"   • Format display: 'Thu' for all weeks")

def main():
    """Main analysis"""
    print("\n" + "="*80)
    print("WEEK-OF-MONTH PATTERN ANALYSIS")
    print("="*80)
    print("Question: Can we parse week-of-month from text, or need binary fields?")
    print("="*80)
    
    # Fetch data
    df = fetch_sample_data(limit=10000)
    print(f"✓ Loaded {len(df)} records for analysis")
    
    # Analyze
    results = analyze_week_fields_vs_text(df)
    
    # Generate recommendation
    generate_recommendation(results)
    
    # Save results
    if results:
        with open('week_of_month_analysis.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Detailed results saved to: week_of_month_analysis.json")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()