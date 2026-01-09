"""
Process remaining unique regulations using refined Worker/Judge prompts
Implements rate limiting, checkpointing, and graceful error handling for free tier
"""
import json
import time
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
import pandas as pd
from typing import Dict, List, Any

# Configuration
RATE_LIMIT_RPM = 10  # 10 requests per minute (free tier)
SECONDS_BETWEEN_CALLS = 6  # 60 / 10 = 6 seconds
CHECKPOINT_INTERVAL = 5  # Save every 5 results
MAX_RETRIES = 3
OUTPUT_FILE = 'remaining_interpretations.json'

# Load API key
from dotenv import load_dotenv
import os
load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Load refined prompts
WORKER_PROMPT = Path('prompts/refined_worker_prompt.md').read_text()
JUDGE_PROMPT = Path('prompts/refined_judge_prompt.md').read_text()

def load_remaining_regulations() -> List[Dict[str, Any]]:
    """Load regulations that haven't been processed yet"""
    print("📊 Loading datasets...")
    
    # Load all unique regulations
    with open('unique_regulations.json', 'r') as f:
        all_regs = json.load(f)
    
    # Load golden dataset (already completed)
    golden_df = pd.read_csv('golden_dataset_partial.csv')
    completed_ids = set(golden_df['unique_id'].tolist())
    
    # Filter to remaining
    remaining = [r for r in all_regs if r['unique_id'] not in completed_ids]
    
    print(f"   Total unique regulations: {len(all_regs)}")
    print(f"   Completed (golden dataset): {len(completed_ids)}")
    print(f"   Remaining to process: {len(remaining)}")
    print(f"   API calls needed: {len(remaining) * 2} (Worker + Judge)")
    
    return remaining

def call_worker(regulation: Dict[str, Any]) -> Dict[str, Any]:
    """Call Worker LLM with refined prompt"""
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Format input for Worker
    input_data = {
        'regulation': regulation.get('regulation', ''),
        'days': regulation.get('days', ''),
        'hours': regulation.get('hours', ''),
        'hrs_begin': regulation.get('hrs_begin', ''),
        'hrs_end': regulation.get('hrs_end', ''),
        'hrlimit': regulation.get('hrlimit', ''),
        'rpparea1': regulation.get('rpparea1', '')
    }
    
    prompt = f"{WORKER_PROMPT}\n\n## INPUT DATA\n```json\n{json.dumps(input_data, indent=2)}\n```\n\nProvide your interpretation as JSON only, no additional text."
    
    response = model.generate_content(prompt)
    
    # Parse JSON response
    response_text = response.text.strip()
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    
    return json.loads(response_text.strip())

def call_judge(regulation: Dict[str, Any], worker_output: Dict[str, Any]) -> Dict[str, Any]:
    """Call Judge LLM with refined prompt"""
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Format input for Judge
    evaluation_input = {
        'source_data': {
            'regulation': regulation.get('regulation', ''),
            'days': regulation.get('days', ''),
            'hours': regulation.get('hours', ''),
            'hrs_begin': regulation.get('hrs_begin', ''),
            'hrs_end': regulation.get('hrs_end', ''),
            'hrlimit': regulation.get('hrlimit', ''),
            'rpparea1': regulation.get('rpparea1', '')
        },
        'interpretation': worker_output
    }
    
    prompt = f"{JUDGE_PROMPT}\n\n## EVALUATION INPUT\n```json\n{json.dumps(evaluation_input, indent=2)}\n```\n\nProvide your evaluation as JSON only, no additional text."
    
    response = model.generate_content(prompt)
    
    # Parse JSON response
    response_text = response.text.strip()
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    
    return json.loads(response_text.strip())

def save_checkpoint(results: List[Dict[str, Any]], output_file: str):
    """Save results to file"""
    with open(output_file, 'w') as f:
        json.dump({
            'total_processed': len(results),
            'last_updated': datetime.now().isoformat(),
            'results': results
        }, f, indent=2)

def process_with_rate_limit(regulations: List[Dict[str, Any]], output_file: str = OUTPUT_FILE) -> List[Dict[str, Any]]:
    """Process regulations with rate limiting and checkpointing"""
    results = []
    start_time = time.time()
    api_calls_made = 0
    
    print(f"\n🚀 Starting processing...")
    print(f"   Rate limit: {RATE_LIMIT_RPM} requests/minute")
    print(f"   Checkpoint interval: Every {CHECKPOINT_INTERVAL} results")
    print(f"   Output file: {output_file}")
    print(f"   Estimated time: ~{len(regulations) * 2 * SECONDS_BETWEEN_CALLS / 60:.1f} minutes\n")
    
    for i, reg in enumerate(regulations, 1):
        unique_id_short = reg['unique_id'][:8]
        print(f"[{i}/{len(regulations)}] Processing {unique_id_short}...")
        
        try:
            # Worker call
            print(f"   → Calling Worker...")
            worker_result = call_worker(reg)
            api_calls_made += 1
            print(f"   ✓ Worker: {worker_result.get('action', 'N/A')} - {worker_result.get('summary', 'N/A')[:50]}...")
            time.sleep(SECONDS_BETWEEN_CALLS)
            
            # Judge call
            print(f"   → Calling Judge...")
            judge_result = call_judge(reg, worker_result)
            api_calls_made += 1
            print(f"   ✓ Judge: Score {judge_result.get('score', 'N/A')}, Flagged: {judge_result.get('flagged', 'N/A')}")
            time.sleep(SECONDS_BETWEEN_CALLS)
            
            # Store result
            results.append({
                'unique_id': reg['unique_id'],
                'usage_count': reg.get('usage_count', 0),
                'source': {
                    'regulation': reg.get('regulation', ''),
                    'days': reg.get('days', ''),
                    'hours': reg.get('hours', ''),
                    'hrs_begin': reg.get('hrs_begin', ''),
                    'hrs_end': reg.get('hrs_end', ''),
                    'hrlimit': reg.get('hrlimit', ''),
                    'rpparea1': reg.get('rpparea1', '')
                },
                'worker_output': worker_result,
                'judge_evaluation': judge_result,
                'processed_at': datetime.now().isoformat()
            })
            
            # Checkpoint save
            if i % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(results, output_file)
                elapsed = time.time() - start_time
                print(f"\n💾 Checkpoint saved: {i}/{len(regulations)} processed ({elapsed/60:.1f} min elapsed)")
                print(f"   API calls made: {api_calls_made}/200 daily quota\n")
        
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Error: {error_msg}")
            
            # Check for quota exceeded
            if "quota" in error_msg.lower() or "429" in error_msg:
                print(f"\n⚠️  QUOTA EXCEEDED after {api_calls_made} API calls")
                print(f"   Processed: {len(results)}/{len(regulations)} regulations")
                print(f"   Saving progress and exiting...")
                save_checkpoint(results, output_file)
                return results
            
            # Log error and continue
            results.append({
                'unique_id': reg['unique_id'],
                'error': error_msg,
                'processed_at': datetime.now().isoformat()
            })
            continue
    
    # Final save
    save_checkpoint(results, output_file)
    
    elapsed = time.time() - start_time
    print(f"\n✅ Processing complete!")
    print(f"   Processed: {len(results)}/{len(regulations)} regulations")
    print(f"   API calls made: {api_calls_made}")
    print(f"   Time elapsed: {elapsed/60:.1f} minutes")
    print(f"   Output saved to: {output_file}")
    
    # Summary statistics
    successful = [r for r in results if 'error' not in r]
    flagged = [r for r in successful if r.get('judge_evaluation', {}).get('flagged', False)]
    avg_score = sum(r.get('judge_evaluation', {}).get('score', 0) for r in successful) / len(successful) if successful else 0
    
    print(f"\n📊 Summary:")
    print(f"   Successful: {len(successful)}")
    print(f"   Errors: {len(results) - len(successful)}")
    print(f"   Flagged by Judge: {len(flagged)}")
    print(f"   Average Judge score: {avg_score:.2f}")
    
    return results

def main():
    """Main execution"""
    print("=" * 80)
    print("PARKING REGULATION INTERPRETATION - BATCH PROCESSING")
    print("Using Refined Worker/Judge Prompts with Free Tier Rate Limiting")
    print("=" * 80)
    
    # Load remaining regulations
    remaining = load_remaining_regulations()
    
    if not remaining:
        print("\n✅ No remaining regulations to process!")
        print("   All unique regulations have been completed in the golden dataset.")
        return
    
    # Confirm before proceeding
    print(f"\n⚠️  About to process {len(remaining)} regulations")
    print(f"   This will make {len(remaining) * 2} API calls")
    print(f"   Estimated time: ~{len(remaining) * 2 * SECONDS_BETWEEN_CALLS / 60:.1f} minutes")
    
    response = input("\nProceed? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Process
    results = process_with_rate_limit(remaining)
    
    print(f"\n✅ Done! Results saved to: {OUTPUT_FILE}")
    print(f"   Review the results and merge with golden dataset when ready.")

if __name__ == '__main__':
    main()