import json

file_path = 'backend/database_backups/pre_cnn_migration_20251127_161321/parking_regulations.json'

try:
    with open(file_path, 'r') as f:
        data = json.load(f)
        total_records = len(data)
        
        # Count unique regulation texts (regulation + details)
        # This represents the actual number of LLM calls needed with caching
        unique_regulations = set()
        for record in data:
            reg_text = str(record.get('regulation', ''))
            reg_details = str(record.get('regdetails', ''))
            
            # Normalize: generic cleanup to ensure we don't count "Time Limit" and "Time Limit " as two different things
            full_text = f"{reg_text} {reg_details}".strip()
            
            if full_text:
                unique_regulations.add(full_text)
                
        print(f"Total Raw Records: {total_records}")
        print(f"Unique Regulation Patterns (LLM Calls needed): {len(unique_regulations)}")
        print(f"Reduction Ratio: {total_records / len(unique_regulations):.1f}x")
except Exception as e:
    print(f"Error reading file: {e}")