"""
Process a SAMPLE (25%) of unique regulation combinations through the LLM pipeline.

This script:
1. Loads unique regulations from unique_regulations.json
2. Processes the first 25% (73 combinations) through gemini-2.0-flash
3. Sends to Worker for interpretation, then Judge for evaluation
4. Generates human-reviewable output with ALL fields and ObjectIds
5. Respects FREE TIER rate limits (10 RPM)
"""

import asyncio
import os
import json
import time
import google.generativeai as genai
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# FREE TIER RATE LIMITS
RATE_LIMIT_RPM = 10      # Requests per minute
DELAY_BETWEEN_CALLS = 6  # seconds (ensures 10 RPM compliance)

def configure_genai():
    # Load .env from parent directory (project root)
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

WORKER_PROMPT_TEMPLATE = """You are an expert Parking Data Analyst for the SFMTA. 
Your goal is to extract structured rules from parking regulation data.

INPUT DATA:
- Regulation Text: {regulation}
- Days: {days}
- Hours: {hours}
- Hours Begin: {hrs_begin}
- Hours End: {hrs_end}
- Regulation Details: {regdetails}
- RPP Area: {rpparea1}
- Exceptions: {exceptions}
- From Time: {from_time}
- To Time: {to_time}
- Hour Limit: {hrlimit}

INSTRUCTIONS:
1. Analyze ALL input fields to determine the parking rule
2. Prioritize structured fields over text when there's a conflict
3. Determine the 'action' (allowed, prohibited, time-limited, etc.)
4. Determine the 'severity' (critical, high, medium, low)
5. Generate a clear, human-readable 'summary'
6. Extract specific conditions (days, hours, time_limit, exceptions)

OUTPUT JSON FORMAT:
{{
  "action": "string (allowed/prohibited/time-limited/restricted)",
  "summary": "string (clear, plain English summary)",
  "severity": "string (critical/high/medium/low)",
  "conditions": {{
    "days": ["string"],
    "hours": "string",
    "time_limit_minutes": int or null,
    "exceptions": ["string"]
  }},
  "details": "string (any additional context)"
}}
"""

JUDGE_PROMPT_TEMPLATE = """You are a Quality Assurance Judge for parking regulation interpretations.
Compare the Original Input with the Worker's Interpretation.

ORIGINAL INPUT:
- Regulation: {regulation}
- Days: {days}
- Hours: {hours}
- Hours Begin: {hrs_begin}
- Hours End: {hrs_end}
- Regulation Details: {regdetails}
- RPP Area: {rpparea1}
- Exceptions: {exceptions}
- From Time: {from_time}
- To Time: {to_time}
- Hour Limit: {hrlimit}

WORKER INTERPRETATION:
{worker_json}

EVALUATION CRITERIA:
1. ACCURACY: Does the summary accurately reflect ALL the input fields?
2. SAFETY: Did the worker miss any critical prohibitions (Tow Away, No Stopping)?
3. COMPLETENESS: Are time limits, RPP areas, and exceptions properly captured?
4. HALLUCINATION: Did the worker invent details not present in the input?

Scoring Guide:
- 1.0: Perfect interpretation, all details correct
- 0.9-0.99: Minor stylistic issues only
- 0.7-0.89: Missing minor details or slight inaccuracies
- 0.5-0.69: Missing important information or moderate errors
- 0.0-0.49: Critical safety errors or major hallucinations

OUTPUT JSON FORMAT:
{{
  "score": float (0.0 to 1.0),
  "reasoning": "string (detailed explanation of score)",
  "flagged": boolean (true if score < 0.9),
  "issues": ["string"] (list of specific problems found)
}}
"""

async def call_llm(model, prompt: str, label: str) -> Dict[str, Any]:
    """Call Gemini API with error handling and JSON parsing."""
    try:
        response = await asyncio.to_thread(
            model.generate_content, 
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"  ❌ {label} Error: {e}")
        return None

async def process_sample():
    print("🚀 Starting SAMPLE LLM Processing Pipeline (25% of data)")
    print("   Model: gemini-2.0-flash (FREE tier)")
    
    try:
        model = configure_genai()
    except ValueError as e:
        print(f"❌ Setup Error: {e}")
        return

    # Load unique regulations
    input_file = "unique_regulations.json"
    if not os.path.exists(input_file):
        print(f"❌ Input file {input_file} not found. Run extraction first.")
        return
        
    with open(input_file, "r") as f:
        data = json.load(f)
        all_regulations = data["unique_combinations"]

    # Process 25% (rounded up)
    sample_size = (len(all_regulations) + 3) // 4  # 25% rounded up
    sample_regulations = all_regulations[:sample_size]
    
    print(f"✅ Loaded {len(all_regulations)} total unique regulations")
    print(f"📊 Processing SAMPLE: {sample_size} combinations (25%)")
    print(f"⏱️  Estimated time: {sample_size * DELAY_BETWEEN_CALLS * 2 / 60:.1f} minutes")
    print(f"💰 Cost: $0.00 (FREE tier)\n")

    results = []
    start_time = time.time()
    
    for i, item in enumerate(sample_regulations, 1):
        fields = item["fields"]
        print(f"\n{'='*80}")
        # Fix: Handle None values properly
        reg_text = fields.get('regulation') or 'N/A'
        print(f"Processing {i}/{sample_size}: {reg_text[:60]}...")
        print(f"{'='*80}")
        
        # 1. Worker Step
        worker_prompt = WORKER_PROMPT_TEMPLATE.format(
            regulation=fields.get('regulation') or 'N/A',
            days=fields.get('days') or 'N/A',
            hours=fields.get('hours') or 'N/A',
            hrs_begin=fields.get('hrs_begin') or 'N/A',
            hrs_end=fields.get('hrs_end') or 'N/A',
            regdetails=fields.get('regdetails') or 'N/A',
            rpparea1=fields.get('rpparea1') or 'N/A',
            exceptions=fields.get('exceptions') or 'N/A',
            from_time=fields.get('from_time') or 'N/A',
            to_time=fields.get('to_time') or 'N/A',
            hrlimit=fields.get('hrlimit') or 'N/A'
        )
        
        print("  🤖 Calling Worker LLM...")
        worker_result = await call_llm(model, worker_prompt, "Worker")
        
        if not worker_result:
            print("  ⚠️ Worker failed, skipping...")
            continue
        
        print(f"  ✅ Worker completed: {worker_result.get('summary', 'N/A')[:60]}")
        
        # Rate limit delay
        await asyncio.sleep(DELAY_BETWEEN_CALLS)
        
        # 2. Judge Step
        judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
            regulation=fields.get('regulation') or 'N/A',
            days=fields.get('days') or 'N/A',
            hours=fields.get('hours') or 'N/A',
            hrs_begin=fields.get('hrs_begin') or 'N/A',
            hrs_end=fields.get('hrs_end') or 'N/A',
            regdetails=fields.get('regdetails') or 'N/A',
            rpparea1=fields.get('rpparea1') or 'N/A',
            exceptions=fields.get('exceptions') or 'N/A',
            from_time=fields.get('from_time') or 'N/A',
            to_time=fields.get('to_time') or 'N/A',
            hrlimit=fields.get('hrlimit') or 'N/A',
            worker_json=json.dumps(worker_result, indent=2)
        )
        
        print("  ⚖️  Calling Judge LLM...")
        judge_result = await call_llm(model, judge_prompt, "Judge")
        
        if not judge_result:
            print("  ⚠️ Judge failed, skipping...")
            continue
        
        score = judge_result.get('score', 0)
        flagged = judge_result.get('flagged', True)
        print(f"  ✅ Judge completed: Score={score:.2f} | Flagged={flagged}")
        
        # Store result with ALL fields for human review
        interpretation_entry = {
            "unique_id": item["unique_id"],
            "usage_count": item["usage_count"],
            "sample_object_ids": item.get("sample_object_ids", []),
            "all_object_ids": item.get("all_object_ids", []),
            "source_fields": fields,
            "worker_output": worker_result,
            "judge_evaluation": judge_result
        }
        
        results.append(interpretation_entry)
        
        # Save intermediate results after each successful interpretation
        if len(results) % 5 == 0 or len(results) == 1:  # Save every 5 results and first result
            temp_output = {
                "metadata": {
                    "processed_at": datetime.now().isoformat(),
                    "model": "gemini-2.0-flash",
                    "total_unique_combinations": len(all_regulations),
                    "sample_size": sample_size,
                    "sample_percentage": "25%",
                    "processed_count": len(results),
                    "status": "in_progress"
                },
                "interpretations": results
            }
            with open("sample_interpretations_review_temp.json", "w") as f:
                json.dump(temp_output, f, indent=2)
            print(f"  💾 Checkpoint saved: {len(results)} interpretations")
        
        # Rate limit delay
        await asyncio.sleep(DELAY_BETWEEN_CALLS)

    # Save final results
    output_file = "sample_interpretations_review.json"
    output_data = {
        "metadata": {
            "processed_at": datetime.now().isoformat(),
            "model": "gemini-2.0-flash",
            "total_unique_combinations": len(all_regulations),
            "sample_size": sample_size,
            "sample_percentage": "25%",
            "processed_count": len(results),
            "elapsed_time_minutes": (time.time() - start_time) / 60,
            "status": "completed"
        },
        "interpretations": results
    }
    
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    # Clean up temp file if it exists
    import os
    if os.path.exists("sample_interpretations_review_temp.json"):
        os.remove("sample_interpretations_review_temp.json")
    
    print(f"\n{'='*80}")
    print(f"🎉 Processing Complete!")
    print(f"{'='*80}")
    print(f"📊 Statistics:")
    print(f"   - Processed: {len(results)}/{sample_size} combinations")
    print(f"   - Success rate: {len(results)/sample_size*100:.1f}%")
    print(f"   - Time elapsed: {(time.time() - start_time)/60:.1f} minutes")
    print(f"   - Output file: {output_file}")
    
    # Summary statistics
    flagged_count = sum(1 for r in results if r['judge_evaluation'].get('flagged', False))
    avg_score = sum(r['judge_evaluation'].get('score', 0) for r in results) / len(results) if results else 0
    
    print(f"\n📈 Quality Metrics:")
    print(f"   - Average Judge Score: {avg_score:.3f}")
    print(f"   - Flagged for review: {flagged_count}/{len(results)} ({flagged_count/len(results)*100:.1f}%)")
    print(f"   - Auto-approved: {len(results)-flagged_count}/{len(results)} ({(len(results)-flagged_count)/len(results)*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(process_sample())