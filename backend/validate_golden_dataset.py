"""
Validate golden dataset interpretations for accuracy issues.
Checks for common interpretation errors and inconsistencies.
"""

import csv
import re
from typing import List, Dict, Tuple

def validate_golden_dataset():
    """Validate all completed golden interpretations."""
    
    issues = []
    
    with open('golden_dataset_partial.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader if row['golden_summary'].strip()]
    
    print(f"🔍 Validating {len(rows)} completed golden interpretations...\n")
    print("=" * 100)
    
    for i, row in enumerate(rows, 1):
        row_issues = validate_row(row, i)
        if row_issues:
            issues.extend(row_issues)
    
    # Print results
    if not issues:
        print("\n✅ ALL INTERPRETATIONS LOOK GOOD!")
        print("No accuracy issues detected.")
    else:
        print(f"\n⚠️  FOUND {len(issues)} POTENTIAL ISSUES:\n")
        print("=" * 100)
        
        for issue in issues:
            print(f"\n🔴 Row {issue['row']}: {issue['type']}")
            print(f"   unique_id: {issue['unique_id']}")
            print(f"   Issue: {issue['description']}")
            print(f"   Source: {issue['source_data']}")
            print(f"   Your interpretation: {issue['interpretation']}")
            if issue.get('suggestion'):
                print(f"   💡 Suggestion: {issue['suggestion']}")
    
    print(f"\n" + "=" * 100)
    print(f"Summary: {len(rows)} validated, {len(issues)} issues found")
    
    return issues

def validate_row(row: Dict, row_num: int) -> List[Dict]:
    """Validate a single row for accuracy issues."""
    issues = []
    
    # Extract fields
    regulation = row.get('regulation', '').strip()
    days = row.get('days', '').strip()
    hours = row.get('hours', '').strip()
    hrs_begin = row.get('hrs_begin', '').strip()
    hrs_end = row.get('hrs_end', '').strip()
    hrlimit = row.get('hrlimit', '').strip()
    rpparea1 = row.get('rpparea1', '').strip()
    
    golden_action = row.get('golden_action', '').strip()
    golden_summary = row.get('golden_summary', '').strip()
    golden_severity = row.get('golden_severity', '').strip()
    golden_hours = row.get('golden_hours', '').strip()
    golden_time_limit = row.get('golden_time_limit_minutes', '').strip()
    
    unique_id = row.get('unique_id', '')
    
    # Check 1: Time limit mismatch
    # EXCEPTION: 72hr limit in HV RPP areas = 2hr for non-permit holders (institutional knowledge)
    if hrlimit and hrlimit not in ['0', '']:
        try:
            source_hours = float(hrlimit)
            
            # Skip 72hr check for HV RPP areas (institutional knowledge)
            if source_hours == 72 and rpparea1 == 'HV':
                pass  # 72hr is for permit holders, 2hr for non-permit holders is correct
            elif golden_time_limit:
                # Convert to minutes if needed
                if 'hr' in golden_time_limit.lower():
                    interp_hours = float(re.findall(r'\d+', golden_time_limit)[0])
                elif 'min' in golden_time_limit.lower():
                    interp_hours = float(re.findall(r'\d+', golden_time_limit)[0]) / 60
                else:
                    interp_hours = None
                
                if interp_hours and abs(source_hours - interp_hours) > 0.1:
                    issues.append({
                        'row': row_num,
                        'unique_id': unique_id,
                        'type': 'TIME_LIMIT_MISMATCH',
                        'description': f'Source says {source_hours}hr but interpretation says {golden_time_limit}',
                        'source_data': f'hrlimit={hrlimit}',
                        'interpretation': golden_summary,
                        'suggestion': f'Should be {int(source_hours * 60)}min or {source_hours}hr'
                    })
        except (ValueError, IndexError):
            pass
    
    # Check 2: Hours mismatch (DISABLED - too many false positives with 24hr to 12hr conversion)
    # Users correctly convert 24-hour format to 12-hour format (e.g., 1800 -> 6pm)
    pass
    
    # Check 3: RPP area not mentioned when present
    if rpparea1 and rpparea1.strip() and golden_action == 'Time-limited':
        if 'except' not in golden_summary.lower() and 'permit' not in golden_summary.lower():
            issues.append({
                'row': row_num,
                'unique_id': unique_id,
                'type': 'MISSING_RPP_EXCEPTION',
                'description': f'RPP Area {rpparea1} present but not mentioned in summary',
                'source_data': f'rpparea1={rpparea1}',
                'interpretation': golden_summary,
                'suggestion': 'Should mention "except residential permit" or "except Area X permit"'
            })
    
    # Check 4: Action/Severity consistency
    # EXCEPTION: "Restricted" can be "critical" for Paid+Permit regulations (conservative interpretation)
    severity_rules = {
        'Prohibited': ['critical', 'high'],
        'Permit-required': ['high', 'critical'],
        'Time-limited': ['medium', 'low'],
        'Restricted': ['low', 'medium', 'critical'],  # Added 'critical' for Paid+Permit cases
        'No data': ['low']
    }
    
    if golden_action in severity_rules:
        expected_severities = severity_rules[golden_action]
        if golden_severity not in expected_severities:
            # Special case: Paid+Permit can be critical
            if regulation and 'paid' in regulation.lower() and 'permit' in regulation.lower():
                pass  # Allow critical severity for Paid+Permit
            else:
                issues.append({
                    'row': row_num,
                    'unique_id': unique_id,
                    'type': 'ACTION_SEVERITY_MISMATCH',
                    'description': f'Action "{golden_action}" typically has severity {expected_severities} but got "{golden_severity}"',
                    'source_data': f'action={golden_action}',
                    'interpretation': f'severity={golden_severity}',
                    'suggestion': f'Consider changing severity to {expected_severities[0]}'
                })
    
    # Check 5: "No parking" in regulation but action is not Prohibited
    if regulation and 'no parking' in regulation.lower():
        if 'anytime' in regulation.lower() or 'any time' in regulation.lower():
            if golden_action != 'Prohibited':
                issues.append({
                    'row': row_num,
                    'unique_id': unique_id,
                    'type': 'NO_PARKING_ANYTIME_MISCLASSIFIED',
                    'description': '"No parking anytime" should be Prohibited action',
                    'source_data': f'regulation={regulation}',
                    'interpretation': f'action={golden_action}',
                    'suggestion': 'Change action to "Prohibited"'
                })
    
    # Check 6: Government permit should be Permit-required
    if regulation and 'government permit' in regulation.lower():
        if golden_action != 'Permit-required':
            issues.append({
                'row': row_num,
                'unique_id': unique_id,
                'type': 'GOVERNMENT_PERMIT_MISCLASSIFIED',
                'description': 'Government permit regulations should be Permit-required action',
                'source_data': f'regulation={regulation}',
                'interpretation': f'action={golden_action}',
                'suggestion': 'Change action to "Permit-required"'
            })
    
    # Check 7: Days mismatch
    if days and days.strip() and golden_hours != 'No data':
        # Check if days are mentioned in golden_hours or golden_summary
        days_lower = days.lower()
        summary_lower = golden_summary.lower()
        hours_lower = golden_hours.lower()
        
        # EXCEPTION: M-Su (Monday-Sunday) = Daily operation
        # When it's daily, you do NOT need to mention days or "daily" - skip validation
        if days_lower in ['m-su', 'm-sun']:
            pass  # Daily regulations don't need day mentions
        # Common day patterns (M-F, M-Sa, etc.) - these MUST be mentioned
        elif 'm-f' in days_lower or 'monday' in days_lower:
            if 'monday' not in summary_lower and 'monday' not in hours_lower and 'm-f' not in summary_lower:
                if 'daily' not in summary_lower and 'daily' not in hours_lower:
                    issues.append({
                        'row': row_num,
                        'unique_id': unique_id,
                        'type': 'DAYS_NOT_MENTIONED',
                        'description': f'Days "{days}" not clearly mentioned in interpretation',
                        'source_data': f'days={days}',
                        'interpretation': golden_summary,
                        'suggestion': 'Ensure day restrictions are mentioned'
                    })
    
    return issues

if __name__ == "__main__":
    validate_golden_dataset()