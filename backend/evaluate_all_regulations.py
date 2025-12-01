import os
import asyncio
import json
import time
from dotenv import load_dotenv
import motor.motor_asyncio
from restriction_judge import RestrictionJudge
from datetime import datetime

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI not found in .env file.")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
try:
    db = client.get_default_database()
except Exception:
    db = client["curby"]

# Initialize Judge
judge = RestrictionJudge()

async def evaluate_all_interpretations():
    """
    1. Fetch all cached interpretations.
    2. Find a representative objectID for each pattern.
    3. Run the Judge.
    4. Save comprehensive report.
    """
    print("Starting comprehensive evaluation...")
    
    # Fetch all interpretations
    cursor = db.regulation_interpretations.find({})
    interpretations = await cursor.to_list(length=None)
    
    print(f"Found {len(interpretations)} unique interpretation patterns to evaluate.")
    
    results = []
    processed_count = 0
    
    for doc in interpretations:
        original_data = doc.get("original_data", {})
        interpretation = doc.get("interpretation", {})
        
        # 1. Find representative ObjectID
        # We search for one parking regulation that matches this pattern
        # Match on the key fields used for deduplication
        match_query = {
            "regulation": original_data.get("regulation"),
            "regdetails": original_data.get("regdetails"),
            "days": original_data.get("days"),
            "hours": original_data.get("hours")
        }
        
        # Handle cases where value is None in original_data but might be missing or null in DB
        # Ideally the process_interpretations script cleaned this up, but let's be robust.
        # Actually, let's just query. If strict match fails, we might just report "N/A".
        
        representative = await db.parking_regulations.find_one(match_query)
        object_id = representative.get("objectid") if representative else "N/A"
        
        # Construct raw text for Judge
        regulation_text = f"{original_data.get('regulation', '')} {original_data.get('regdetails', '')}".strip()
        
        # 2. Run Judge
        print(f"[{processed_count+1}/{len(interpretations)}] Evaluating Object ID: {object_id}...")
        
        try:
            evaluation = judge.evaluate(
                original_text=regulation_text,
                interpretation=interpretation,
                original_data=original_data
            )
            
            # Simple rate limiting protection (Judge also has retries, but this helps)
            time.sleep(2) 
            
        except Exception as e:
            print(f"Error evaluating: {e}")
            evaluation = {
                "score": 0.0,
                "reasoning": f"Evaluation script error: {str(e)}",
                "flagged": True
            }

        # 3. Compile Result
        result_entry = {
            "object_id": object_id,
            "original_fields": original_data,
            "worker_interpretation": interpretation,
            "judge_evaluation": evaluation,
            "evaluated_at": datetime.utcnow().isoformat()
        }
        
        results.append(result_entry)
        processed_count += 1
        
        # Periodic save to avoid data loss on long runs
        if processed_count % 10 == 0:
            with open('backend/comprehensive_evaluation_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Saved progress ({processed_count} records).")

    # Final Save
    with open('backend/comprehensive_evaluation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
        
    print("-" * 60)
    print("Evaluation Complete")
    print(f"Total Evaluated: {len(results)}")
    print(f"Report saved to backend/comprehensive_evaluation_results.json")

    # Calculate summary stats
    total_score = sum(r['judge_evaluation'].get('score', 0) for r in results)
    avg_score = total_score / len(results) if results else 0
    pass_count = sum(1 for r in results if r['judge_evaluation'].get('score', 0) >= 0.9)
    
    print(f"Average Judge Score: {avg_score:.2f}")
    print(f"Pass Rate (Score >= 0.9): {pass_count}/{len(results)} ({pass_count/len(results)*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(evaluate_all_interpretations())