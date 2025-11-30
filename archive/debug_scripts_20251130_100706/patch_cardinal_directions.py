import asyncio
import os
import motor.motor_asyncio
from dotenv import load_dotenv
from typing import Dict, List
import re
import sys
import datetime
import traceback

# Setup logging
LOG_FILE = "patch_debug.log"

def log(msg):
    timestamp = datetime.datetime.now().isoformat()
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"Failed to write to log file: {e}")

# Clear log file
with open(LOG_FILE, "w") as f:
    f.write(f"Script initialized at {datetime.datetime.now()}\n")

log("Imports started...")

try:
    # Import helper functions from existing modules
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from display_utils import generate_display_messages, format_restriction_description
    from deterministic_parser import _parse_days, parse_time_to_minutes
    log("Imports successful.")
except Exception as e:
    log(f"Import Error: {e}")
    sys.exit(1)

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

def extract_street_limits(sweeping_schedule: Dict) -> tuple:
    """Extract FROM/TO street names from sweeping schedule limits."""
    limits = sweeping_schedule.get("limits", "")
    if not limits or "-" not in limits:
        return (None, None)
    
    parts = limits.split("-")
    if len(parts) == 2:
        from_street = parts[0].strip()
        to_street = parts[1].strip()
        return (from_street, to_street)
    
    return (None, None)

async def patch_cardinal_directions():
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        log("Error: MONGODB_URI not set")
        return

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client.curby
    
    log("Starting cardinal direction patch...")
    
    # 1. Fetch all street cleaning schedules
    log("Fetching street cleaning schedules from DB...")
    cursor = db.street_cleaning_schedules.find({})
    schedules = await cursor.to_list(length=None)
    log(f"Loaded {len(schedules)} cleaning schedules.")
    
    # Build lookup map: (cnn_str, side) -> list of schedule docs
    schedules_map = {}
    for sched in schedules:
        raw_cnn = sched.get("cnn", "")
        cnn = str(raw_cnn).strip()
        # Clean side: ensure it's just 'L' or 'R'
        raw_side = sched.get("cnnrightleft", "")
        side = str(raw_side).strip().upper()
        
        if cnn and side:
            key = (cnn, side)
            if key not in schedules_map:
                schedules_map[key] = []
            schedules_map[key].append(sched)
            
    # 2. Iterate over all segments and update
    log("Fetching all street segments...")
    cursor = db.street_segments.find({})
    
    updated_count = 0
    processed_count = 0
    
    async for segment in cursor:
        processed_count += 1
        if processed_count % 5000 == 0:
            log(f"Processed {processed_count} segments...")
            
        cnn = str(segment.get("cnn", "")).strip()
        side = str(segment.get("side", "")).strip().upper()
        
        if not cnn or not side:
            continue
            
        # Find matching schedules
        key = (cnn, side)
        matched_schedules = schedules_map.get(key, [])
        
        if not matched_schedules:
            continue
            
        # Re-build street sweeping rules
        # First, remove existing street-sweeping rules to avoid duplicates/stale data
        current_rules = [r for r in segment.get("rules", []) if r.get("type") != "street-sweeping"]
        
        # Add fresh rules from matched schedules
        new_sweeping_rules = []
        cardinal = None
        from_street = segment.get("fromStreet")
        to_street = segment.get("toStreet")
        
        for row in matched_schedules:
            f_st, t_st = extract_street_limits(row)
            if not from_street and f_st:
                from_street = f_st
            if not to_street and t_st:
                to_street = t_st
                
            active_days = _parse_days(row.get("weekday"))
            start_min = parse_time_to_minutes(row.get("fromhour"))
            end_min = parse_time_to_minutes(row.get("tohour"))
            
            description = format_restriction_description(
                "street-sweeping",
                day=row.get("weekday"),
                start_time=row.get("fromhour"),
                end_time=row.get("tohour")
            )
            
            # Capture blockside and handle float/nan types safely
            current_blockside = row.get("blockside")
            safe_cardinal = None
            if current_blockside:
                # Ensure string and handle stringified 'nan' or 'none'
                cardinal_str = str(current_blockside).strip()
                if cardinal_str.lower() not in ['nan', 'none', 'null', '']:
                    safe_cardinal = cardinal_str
                    cardinal = safe_cardinal # Update segment-level cardinal

            new_sweeping_rules.append({
                "type": "street-sweeping",
                "day": row.get("weekday"),
                "startTime": row.get("fromhour"),
                "endTime": row.get("tohour"),
                "activeDays": active_days,
                "startTimeMin": start_min,
                "endTimeMin": end_min,
                "description": description,
                "blockside": safe_cardinal, # Use sanitized value
                "side": side,
                "limits": row.get("limits")
            })
            
        # Update segment fields
        current_rules.extend(new_sweeping_rules)
        segment["rules"] = current_rules
        segment["cardinalDirection"] = cardinal
        if from_street:
            segment["fromStreet"] = from_street
        if to_street:
            segment["toStreet"] = to_street
            
        # Regenerate display messages with new info
        parity = None
        if segment.get("fromAddress"):
            try:
                addr_num = int(re.sub(r'\D', '', str(segment["fromAddress"])))
                parity = "even" if addr_num % 2 == 0 else "odd"
            except:
                pass

        try:
            msgs = generate_display_messages(
                street_name=segment.get("streetName", ""),
                side_code=segment.get("side", ""),
                cardinal_direction=cardinal, # Safely passed now
                from_address=segment.get("fromAddress"),
                to_address=segment.get("toAddress"),
                address_parity=parity
            )
            
            segment["displayName"] = msgs["display_name"]
            segment["displayNameShort"] = msgs["display_name_short"]
            segment["displayAddressRange"] = msgs["display_address_range"]
            segment["displayCardinal"] = msgs["display_cardinal"]
            
            # Save updates
            await db.street_segments.replace_one({"_id": segment["_id"]}, segment)
            updated_count += 1
            
            if cnn == "13766000":
                log(f"DEBUG: Updated 13766000 {side}. New Cardinal: {cardinal}")
                
        except Exception as e:
            log(f"Error processing segment {cnn} {side}: {e}")
            # traceback.print_exc() # detailed trace if needed
        
    log(f"✓ Patch complete. Updated {updated_count} segments.")
    client.close()

if __name__ == "__main__":
    asyncio.run(patch_cardinal_directions())