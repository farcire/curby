"""
Restriction Judge System

Evaluates the accuracy and safety of AI-interpreted parking restrictions.
"""

import os
import json
import google.generativeai as genai
from typing import Dict, Optional

class RestrictionJudge:
    """
    Evaluates interpreted restrictions against original text using an LLM Judge.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found. Judge will not function.")
            self.client = None
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")

    def evaluate(self, original_text: str, interpretation: Dict) -> Dict:
        """
        Evaluate a single interpretation.
        
        Args:
            original_text: The raw regulation text
            interpretation: The JSON output from the Worker
            
        Returns:
            Dict containing score, reasoning, and flag status
        """
        if not self.api_key:
            return {"score": 0.0, "reasoning": "No API key available for Judge", "flagged": True}

        prompt = self._build_judge_prompt(original_text, interpretation)
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            return self._parse_judge_response(response_text)
            
        except Exception as e:
            print(f"Error in Judge evaluation: {e}")
            return {"score": 0.0, "reasoning": f"Evaluation error: {str(e)}", "flagged": True}

    def _build_judge_prompt(self, original_text: str, interpretation: Dict) -> str:
        """
        Constructs the prompt for the Judge LLM.
        """
        # Clean up interpretation for the prompt to avoid noise
        clean_interpretation = {k: v for k, v in interpretation.items() if k != "meta"}
        
        return f"""You are an expert Parking Regulation Auditor for the SFMTA.
Your goal is to EVALUATE the accuracy and safety of AI-generated parking regulation interpretations.

INPUT:
1. "original_text": The raw regulation string.
2. "interpretation": The structured JSON object produced by the Worker.

OUTPUT:
A JSON object:
{{
  "score": 0.0 to 1.0,
  "reasoning": "Explanation of the score",
  "flagged": true/false
}}

SCORING RUBRIC:

[CRITICAL SAFETY ERRORS] -> Score: 0.0 (Flagged: true)
- FALSE PERMISSION: Interpretation says "allowed" when text says "prohibited" or "tow away".
- TOW AWAY OMISSION: Text mentions "Tow Away" but interpretation misses it.
- TIME WINDOW EXPANSION: Interpretation ends earlier or starts later than the rule (creating a false safe zone).
  * Example: Rule "7-9AM" -> Interp "7-8AM". (User parks at 8:30 -> Towed).

[ACCURACY ERRORS] -> Score: 0.5 (Flagged: true)
- TEMPORAL MISMATCH: Interpretation is over-cautious or wrong but safe.
  * Example: Rule "Mon-Fri" -> Interp "Mon-Sat". (User loses parking spot, but no tow).
- HALLUCINATION: Inventing exceptions/permits not in text.
- CONFLICT: Summary contradicts structured data.

[MINOR OMISSIONS] -> Score: 0.8 (Flagged: false - pass with warning)
- Formatting issues.
- Missing rare exceptions (e.g. "Diplomatic Corps").
- Vague summary.

[PERFECT] -> Score: 1.0 (Flagged: false)
- Accurate capture of rule, time, days, and exceptions.
- Severity matches risk level.

INSTRUCTIONS:
- You must prioritize SAFETY (avoiding towing/ticketing) above all else.
- If there is ANY doubt about a safety-critical discrepancy (risk of tow/ticket), score 0.0.
- Check time ranges meticulously. "07:00-09:00" is NOT the same as "07:00-08:00".
- Respond ONLY with the JSON object.

---
DATA TO EVALUATE:

original_text: "{original_text}"

interpretation:
{json.dumps(clean_interpretation, indent=2)}
"""

    def _parse_judge_response(self, response_text: str) -> Dict:
        """
        Parses the JSON response from the Judge.
        """
        try:
            # Extract JSON if wrapped in markdown
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
                
            return json.loads(json_str)
        except Exception as e:
            print(f"Error parsing Judge response: {e}")
            print(f"Raw response: {response_text}")
            return {"score": 0.0, "reasoning": "Failed to parse Judge response", "flagged": True}