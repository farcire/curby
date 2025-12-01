# Free Tier Processing Plan for Parking Regulation Interpretations

## Current Situation

### API Limits (Gemini 2.0 Flash Free Tier)
- **Daily Quota**: 200 requests/day
- **Rate Limit**: 10 requests/minute (RPM)
- **Cost**: $0 (free tier)

### Dataset Size
- **Total unique regulations**: 292 combinations
- **Validated golden dataset**: 222 entries (already completed)
- **Remaining to process**: 70 unique regulations
- **API calls per regulation**: 2 (Worker + Judge)
- **Total API calls needed**: 70 × 2 = **140 calls**

### Current Status
- ✅ Processed: ~29 combinations (58 API calls) before hitting quota
- ✅ Validated: 222 golden dataset entries (no API calls needed)
- ⏳ Remaining: 70 combinations (140 API calls)

## Cost-Effective Strategy

### Option 1: Single-Day Completion (RECOMMENDED)
**Timeline**: 1 day
**Approach**: Process all 70 remaining regulations in one batch

**Execution Plan**:
1. Wait for quota reset (midnight PST)
2. Run batch processing script with:
   - Rate limiting: 10 requests/minute
   - Checkpoint saving: Every 5 results
   - Error handling: Graceful quota exceeded handling
3. Complete all 140 API calls (70 regulations × 2)
4. Total time: ~14 minutes (140 calls ÷ 10 RPM)

**Advantages**:
- ✅ Fastest completion (1 day)
- ✅ Well within daily quota (140/200 = 70% usage)
- ✅ Simple execution
- ✅ No multi-day coordination needed

**Script**: `process_remaining_interpretations.py`

### Option 2: Multi-Day Processing
**Timeline**: 2 days
**Approach**: Split processing across multiple days for safety margin

**Day 1**: Process 35 regulations (70 API calls)
**Day 2**: Process 35 regulations (70 API calls)

**Advantages**:
- ✅ More conservative (35% daily quota usage)
- ✅ Allows for retries if errors occur
- ✅ Can review Day 1 results before continuing

**Disadvantages**:
- ❌ Slower (2 days vs 1 day)
- ❌ More manual coordination

### Option 3: Upgrade to Paid Tier
**Cost**: ~$0.01 per 1000 requests
**Total cost**: 140 requests × $0.00001 = **$0.0014** (~$0.00)

**Advantages**:
- ✅ No daily quota limits
- ✅ Higher rate limits (1000 RPM)
- ✅ Complete in minutes
- ✅ Negligible cost

**Disadvantages**:
- ❌ Requires payment setup
- ❌ Overkill for small dataset

## Recommended Implementation

### Phase 1: Process Remaining 70 Regulations (Option 1)

**Script**: `backend/process_remaining_interpretations.py`

```python
"""
Process the 70 remaining unique regulations using refined Worker/Judge prompts
"""
import json
import time
from datetime import datetime
import google.generativeai as genai
from pathlib import Path

# Configuration
RATE_LIMIT_RPM = 10  # 10 requests per minute
CHECKPOINT_INTERVAL = 5  # Save every 5 results
MAX_RETRIES = 3

def load_remaining_regulations():
    """Load regulations that haven't been processed yet"""
    # Load all unique regulations
    with open('unique_regulations.json', 'r') as f:
        all_regs = json.load(f)
    
    # Load golden dataset (already completed)
    import pandas as pd
    golden_df = pd.read_csv('golden_dataset_partial.csv')
    completed_ids = set(golden_df['unique_id'].tolist())
    
    # Filter to remaining
    remaining = [r for r in all_regs if r['unique_id'] not in completed_ids]
    
    print(f"Total regulations: {len(all_regs)}")
    print(f"Completed (golden): {len(completed_ids)}")
    print(f"Remaining: {len(remaining)}")
    
    return remaining

def process_with_rate_limit(regulations, output_file='remaining_interpretations.json'):
    """Process regulations with rate limiting and checkpointing"""
    results = []
    start_time = time.time()
    
    for i, reg in enumerate(regulations, 1):
        print(f"\nProcessing {i}/{len(regulations)}: {reg['unique_id'][:8]}...")
        
        try:
            # Worker call
            worker_result = call_worker(reg)
            time.sleep(6)  # 10 RPM = 6 seconds between calls
            
            # Judge call
            judge_result = call_judge(reg, worker_result)
            time.sleep(6)  # 10 RPM = 6 seconds between calls
            
            # Store result
            results.append({
                'unique_id': reg['unique_id'],
                'source': reg,
                'worker': worker_result,
                'judge': judge_result,
                'processed_at': datetime.now().isoformat()
            })
            
            # Checkpoint save
            if i % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(results, output_file)
                print(f"✅ Checkpoint saved: {i} regulations processed")
        
        except Exception as e:
            print(f"❌ Error processing {reg['unique_id']}: {e}")
            if "quota" in str(e).lower():
                print("⚠️  Quota exceeded. Saving progress and exiting...")
                save_checkpoint(results, output_file)
                return results
            continue
    
    # Final save
    save_checkpoint(results, output_file)
    
    elapsed = time.time() - start_time
    print(f"\n✅ Processing complete!")
    print(f"   Processed: {len(results)} regulations")
    print(f"   Time: {elapsed/60:.1f} minutes")
    print(f"   Output: {output_file}")
    
    return results

def save_checkpoint(results, output_file):
    """Save results to file"""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    remaining = load_remaining_regulations()
    process_with_rate_limit(remaining)
```

### Phase 2: Merge with Golden Dataset

After processing, merge the new interpretations with the golden dataset:

```python
"""
Merge remaining interpretations with golden dataset
"""
import pandas as pd
import json

# Load golden dataset
golden_df = pd.read_csv('golden_dataset_partial.csv')

# Load new interpretations
with open('remaining_interpretations.json', 'r') as f:
    new_interps = json.load(f)

# Convert to DataFrame and merge
# ... (merge logic)

# Save complete dataset
complete_df.to_csv('complete_interpretations.csv', index=False)
```

## Execution Timeline

### Day 1 (Today)
- ✅ Validated golden dataset (222 entries)
- ✅ Created refined Worker/Judge prompts
- ✅ Created processing plan

### Day 2 (Tomorrow)
- ⏰ Wait for quota reset (midnight PST)
- 🚀 Run `process_remaining_interpretations.py`
- ⏱️ Complete in ~14 minutes (140 calls ÷ 10 RPM)
- ✅ Review results
- 📊 Merge with golden dataset

### Day 3 (Optional)
- 📈 Analyze complete dataset
- 🔍 Identify any issues
- 🔄 Re-process if needed (still within quota)

## Monitoring & Safety

### Rate Limiting
- **10 RPM**: 6 seconds between API calls
- **Buffer**: Add 0.5s extra delay for safety
- **Total time**: ~15 minutes for 140 calls

### Checkpointing
- Save every 5 results
- Prevents data loss on quota exceeded
- Allows resume from last checkpoint

### Error Handling
- Catch quota exceeded errors
- Save progress before exiting
- Log all errors for review

### Quota Tracking
```python
# Track API usage
api_calls_made = 0
api_calls_limit = 200

if api_calls_made >= api_calls_limit * 0.9:  # 90% threshold
    print("⚠️  Approaching quota limit")
```

## Cost Analysis

### Free Tier (Current)
- **Cost**: $0
- **Time**: 1 day (waiting for quota reset)
- **Effort**: Low (automated script)
- **Risk**: None

### Paid Tier (Alternative)
- **Cost**: $0.0014 (~$0.00)
- **Time**: 15 minutes
- **Effort**: Minimal (payment setup)
- **Risk**: None

**Recommendation**: Stick with free tier. The cost savings ($0.0014) is negligible, and the 1-day wait is acceptable for this project phase.

## Success Criteria

✅ All 292 unique regulations processed
✅ Worker + Judge evaluations complete
✅ Results saved with checkpointing
✅ No data loss from quota limits
✅ Complete dataset ready for analysis

## Next Steps After Processing

1. **Quality Review**: Analyze Judge scores and flagged interpretations
2. **Refinement**: Identify patterns in low-scoring interpretations
3. **Iteration**: Update prompts if needed and re-process flagged items
4. **Production**: Deploy refined prompts to production system
5. **Monitoring**: Track interpretation quality in production

## Appendix: API Quota Details

### Gemini 2.0 Flash Free Tier
- **Requests per day (RPD)**: 200
- **Requests per minute (RPM)**: 10
- **Tokens per minute (TPM)**: 1,000,000
- **Tokens per day (TPD)**: 50,000,000

### Our Usage
- **Average tokens per request**: ~500 (Worker) + ~800 (Judge) = 1,300
- **Total tokens for 140 calls**: 140 × 1,300 = 182,000 tokens
- **Percentage of daily limit**: 182,000 / 50,000,000 = 0.36%

**Conclusion**: We're well within all limits. Token usage is negligible (0.36% of daily limit).