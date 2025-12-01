import os
import asyncio
import json
from dotenv import load_dotenv
import motor.motor_asyncio
from restriction_interpreter import RestrictionInterpreter
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

# Initialize Interpreter
interpreter = RestrictionInterpreter()

async def process_unique_regulations():
    """
    1. Scan 'parking_regulations' collection for unique text patterns.
    2. Check 'regulation_interpretations' collection for existing interpretation.
    3. If missing, call LLM and save result.
    """
    print("Starting interpretation processing...")
    
    # 1. Aggregation to find unique patterns
    pipeline = [
        {
            "$group": {
                "_id": {
                    "regulation": "$regulation",
                    "regdetails": "$regdetails",
                    "days": "$days",
                    "hours": "$hours",
                    "hrlimit": "$hrlimit",
                    "rpparea1": "$rpparea1",
                    "exceptions": "$exceptions"
                },
                "count": {"$sum": 1}
            }
        }
    ]
    
    print("Aggregating unique regulations...")
    unique_patterns = []
    async for doc in db.parking_regulations.aggregate(pipeline):
        pattern = doc["_id"]
        # Create a deterministic hash/key for this pattern
        # We can use the JSON dump as the key if normalized, or just query by fields
        unique_patterns.append(pattern)
        
    print(f"Found {len(unique_patterns)} unique regulation patterns.")
    
    # 2. Process each pattern
    processed = 0
    skipped = 0
    errors = 0
    
    for pattern in unique_patterns:
        try:
            # Check if exists in interpretations collection
            # We use the exact fields as the unique key
            existing = await db.regulation_interpretations.find_one({
                "original_data.regulation": pattern.get("regulation"),
                "original_data.regdetails": pattern.get("regdetails"),
                "original_data.days": pattern.get("days"),
                "original_data.hours": pattern.get("hours")
            })
            
            if existing:
                skipped += 1
                continue
                
            # If not exists, Interpret
            print(f"Interpreting: {pattern.get('regulation')}...")
            
            # Prepare data for interpreter
            # Clean up NaN/None
            clean_pattern = {k: (v if str(v).lower() != 'nan' else None) for k, v in pattern.items()}
            
            # Extract time limit
            hr_limit = clean_pattern.get('hrlimit')
            time_limit_minutes = None
            try:
                if hr_limit and float(hr_limit) > 0:
                    time_limit_minutes = int(float(hr_limit) * 60)
            except:
                pass

            interpretation = interpreter.interpret_restriction(
                regulation_text=f"{clean_pattern.get('regulation', '')} {clean_pattern.get('regdetails', '')}".strip(),
                days=clean_pattern.get('days'),
                hours=clean_pattern.get('hours'),
                time_limit_minutes=time_limit_minutes,
                permit_area=clean_pattern.get('rpparea1'),
                additional_context=clean_pattern
            )
            
            # Save to DB
            doc = {
                "original_data": clean_pattern,
                "interpretation": interpretation,
                "created_at": datetime.utcnow(),
                "model_version": "gemini-2.0-flash"
            }
            
            await db.regulation_interpretations.insert_one(doc)
            processed += 1
            
            # Simple rate limiting (1.5s delay to be safe for 15 RPM free tier if running serially)
            await asyncio.sleep(4.0)
            
        except Exception as e:
            print(f"Error processing pattern {pattern}: {e}")
            errors += 1
            
    print(f"\nProcessing Complete.")
    print(f"New Interpretations: {processed}")
    print(f"Skipped (Already Cached): {skipped}")
    print(f"Errors: {errors}")

async def apply_interpretations_to_segments():
    """
    Apply cached interpretations to the street_segments collection.
    
    HYBRID RULES ARCHITECTURE:
    A single street segment (CNN) can have a mix of rule types:
    
    1. DETERMINISTIC (Native Processing):
       - Street Sweeping: Stored in 'rules' array with type='street-sweeping'. Ignored here.
       - Metered Parking: Stored in separate 'schedules' array. Ignored here.
       
    2. GENERATIVE (LLM Processing):
       - Parking Regulations: Stored in 'rules' array. Targeted by this function.
    
    This function uses MongoDB's arrayFilters ($[elem]) to specifically target ONLY
    the matching parking regulation items within the rules list, leaving street
    sweeping and meters completely matching/untouched.
    """
    print("\nStarting application of interpretations to segments...")
    
    # Fetch all interpretations
    cursor = db.regulation_interpretations.find({})
    
    total_updated = 0
    patterns_processed = 0
    
    async for doc in cursor:
        patterns_processed += 1
        original = doc.get("original_data", {})
        interpretation = doc.get("interpretation", {})
        
        # Criteria to find documents that contain this specific regulation rule
        match_query = {
            "rules": {
                "$elemMatch": {
                    "regulation": original.get("regulation"),
                    "details": original.get("regdetails"),
                    "days": original.get("days"),
                    "hours": original.get("hours")
                }
            }
        }
        
        # Update operation: Only adds 'interpretation' field to the specific matching rule object
        update_query = {
            "$set": {
                "rules.$[elem].interpretation": interpretation
            }
        }
        
        # Array filter ensures we only update the specific array item that matches this regulation
        array_filters = [
            {
                "elem.regulation": original.get("regulation"),
                "elem.details": original.get("regdetails"),
                "elem.days": original.get("days"),
                "elem.hours": original.get("hours")
            }
        ]
        
        try:
            result = await db.street_segments.update_many(
                match_query,
                update_query,
                array_filters=array_filters
            )
            total_updated += result.modified_count
            
            if patterns_processed % 100 == 0:
                print(f"Processed {patterns_processed} patterns. Updated {total_updated} segments so far...")
                
        except Exception as e:
            print(f"Error updating segments for pattern {original.get('regulation')}: {e}")

    print(f"Application Complete.")
    print(f"Total Patterns Applied: {patterns_processed}")
    print(f"Total Segment Rules Updated: {total_updated}")

async def main():
    # 1. Process unique regulations (Ingest -> Interpretations)
    await process_unique_regulations()
    
    # 2. Apply to segments (Interpretations -> Street Segments)
    await apply_interpretations_to_segments()

if __name__ == "__main__":
    asyncio.run(main())