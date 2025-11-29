import json
import random
import os

def generate_test_set():
    input_file = 'backend/database_backups/pre_cnn_migration_20251127_161321/parking_regulations.json'
    output_file = 'backend/test_set_regulations.json'

    if not os.path.exists(input_file):
        print(f"Error: Could not find {input_file}")
        # Try relative to current directory if running from root
        input_file = 'backend/database_backups/pre_cnn_migration_20251127_161321/parking_regulations.json' 
        if not os.path.exists(input_file):
             print("Could not find input file in standard locations.")
             return

    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print(f"Total records: {len(data)}")

    # Filter for unique texts to avoid duplicates
    seen_texts = set()
    unique_records = []
    
    for record in data:
        # Create a signature based on the main text fields
        reg = str(record.get('regulation', ''))
        details = str(record.get('regdetails', ''))
        # If details is 'nan' (from pandas export sometimes), treat as empty
        if details.lower() == 'nan': 
            details = ''
            
        text = f"{reg} {details}".strip()
        
        if text and text not in seen_texts:
            seen_texts.add(text)
            unique_records.append(record)

    print(f"Unique text records: {len(unique_records)}")

    # Heuristics for "challenging"
    # We want to find records that aren't just simple "Time limited" with standard hours
    challenging_keywords = [
        "except", "tow", "overnight", "oversized", "commercial", 
        "permit", "holiday", "school", "construction", "temporary",
        "dual", "zone", "between", "and", "stopped", "standing",
        "meter", "pay", "block", "wheels"
    ]

    challenging_records = []
    other_records = []

    for record in unique_records:
        reg = str(record.get('regulation', ''))
        details = str(record.get('regdetails', ''))
        if details.lower() == 'nan': details = ''
        
        full_text = (reg + " " + details).lower()
        is_challenging = False
        
        # Complexity heuristic 1: Long details
        if len(details) > 20:
            is_challenging = True
        
        # Complexity heuristic 2: Keywords
        if any(kw in full_text for kw in challenging_keywords):
            is_challenging = True
            
        # Complexity heuristic 3: Missing structured data but having text
        # If hours are missing but regulation implies time
        if (not record.get('hours') or str(record.get('hours')).lower() == 'nan') and 'time' in reg.lower():
             is_challenging = True

        if is_challenging:
            challenging_records.append(record)
        else:
            other_records.append(record)

    print(f"Identified {len(challenging_records)} potentially challenging records.")

    # Select 50 diverse records
    # 1. Sort by length of text (descending) to get the most verbose/complex ones first
    challenging_records.sort(key=lambda x: len(str(x.get('regdetails', ''))) + len(str(x.get('regulation', ''))), reverse=True)
    
    selected = []
    
    # Take top 20 most complex by length
    selected.extend(challenging_records[:20])
    
    # Take 20 random from the rest of 'challenging' to ensure variety, not just long ones
    remaining_challenging = challenging_records[20:]
    if len(remaining_challenging) >= 20:
        selected.extend(random.sample(remaining_challenging, 20))
    else:
        selected.extend(remaining_challenging)

    # Fill the rest with random 'other' records if we haven't reached 50
    # This ensures we also test simple/standard cases to make sure the LLM doesn't hallucinate complexity
    needed = 50 - len(selected)
    if needed > 0:
        if len(other_records) >= needed:
             selected.extend(random.sample(other_records, needed))
        else:
             selected.extend(other_records)

    # Format for the test set
    final_test_set = []
    for i, record in enumerate(selected):
        # Clean up NaN values for JSON output
        clean_record = {}
        for k, v in record.items():
            if isinstance(v, float) and str(v) == 'nan':
                clean_record[k] = None
            else:
                clean_record[k] = v
                
        final_test_set.append({
            "id": f"test_case_{i+1}",
            "original_data": clean_record,
            "regulation_text": f"{clean_record.get('regulation', '')} {clean_record.get('regdetails', '') or ''}".strip(),
            "expected_result": None # To be filled by human or golden reference later
        })

    with open(output_file, 'w') as f:
        json.dump(final_test_set, f, indent=2)
    
    print(f"Successfully created {output_file} with {len(final_test_set)} examples.")

if __name__ == "__main__":
    generate_test_set()