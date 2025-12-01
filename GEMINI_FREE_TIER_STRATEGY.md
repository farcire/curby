# Gemini 2.0 Flash Free Tier Strategy

## Free Tier Limits (December 2024)

Based on [Google AI Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-2.0-flash):

| Limit Type | Free Tier | Our Usage | Status |
|------------|-----------|-----------|--------|
| **Requests per Minute (RPM)** | 10 | 10 (with 6s delays) | ✅ |
| **Requests per Day (RPD)** | 1,500 | 500 | ✅ |
| **Tokens per Minute (TPM)** | 1,000,000 | ~5,000 | ✅ |
| **Tokens per Day (TPD)** | 4,000,000 | ~250,000 | ✅ |

## Processing Strategy for 500 Unique Regulations

### Rate Limiting Configuration

```python
import google.generativeai as genai
import time
from datetime import datetime

# Configure gemini-2.0-flash-exp
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# FREE TIER RATE LIMITS
RATE_LIMIT_RPM = 10      # Requests per minute
RATE_LIMIT_RPD = 1500    # Requests per day
DELAY_BETWEEN_CALLS = 6  # seconds (ensures 10 RPM compliance)

# Token tracking
total_tokens_used = 0
requests_today = 0
```

### Processing Timeline

**Single Day Processing:**
- Total regulations: 500
- Delay per request: 6 seconds
- Total time: 500 × 6 = 3,000 seconds = **50 minutes**
- Total cost: **$0.00** (within free tier)

### Implementation with Rate Limiting

```python
async def process_with_rate_limiting(unique_regulations: List[Dict]):
    """Process regulations while respecting free tier limits."""
    
    results = []
    start_time = time.time()
    
    for i, reg in enumerate(unique_regulations, 1):
        # Check if we're approaching daily limit
        if i > RATE_LIMIT_RPD:
            print(f"⚠️ Approaching daily limit. Processed {i-1} regulations.")
            print(f"Resume tomorrow to process remaining {len(unique_regulations) - i + 1}")
            break
        
        # Process regulation
        try:
            # Worker interpretation
            worker_result = await call_worker_llm(reg)
            
            # Judge evaluation
            judge_result = await call_judge_llm(reg, worker_result)
            
            results.append({
                'unique_id': reg['unique_id'],
                'worker_output': worker_result,
                'judge_evaluation': judge_result
            })
            
            # Progress update
            elapsed = time.time() - start_time
            remaining = len(unique_regulations) - i
            eta_seconds = remaining * DELAY_BETWEEN_CALLS
            
            print(f"✅ Processed {i}/{len(unique_regulations)} "
                  f"({i/len(unique_regulations)*100:.1f}%) "
                  f"| ETA: {eta_seconds//60:.0f}m {eta_seconds%60:.0f}s")
            
            # Rate limiting delay (except for last request)
            if i < len(unique_regulations):
                time.sleep(DELAY_BETWEEN_CALLS)
                
        except Exception as e:
            print(f"❌ Error processing regulation {i}: {e}")
            # Continue with next regulation
            continue
    
    return results
```

### Token Usage Estimation

**Per Regulation:**
- Input tokens (regulation fields): ~200 tokens
- Output tokens (interpretation): ~300 tokens
- Total per regulation: ~500 tokens

**Total for 500 Regulations:**
- Total tokens: 500 × 500 = 250,000 tokens
- TPM usage: ~5,000 tokens/minute (well under 1M limit)
- TPD usage: 250,000 tokens (well under 4M limit)

### Safety Margins

To ensure we stay within limits:

1. **RPM Safety:** 6-second delays guarantee max 10 RPM
2. **RPD Safety:** 500 requests << 1,500 limit (67% margin)
3. **TPM Safety:** 5K tokens/min << 1M limit (99.5% margin)
4. **TPD Safety:** 250K tokens << 4M limit (93.75% margin)

## Cost Comparison

### Our Approach (Free Tier)
- Processing time: 50 minutes
- Total cost: **$0.00**
- Ongoing cost: **$0.00** (dumb pipe lookups)

### Alternative (Paid Tier)
- Processing time: 5 minutes (no rate limits)
- One-time cost: ~$0.10
- Ongoing cost: **$0.00** (dumb pipe lookups)

### Alternative (Runtime Processing)
- Processing time: Real-time per user
- One-time cost: $0.00
- Ongoing cost: **$60-$60,000/month** (scales with users)

## Implementation Checklist

- [ ] Configure gemini-2.0-flash-exp API key
- [ ] Implement 6-second delay between requests
- [ ] Add progress tracking with ETA
- [ ] Add token usage monitoring
- [ ] Add daily limit checking
- [ ] Test with 10 regulations first
- [ ] Run full batch of 500 regulations
- [ ] Verify $0.00 cost in Google Cloud Console

## Monitoring During Processing

```python
# Track metrics during processing
metrics = {
    'start_time': datetime.now(),
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'total_tokens': 0,
    'average_tokens_per_request': 0
}

# Log every 50 requests
if i % 50 == 0:
    print(f"\n📊 Progress Report:")
    print(f"  Processed: {metrics['successful_requests']}/{metrics['total_requests']}")
    print(f"  Success rate: {metrics['successful_requests']/metrics['total_requests']*100:.1f}%")
    print(f"  Tokens used: {metrics['total_tokens']:,}")
    print(f"  Avg tokens/request: {metrics['average_tokens_per_request']:.0f}")
```

## Error Handling

```python
# Retry logic for rate limit errors
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds

for attempt in range(MAX_RETRIES):
    try:
        result = model.generate_content(prompt)
        break
    except Exception as e:
        if "quota" in str(e).lower() or "rate" in str(e).lower():
            if attempt < MAX_RETRIES - 1:
                print(f"⚠️ Rate limit hit. Waiting {RETRY_DELAY}s before retry...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"❌ Max retries reached. Stopping.")
                raise
        else:
            raise
```

## Resume Capability

If processing is interrupted:

```python
# Save progress after each batch
CHECKPOINT_INTERVAL = 50

if i % CHECKPOINT_INTERVAL == 0:
    save_checkpoint({
        'last_processed_index': i,
        'results': results,
        'timestamp': datetime.now().isoformat()
    })

# Resume from checkpoint
def resume_processing(checkpoint_file):
    checkpoint = load_checkpoint(checkpoint_file)
    start_index = checkpoint['last_processed_index']
    previous_results = checkpoint['results']
    
    # Continue from where we left off
    remaining = unique_regulations[start_index:]
    new_results = process_with_rate_limiting(remaining)
    
    return previous_results + new_results
```

## Summary

**Key Advantages:**
- ✅ Zero cost ($0.00)
- ✅ Completes in 50 minutes
- ✅ Safe margins on all limits
- ✅ Automatic rate limiting
- ✅ Progress tracking
- ✅ Resume capability

**Next Steps:**
1. Implement rate-limited processing script
2. Test with 10 regulations
3. Run full batch of 500
4. Verify free tier compliance
5. Celebrate $0.00 cost! 🎉