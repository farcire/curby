import json
import os
from datetime import datetime

def generate_notion_report():
    input_path = 'backend/evaluation_results.json'
    output_path = 'backend/EVALUATION_REPORT.md'
    
    if not os.path.exists(input_path):
        print(f"Error: Results file not found at {input_path}")
        return

    with open(input_path, 'r') as f:
        data = json.load(f)

    summary = data.get('summary', {})
    results = data.get('results', [])

    timestamp = summary.get('timestamp', 'N/A')
    model = summary.get('model', 'Unknown')
    pass_rate = summary.get('pass_rate', 0)
    
    # Start building Markdown content
    md = []
    
    # Title and Summary Block (Notion Callout style)
    md.append(f"# 📊 AI Restriction Interpretation Report")
    md.append("")
    md.append("> **Evaluation Summary**")
    md.append(f"> - **Model:** `{model}`")
    md.append(f"> - **Date:** {timestamp}")
    md.append(f"> - **Pass Rate:** {pass_rate:.1f}% ({summary.get('passed_count')}/{summary.get('total_cases')})")
    md.append(f"> - **Avg Score:** {summary.get('average_score', 0):.2f}")
    md.append("")

    # Results Table
    md.append("## 🧪 Test Case Results")
    md.append("")
    md.append("| ID | Object ID | Score | Status | Original Text |")
    md.append("|:---|:---:|:---:|:---:|:---|")
    
    # Load original test cases to look up object IDs
    test_cases_path = 'backend/test_set_regulations.json'
    test_cases_map = {}
    if os.path.exists(test_cases_path):
        with open(test_cases_path, 'r') as f:
            tcs = json.load(f)
            for tc in tcs:
                test_cases_map[tc['id']] = tc.get('original_data', {}).get('objectid', 'N/A')

    for case in results:
        case_id = case.get('test_case_id', 'N/A')
        object_id = test_cases_map.get(case_id, 'N/A')
        score = case.get('evaluation', {}).get('score', 0.0)
        text = case.get('original_text', '').replace('|', '\|').replace('\n', ' ')
        
        # Determine status icon
        if score >= 0.9:
            status = "✅ PASS"
        elif score >= 0.5:
            status = "⚠️ WARN"
        else:
            status = "❌ FAIL"
            
        # Truncate text for table
        display_text = (text[:60] + '...') if len(text) > 60 else text
        
        md.append(f"| {case_id} | {object_id} | {score} | {status} | {display_text} |")

    md.append("")
    
    # Detailed Failures Section
    md.append("## 🔍 Failed Cases Analysis")
    md.append("")
    
    failed_cases = [c for c in results if c.get('evaluation', {}).get('score', 0.0) < 0.9]
    
    if not failed_cases:
        md.append("🎉 **No failures found!**")
    else:
        for case in failed_cases:
            case_id = case.get('test_case_id')
            object_id = test_cases_map.get(case_id, 'N/A')
            score = case.get('evaluation', {}).get('score')
            text = case.get('original_text')
            reason = case.get('evaluation', {}).get('reasoning', 'No reasoning provided')
            
            md.append(f"### {case_id} (ObjID: {object_id}) `Score: {score}`")
            md.append(f"**📝 Original Text:**")
            md.append(f"> {text}")
            md.append("")
            md.append(f"**🤔 Reasoning:**")
            md.append(f"{reason}")
            md.append("")
            md.append("---")
            md.append("")

    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(md))
        
    print(f"Successfully generated Notion-formatted report at: {output_path}")

if __name__ == "__main__":
    generate_notion_report()