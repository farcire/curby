import json
import os
import time
from typing import List, Dict
from restriction_interpreter import RestrictionInterpreter
from restriction_judge import RestrictionJudge
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_evaluation():
    """
    Runs the evaluation pipeline on the test set.
    """
    # file paths
    test_set_path = 'backend/test_set_regulations.json'
    results_path = 'backend/evaluation_results.json'
    
    if not os.path.exists(test_set_path):
        print(f"Error: Test set not found at {test_set_path}")
        # Try absolute path or relative to root if running from different cwd
        if os.path.exists(os.path.join(os.getcwd(), test_set_path)):
             test_set_path = os.path.join(os.getcwd(), test_set_path)
        else:
             return

    # Load test set
    try:
        with open(test_set_path, 'r') as f:
            test_cases = json.load(f)
    except Exception as e:
        print(f"Error loading test set: {e}")
        return
    
    print(f"Loaded {len(test_cases)} test cases.")

    # Initialize agents
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        print("Please set GEMINI_API_KEY in your .env file.")
        return

    print("Initializing Interpreter and Judge...")
    interpreter = RestrictionInterpreter(api_key=api_key)
    judge = RestrictionJudge(api_key=api_key)

    results = []
    passed_count = 0
    total_score = 0

    print("\nStarting evaluation...")
    print("-" * 60)

    for i, case in enumerate(test_cases):
        print(f"Processing case {i+1}/{len(test_cases)}: {case['id']}")
        
        original_text = case['regulation_text']
        original_data = case.get('original_data', {})
        
        # 1. Interpret
        start_time = time.time()
        try:
            # We extract some context from original_data if available to pass as hints
            # But main input is regulation_text
            # Extract structured fields
            hr_limit = original_data.get('hrlimit')
            try:
                time_limit_minutes = int(float(hr_limit) * 60) if hr_limit and str(hr_limit).lower() != 'nan' and float(hr_limit) > 0 else None
            except (ValueError, TypeError):
                time_limit_minutes = None

            interpretation = interpreter.interpret_restriction(
                regulation_text=original_text,
                days=original_data.get('days'),
                hours=original_data.get('hours'),
                time_limit_minutes=time_limit_minutes,
                permit_area=original_data.get('rpparea1'),
                additional_context=original_data
            )
        except Exception as e:
            print(f"  Error during interpretation: {e}")
            interpretation = {"error": str(e), "type": "error"}

        # 2. Judge
        try:
            evaluation = judge.evaluate(original_text, interpretation, original_data)
        except Exception as e:
            print(f"  Error during evaluation: {e}")
            evaluation = {"score": 0, "reasoning": f"Evaluation error: {str(e)}", "flagged": True}

        duration = time.time() - start_time
        
        # Metrics
        score = evaluation.get('score', 0)
        total_score += score
        if score >= 0.9:
            passed_count += 1
            status = "PASS"
        else:
            status = "FAIL"
            
        print(f"  Result: {status} (Score: {score})")
        print(f"  Reasoning: {evaluation.get('reasoning', 'No reasoning provided')}")
        
        # Store result
        results.append({
            "test_case_id": case['id'],
            "original_text": original_text,
            "interpretation": interpretation,
            "evaluation": evaluation,
            "duration_seconds": round(duration, 2)
        })

    # Calculate statistics
    avg_score = total_score / len(test_cases) if test_cases else 0
    pass_rate = (passed_count / len(test_cases)) * 100 if test_cases else 0

    summary = {
        "total_cases": len(test_cases),
        "passed_count": passed_count,
        "pass_rate": pass_rate,
        "average_score": avg_score,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": "gemini-2.0-flash"
    }

    final_output = {
        "summary": summary,
        "results": results
    }

    # Save results
    try:
        with open(results_path, 'w') as f:
            json.dump(final_output, f, indent=2)
    except Exception as e:
        print(f"Error saving results: {e}")

    print("-" * 60)
    print("Evaluation Complete")
    print(f"Pass Rate: {pass_rate:.1f}% ({passed_count}/{len(test_cases)})")
    print(f"Average Score: {avg_score:.2f}")
    print(f"Results saved to {results_path}")

if __name__ == "__main__":
    run_evaluation()