"""
Test script for AI Restriction Interpreter.
Run this to verify that the LLM integration is working correctly.
"""

import os
import json
import sys
from restriction_interpreter import RestrictionInterpreter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_interpreter():
    """Test the restriction interpreter with various cases."""
    
    # Initialize interpreter
    # It will use ANTHROPIC_API_KEY from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n⚠️  WARNING: ANTHROPIC_API_KEY not found in environment.")
        print("Interpreter will use fallback mode (non-AI).")
        print("To test AI features, set ANTHROPIC_API_KEY in .env file.\n")
    
    interpreter = RestrictionInterpreter()
    
    print("=" * 60)
    print("TESTING AI RESTRICTION INTERPRETER")
    print("=" * 60)
    
    # Test case 1: Oversized vehicles (Complex restriction)
    print("\n🔹 Test Case 1: Oversized Vehicles")
    input1 = {
        "regulation_text": "Oversized vehicles and trailers are those longer than 22 feet or taller than 7 feet",
        "restriction_type": "vehicle-restriction"
    }
    print(f"Input: {input1['regulation_text']}")
    
    result1 = interpreter.interpret_restriction(**input1)
    print("Result:")
    print(json.dumps(result1, indent=2))
    
    # Test case 2: Time limit with permit exception (Structured data)
    print("\n🔹 Test Case 2: Time Limit with Exception")
    input2 = {
        "regulation_text": "2 HR PARKING 9AM-6PM MON-SAT EXCEPT PERMIT W",
        "restriction_type": "time-limit",
        "time_limit_minutes": 120,
        "days": "MON-SAT",
        "hours": "9AM-6PM",
        "permit_area": "W"
    }
    print(f"Input: {input2['regulation_text']}")
    
    result2 = interpreter.interpret_restriction(**input2)
    print("Result:")
    print(json.dumps(result2, indent=2))
    
    # Test case 3: No stopping (Critical restriction)
    print("\n🔹 Test Case 3: No Stopping")
    input3 = {
        "regulation_text": "NO STOPPING ANYTIME",
        "restriction_type": "no-stopping"
    }
    print(f"Input: {input3['regulation_text']}")
    
    result3 = interpreter.interpret_restriction(**input3)
    print("Result:")
    print(json.dumps(result3, indent=2))
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_interpreter()