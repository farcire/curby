import json
import os

def display_results():
    file_path = 'backend/evaluation_results.json'
    
    if not os.path.exists(file_path):
        print(f"Error: Results file not found at {file_path}")
        return

    with open(file_path, 'r') as f:
        data = json.load(f)

    summary = data.get('summary', {})
    results = data.get('results', [])

    print("\n" + "="*80)
    print(f"EVALUATION SUMMARY ({summary.get('model', 'Unknown Model')})")
    print("="*80)
    print(f"Total Cases:   {summary.get('total_cases', 0)}")
    print(f"Passed:        {summary.get('passed_count', 0)}")
    print(f"Pass Rate:     {summary.get('pass_rate', 0):.1f}%")
    print(f"Average Score: {summary.get('average_score', 0):.2f}")
    print(f"Timestamp:     {summary.get('timestamp', 'N/A')}")
    print("="*80 + "\n")

    print(f"{'ID':<12} | {'Score':<5} | {'Status':<6} | {'Original Text':<50}")
    print("-" * 80)

    for case in results:
        case_id = case.get('test_case_id', 'N/A')
        score = case.get('evaluation', {}).get('score', 0.0)
        text = case.get('original_text', '')
        
        # Determine status
        if score >= 0.9:
            status = "PASS"
        elif score >= 0.5:
            status = "WARN"
        else:
            status = "FAIL"
            
        # Truncate text if too long
        display_text = (text[:47] + '...') if len(text) > 47 else text
        
        print(f"{case_id:<12} | {score:<5.1f} | {status:<6} | {display_text}")

    print("\n" + "="*80)
    print("FAILED CASES DETAILS")
    print("="*80)
    
    for case in results:
        score = case.get('evaluation', {}).get('score', 0.0)
        if score < 0.9:
            print(f"\n[{case.get('test_case_id')}] (Score: {score})")
            print(f"Text: {case.get('original_text')}")
            reason = case.get('evaluation', {}).get('reasoning', 'No reasoning provided')
            print(f"Reason: {reason}")
            print("-" * 40)

if __name__ == "__main__":
    display_results()