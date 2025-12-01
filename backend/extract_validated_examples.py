"""
Extract examples from the 227 validated golden dataset entries
"""
import pandas as pd
import json

def extract_examples():
    df = pd.read_csv('golden_dataset_partial.csv')
    
    # Filter to completed entries (those validated by validate_golden_dataset.py)
    completed = df[df['golden_action'] != 'No data'].copy()
    
    # Further filter to entries that would pass validation
    # (have golden_summary filled and are not just "No data")
    validated = completed[
        (completed['golden_summary'].notna()) &
        (completed['golden_summary'] != '') &
        (completed['golden_summary'] != 'No data')
    ].copy()
    
    print(f"Total validated entries: {len(validated)}")
    print(f"\nAction distribution:")
    print(validated['golden_action'].value_counts())
    
    # Select 10-12 diverse examples
    examples = []
    
    # Get examples for each action type
    for action in ['Time-limited', 'Prohibited', 'Permit-required', 'Restricted']:
        action_examples = validated[validated['golden_action'] == action]
        
        if action == 'Time-limited':
            # Get variety: simple, with RPP, daily (M-Su)
            simple = action_examples[
                (action_examples['rpparea1'].isna() | (action_examples['rpparea1'] == '')) &
                (action_examples['days'].notna()) &
                (action_examples['days'] != 'M-Su')
            ].head(2)
            
            with_rpp = action_examples[
                (action_examples['rpparea1'].notna()) &
                (action_examples['rpparea1'] != '') &
                (action_examples['days'] != 'M-Su')
            ].head(2)
            
            daily = action_examples[
                action_examples['days'] == 'M-Su'
            ].head(2)
            
            examples.extend(simple.to_dict('records'))
            examples.extend(with_rpp.to_dict('records'))
            examples.extend(daily.to_dict('records'))
        else:
            # Get 2 examples for other actions
            examples.extend(action_examples.head(2).to_dict('records'))
    
    # Clean up and format
    formatted_examples = []
    for ex in examples:
        formatted_examples.append({
            'regulation': str(ex['regulation']) if pd.notna(ex['regulation']) else '',
            'days': str(ex['days']) if pd.notna(ex['days']) else '',
            'hours': str(ex['hours']) if pd.notna(ex['hours']) else '',
            'hrs_begin': str(ex['hrs_begin']) if pd.notna(ex['hrs_begin']) else '',
            'hrs_end': str(ex['hrs_end']) if pd.notna(ex['hrs_end']) else '',
            'rpparea1': str(ex['rpparea1']) if pd.notna(ex['rpparea1']) else '',
            'hrlimit': str(ex['hrlimit']) if pd.notna(ex['hrlimit']) else '',
            'golden_action': ex['golden_action'],
            'golden_summary': ex['golden_summary'],
            'golden_severity': ex['golden_severity']
        })
    
    # Save
    output = {
        'total_validated': len(validated),
        'total_examples': len(formatted_examples),
        'examples': formatted_examples
    }
    
    with open('validated_golden_examples.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Extracted {len(formatted_examples)} examples from validated dataset")
    print(f"Saved to: validated_golden_examples.json")
    
    # Print first few
    print(f"\nFirst 3 examples:")
    for i, ex in enumerate(formatted_examples[:3], 1):
        print(f"\n{i}. {ex['golden_action']}")
        print(f"   Input: regulation='{ex['regulation']}', days='{ex['days']}', hours='{ex['hours']}'")
        print(f"   Output: {ex['golden_summary']}")

if __name__ == '__main__':
    extract_examples()