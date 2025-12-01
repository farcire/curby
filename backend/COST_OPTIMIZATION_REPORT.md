# LLM Cost Optimization & Architectural Strategy

## 1. The Core Question: Ingestion vs. Runtime Processing

**Question:** Is applying LLM at data ingestion more cost effective than at runtime?

**Answer:** **YES, EXPONENTIALLY SO.**

For a map-based application like yours, processing at **Ingestion** is the only viable economic model for a free product.

### The Mathematical Comparison

**Assumptions:**
*   **Total Parking Regulations (Dataset hi6h-neyh):** ~7,783 records (based on recent logs).
*   **Daily Active Users:** 1,000 users.
*   **Segments Viewed per User:** 20 segments.
*   **LLM Cost:** ~$0.0001 per interpretation (using Gemini Flash).

#### Scenario A: Runtime Processing (On-the-Fly)
In this model, the API calls the LLM every time a user requests a blockface that hasn't been cached recently.
*   **Daily Calls:** 1,000 users × 20 segments = **20,000 calls/day**.
*   **Monthly Calls:** 600,000 calls.
*   **Estimated Cost:** ~$60.00 / month (and rising with every new user).
*   **Performance:** Slow. Users wait ~1-2 seconds for the map to load while the LLM thinks.

#### Scenario B: Ingestion Processing (Pre-Computation)
In this model (your current architecture), you process the dataset once and save the result to the database.
*   **One-Time Calls:** ~7,800 regulations.
*   **Daily Calls:** 0 (Users just read static text from MongoDB).
*   **Monthly Calls:** 0 (unless you re-ingest data).
*   **Estimated Cost:** **$0.78 (One-time)**.
*   **Performance:** Instant. milliseconds to load from DB.

**Verdict:** Processing at ingestion decouples your costs from your success. If you get 1 million users tomorrow, your LLM bill remains $0.

---

## 2. Model Selection for Free/Low-Cost Constraints

Since you are optimizing for a free product, we need a model that offers a generous **Free Tier** or extremely low tokens pricing.

| Model | Provider | Input Cost / 1M | Output Cost / 1M | Free Tier? | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Gemini 1.5 Flash** | Google | **$0.075** | **$0.30** | **Yes** (1,500 req/day) | **⭐ WINNER** |
| **GPT-4o-mini** | OpenAI | $0.150 | $0.60 | No | Reliable, but paid. |
| **Llama 3 (Groq)** | Groq | ~$0.05 | ~$0.10 | Limited | Fast, but rate limits vary. |
| **Claude 3 Haiku** | Anthropic | $0.25 | $1.25 | No | Too expensive for this task. |

**Why Gemini 1.5 Flash?**
1.  **Free Tier:** You can interpret 1,500 regulations per day for free.
    *   **Total Regulations:** ~7,800.
    *   **Strategy:** You can ingest your entire database in **5-6 days** for **$0** by running the script in batches (1,500/day).
2.  **Paid Tier:** Even if you pay to do it all at once, the cost is trivial (~$0.80).

---

## 3. Recommended Optimization Roadmap

### Phase 1: Robust Caching (Immediate)
Currently, if your ingestion script crashes, you lose your progress.
*   **Action:** Modify `RestrictionInterpreter` to use a persistent JSON file cache (`interpretation_cache.json`) or check MongoDB before calling the LLM.
*   **Impact:** Re-running the script becomes free and instant for already-processed regulations.

### Phase 2: "Deterministic First" Hybrid Approach
Many regulations are simple standard formats (e.g., "Mon-Fri 8am-6pm").
*   **Action:** Write a simple Regex parser for standard strings.
*   **Logic:** `Regex Parser` -> if fail -> `LLM`.
*   **Impact:** Reduces LLM calls by potentially 50-80%, making the pipeline even faster and cheaper.

### Phase 3: Rate-Limited Ingestion
To stay strictly within the **Free Tier**, you must manage the rate limit (15 RPM for free Gemini).
*   **Action:** Keep the retry logic we implemented (exponential backoff) or cap the script to process only 1 record every 4 seconds.

---

## 4. Conclusion

Your current architecture (**Ingestion-based**) is the correct choice. Moving to Runtime processing would be a financial mistake.

**Next Immediate Step:**
Stick with **Gemini 1.5 Flash** and implement **Persistent Caching** to ensure efficient processing of the ~7,800 records.