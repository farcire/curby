"""
AI-Powered Restriction Interpretation System

Uses LLMs to interpret and clarify parking restrictions for user-friendly display.
"""

import os
import json
import hashlib
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import anthropic
from functools import lru_cache


class RestrictionInterpreter:
    """
    Interprets parking restrictions using AI to produce clear, user-friendly messages.
    """
    
    def __init__(self, api_key: Optional[str] = None, cache_ttl_days: int = 30):
        """
        Initialize the interpreter.
        
        Args:
            api_key: API key for LLM service (Claude)
            cache_ttl_days: How long to cache interpretations (default 30 days)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("Warning: ANTHROPIC_API_KEY not found in environment variables. Interpretation will use fallback.")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            
        self.cache_ttl_days = cache_ttl_days
        self.cache = {}  # In-memory cache (could be Redis in production)
    
    def _generate_cache_key(self, restriction_data: Dict) -> str:
        """Generate a unique cache key for a restriction."""
        # Create a stable string representation
        # Filter out None values to ensure consistency
        clean_data = {k: v for k, v in restriction_data.items() if v is not None}
        stable_str = json.dumps(clean_data, sort_keys=True)
        return hashlib.md5(stable_str.encode()).hexdigest()
    
    def _get_cached_interpretation(self, cache_key: str) -> Optional[Dict]:
        """Retrieve cached interpretation if available and not expired."""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cached_time = cached_data.get("cached_at")
            
            if cached_time:
                age = datetime.utcnow() - datetime.fromisoformat(cached_time)
                if age.days < self.cache_ttl_days:
                    return cached_data.get("interpretation")
        
        return None
    
    def _cache_interpretation(self, cache_key: str, interpretation: Dict):
        """Cache an interpretation."""
        self.cache[cache_key] = {
            "interpretation": interpretation,
            "cached_at": datetime.utcnow().isoformat()
        }
    
    def interpret_restriction(
        self,
        regulation_text: str,
        restriction_type: Optional[str] = None,
        time_limit_minutes: Optional[int] = None,
        days: Optional[str] = None,
        hours: Optional[str] = None,
        permit_area: Optional[str] = None,
        additional_context: Optional[Dict] = None
    ) -> Dict:
        """
        Interpret a parking restriction using AI.
        
        Args:
            regulation_text: The raw regulation text
            restriction_type: Type of restriction (e.g., "time-limit", "no-parking")
            time_limit_minutes: Time limit in minutes if applicable
            days: Days when restriction applies
            hours: Hours when restriction applies
            permit_area: Permit area if applicable
            additional_context: Any additional context
        
        Returns:
            Dictionary with interpreted restriction:
            {
                "type": "tow-away" | "no-parking" | "time-limit" | ...,
                "logic": {...},
                "conditions": {...},
                "display": {...}
            }
        """
        # Build restriction data
        restriction_data = {
            "regulation": regulation_text,
            "type": restriction_type,
            "time_limit_minutes": time_limit_minutes,
            "days": days,
            "hours": hours,
            "permit_area": permit_area,
            "additional_context": additional_context
        }
        
        # Check cache
        cache_key = self._generate_cache_key(restriction_data)
        cached = self._get_cached_interpretation(cache_key)
        if cached:
            return cached
        
        # If no client (no API key), use fallback immediately
        if not self.client:
            return self._fallback_interpretation(restriction_data)
        
        # Build prompt
        prompt = self._build_interpretation_prompt(restriction_data)
        
        # Call LLM
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=self._get_system_prompt(),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            # Extract JSON from the text response
            response_text = response.content[0].text
            
            # Find JSON block if wrapped in markdown
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
                
            interpretation = json.loads(json_str)
            
            # Validate and enhance
            interpretation = self._validate_interpretation(interpretation, restriction_data)
            
            # Cache result
            self._cache_interpretation(cache_key, interpretation)
            
            return interpretation
            
        except Exception as e:
            print(f"Error interpreting restriction: {e}")
            # Return fallback interpretation
            return self._fallback_interpretation(restriction_data)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return """You are a Parking Regulation Compiler for San Francisco. Your goal is NOT just to summarize, but to EXTRACT LOGIC into a structured format that a rule engine can execute.

Input: Raw parking regulation text (often ambiguous or technical).
Output: A JSON object representing the logic, conditions, and user-friendly display text.

Guidelines:
1. Identify the TYPE of rule (tow-away, no-parking, time-limit, etc.).
2. Extract LOGIC: standard time ranges (days/hours) and specific conditions.
3. Extract CONDITIONS: vehicle size limits, permit exceptions, user classes.
4. Generate DISPLAY text: concise summary and clear details.
5. Normalize days (0=Sunday, 1=Monday... 6=Saturday) and times (24h format HH:MM).
6. IMPORTANT: Return ONLY valid JSON, no other text.

Output Format (JSON):
{
  "type": "tow-away" | "no-parking" | "time-limit" | "meter" | "street-sweeping" | "restricted-vehicle",
  "logic": {
    "time_ranges": [
      {
        "days": [1, 2, 3, 4, 5], // Mon-Fri
        "start": "09:00",
        "end": "18:00"
      }
    ],
    "duration_minutes": 120 // if applicable
  },
  "conditions": {
    "min_vehicle_size": { "length": 22, "height": 7 }, // if applicable
    "permit_exception": ["W", "S"], // list of permit areas that are exempt
    "user_class": "commercial" | "commuter" // inferred context
  },
  "display": {
    "summary": "No Oversized Vehicles",
    "details": "Vehicles over 22ft long or 7ft tall prohibited.",
    "severity": "high", // critical, high, medium, low
    "icon": "no-truck"
  }
}"""
    
    def _build_interpretation_prompt(self, restriction_data: Dict) -> str:
        """Build the interpretation prompt."""
        # Convert data to string for prompt
        clean_data = {k: v for k, v in restriction_data.items() if v is not None}
        
        return f"""Compile this parking restriction into structured logic:

Input Data:
{json.dumps(clean_data, indent=2)}

Provide your compilation in the specified JSON format."""
    
    def _validate_interpretation(self, interpretation: Dict, original_data: Dict) -> Dict:
        """Validate and enhance the interpretation."""
        # Ensure required fields
        if "type" not in interpretation:
            interpretation["type"] = "unknown"
        
        if "display" not in interpretation:
            interpretation["display"] = {
                "summary": original_data.get("regulation", "Parking restriction"),
                "details": "Details unavailable",
                "severity": "medium",
                "icon": "info"
            }
        
        if "logic" not in interpretation:
            interpretation["logic"] = {}
            
        if "conditions" not in interpretation:
            interpretation["conditions"] = {}
        
        # Add metadata
        interpretation["meta"] = {
            "interpreted_at": datetime.utcnow().isoformat(),
            "original_text": original_data.get("regulation"),
            "model": "claude-3-5-sonnet"
        }
        
        return interpretation
    
    def _fallback_interpretation(self, restriction_data: Dict) -> Dict:
        """Provide a fallback interpretation if AI fails."""
        return {
            "type": "unknown",
            "display": {
                "summary": restriction_data.get("regulation", "Parking restriction applies"),
                "details": "Unable to fully interpret this restriction. Please check signage.",
                "severity": "medium",
                "icon": "info"
            },
            "logic": {},
            "conditions": {},
            "meta": {
                "interpreted_at": datetime.utcnow().isoformat(),
                "original_text": restriction_data.get("regulation"),
                "fallback": True
            }
        }
    
    def batch_interpret_restrictions(
        self,
        restrictions: List[Dict]
    ) -> List[Dict]:
        """
        Interpret multiple restrictions in batch.
        
        Args:
            restrictions: List of restriction dictionaries
        
        Returns:
            List of interpreted restrictions
        """
        interpreted = []
        
        for restriction in restrictions:
            try:
                result = self.interpret_restriction(
                    regulation_text=restriction.get("regulation", ""),
                    restriction_type=restriction.get("type"),
                    time_limit_minutes=restriction.get("time_limit_minutes"),
                    days=restriction.get("days"),
                    hours=restriction.get("hours"),
                    permit_area=restriction.get("permit_area"),
                    additional_context=restriction.get("additional_context")
                )
                interpreted.append(result)
            except Exception as e:
                print(f"Error interpreting restriction: {e}")
                interpreted.append(self._fallback_interpretation(restriction))
        
        return interpreted