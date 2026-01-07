#!/usr/bin/env python3
"""
Generate Interpretation Layer for Street Segments

This script creates the 'interpretation' array in street_segments that contains:
1. Business logic from rule_engine.py (cap colors, schedule priority, TOW aggregation)
2. Manual overrides from manual_data_overrides.json
3. Display formatting from regulation_normalizer.py
4. UX-ready presentation from RuleDisplayFormatter

The interpretation array is the FINAL processed output ready for frontend consumption.
Raw data remains in rules/schedules/meters arrays for reference and reprocessing.

Architecture:
- Input: Raw rules[], schedules[], meters[] arrays
- Processing: Apply business rules + manual overrides + formatting
- Output: interpretation[] array with complete UX-ready data
"""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any
from datetime import datetime

# Import business logic modules
from src.core.regulation_normalizer import (
    normalize_regulation,
    format_rule_for_modal,
    sort_rules_for_modal,
    calculate_next_restriction,
    format_segment_for_modal
)
from rule_engine import (
    normalize_cap_color,
    aggregate_blockface_cap_colors,
    prioritize_meter_schedules,
    aggregate_blockface_tow_schedules
)
from apply_manual_overrides import load_manual_overrides

load_dotenv()

class InterpretationGenerator:
    """Generate interpretation layer with all business logic applied"""
    
    def __init__(self):
        self.manual_overrides = load_manual_overrides()
    
    def generate_interpretation(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete interpretation for a segment.
        
        Returns:
            {
                'version': '1.0.0',
                'generated_at': ISO timestamp,
                'parking_status': {...},  # Overall status
                'rules_display': [...],   # Formatted rules for modal
                'meter_info': {...},      # Meter aggregation with business logic
                'next_restriction': {...}, # Next upcoming prohibition
                'manual_overrides_applied': [...],  # List of override IDs applied
                'location_display': {...}  # Formatted location text
            }
        """
        # Store segment for access in helper methods
        self.segment = segment
        
        rules = segment.get('rules', [])
        schedules = segment.get('schedules', [])
        meters = segment.get('meters', [])
        
        # 1. Apply manual overrides (check if any apply to this segment)
        overrides_applied = self._check_manual_overrides(segment)
        
        # 2. Generate parking status
        parking_status = self._generate_parking_status(rules, meters)
        
        # 3. Format rules AND meter schedules for display (with business logic)
        rules_display = self._format_rules_display(rules, schedules, meters)
        
        # 4. Aggregate meter information (cap colors, schedules, TOW)
        meter_info = self._aggregate_meter_info(meters)
        
        # 5. Calculate next restriction
        next_restriction = calculate_next_restriction(rules)
        
        # 6. Format location display
        location_display = self._format_location_display(segment)
        
        return {
            'version': '1.0.0',
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'parking_status': parking_status,
            'rules_display': rules_display,
            'meter_info': meter_info,
            'next_restriction': next_restriction,
            'manual_overrides_applied': overrides_applied,
            'location_display': location_display
        }
    
    def _check_manual_overrides(self, segment: Dict[str, Any]) -> List[str]:
        """Check which manual overrides were applied to this segment"""
        applied = []
        
        for rule in segment.get('rules', []):
            if rule.get('source') == 'manual_override':
                override_id = rule.get('override_id')
                if override_id:
                    applied.append(override_id)
        
        return applied
    
    def _generate_parking_status(self, rules: List[Dict], meters: List[Dict]) -> Dict[str, Any]:
        """
        Generate overall parking status with business logic.
        
        Priority (most restrictive first):
        1. No Parking (absolute prohibition)
        2. Tow-Away Zone
        3. Metered (requires payment)
        4. Time Limited
        5. RPP Zone (permit required)
        6. Regulated (other restrictions)
        7. Unrestricted
        """
        has_no_parking = any('no parking' in str(r.get('regulation', '')).lower() for r in rules)
        has_tow = any(r.get('type') == 'tow-away' for r in rules)
        has_meters = len(meters) > 0
        has_time_limit = any(r.get('type') == 'time-limit' for r in rules)
        has_rpp = any(r.get('permitArea') for r in rules)
        has_street_cleaning = any(r.get('type') == 'street-sweeping' for r in rules)
        
        # Determine primary status
        if has_no_parking:
            status = 'no-parking'
            status_text = 'No Parking'
            severity = 'error'
            user_can_park = False
        elif has_tow:
            status = 'tow-away'
            status_text = 'Tow-Away Zone'
            severity = 'error'
            user_can_park = False
        elif has_meters:
            status = 'metered'
            status_text = 'Metered Parking'
            severity = 'info'
            user_can_park = True
        elif has_time_limit:
            status = 'time-limited'
            status_text = 'Time Limited Parking'
            severity = 'warning'
            user_can_park = True
        elif has_rpp:
            status = 'rpp-zone'
            status_text = 'Permit Zone'
            severity = 'warning'
            user_can_park = True
        elif rules:
            status = 'regulated'
            status_text = 'Regulated Parking'
            severity = 'info'
            user_can_park = True
        else:
            status = 'unrestricted'
            status_text = 'Unrestricted Parking'
            severity = 'success'
            user_can_park = True
        
        return {
            'status': status,
            'status_text': status_text,
            'severity': severity,
            'user_can_park': user_can_park,
            'has_meters': has_meters,
            'has_time_limits': has_time_limit,
            'has_street_cleaning': has_street_cleaning,
            'has_rpp': has_rpp,
            'has_tow_away': has_tow,
            'is_unrestricted': not rules and not has_meters
        }
    
    def _format_rules_display(self, rules: List[Dict], schedules: List[Dict] = None, meters: List[Dict] = None) -> List[str]:
        """
        Format rules AND meter schedules for display with business logic applied.
        Aggregates rules of the same type and time into single lines.
        
        Display Rules:
        - TOW schedules: "No Parking [days] [time]" (not "Tow-Away Zone")
        - Meter schedules: "[duration] [vehicle_type] [days] [time]" (NO rates)
          * Vehicle type based on cap color aggregation:
            - COMMERCIAL (Yellow/Red) → "Commercial Meter"
            - GENERAL (Green/Grey/Gray) → "Meter"
            - Other types → "Meter"
        - Sort order: Chronological by time, then by type
        - Special events: Hyperlink "schedule" word to SFMTA URL
        - Conflict Resolution: 24/7 "No Parking" overrides time-limit/RPP rules
        
        Returns array of strings (not objects) for backend API compatibility.
        """
        if not rules and not schedules and not meters:
            return []
        
        # Check for 24/7 "No Parking" rules (no time/day restrictions)
        # These override time-limit and RPP rules since parking is never allowed
        has_247_no_parking = any(
            'no parking' in str(r.get('regulation', '')).lower() and
            r.get('type') == 'no-parking' and
            (not r.get('activeDays') or len(r.get('activeDays', [])) == 0) and
            (not r.get('startTimeMin') or r.get('startTimeMin') == 0) and
            (not r.get('endTimeMin') or r.get('endTimeMin') == 0)
            for r in rules
        )
        
        # Process regular rules first
        formatted = []
        
        if rules:
            # Filter out conflicting rules if 24/7 no-parking exists
            if has_247_no_parking:
                # Keep: no-parking, street-sweeping, tow-away
                # Remove: time-limit, rpp-zone (these conflict with 24/7 no parking)
                filtered_rules = [
                    r for r in rules
                    if r.get('type') in ('no-parking', 'street-sweeping', 'tow-away') or
                       'no parking' in str(r.get('regulation', '')).lower()
                ]
            else:
                filtered_rules = rules
            
            # Sort rules (Monday-first, then by frequency)
            sorted_rules = sort_rules_for_modal(filtered_rules)
        
            # Group rules by type and time for aggregation
            rule_groups = {}
            
            for rule in sorted_rules:
                # Get the formatted display text
                display_text = format_rule_for_modal(rule)
                
                # Skip if None (e.g., standalone RPP zones, paid/permit rules)
                if display_text is None:
                    continue
                
                # Create a grouping key based on type, time, and non-day parts
                rule_type = rule.get('type', '')
                start_time = rule.get('startTimeMin', 0)
                end_time = rule.get('endTimeMin', 0)
                
                # For time-limit rules, include duration and permit info in key
                duration = rule.get('displayDuration', '')
                permit = rule.get('permitArea', '')
                exceptions = rule.get('exceptions', '')
                
                group_key = (rule_type, start_time, end_time, duration, permit, exceptions)
                
                if group_key not in rule_groups:
                    rule_groups[group_key] = {
                        'rules': [],
                        'display_text': display_text
                    }
                
                rule_groups[group_key]['rules'].append(rule)
            
            # Now format each group
            seen = set()
            
            for group_key, group_data in rule_groups.items():
                group_rules = group_data['rules']
                
                # If only one rule in group, use its display text as-is
                if len(group_rules) == 1:
                    display_text = group_data['display_text']
                    if display_text not in seen:
                        seen.add(display_text)
                        formatted.append(display_text)
                    continue
                
                # Multiple rules with same type/time - aggregate days
                # Re-format with combined days
                first_rule = group_rules[0]
                rule_type = first_rule.get('type', '')
                
                # Collect all days from all rules in group
                all_days = []
                for r in group_rules:
                    days = r.get('activeDays', [])
                    all_days.extend(days)
                
                # Remove duplicates and sort
                unique_days = sorted(set(all_days))
                
                # Create a combined rule with all days
                combined_rule = first_rule.copy()
                combined_rule['activeDays'] = unique_days
                
                # Re-calculate displayDays for the combined rule
                # Canonical format: 0=Monday, 1=Tuesday, ..., 6=Sunday
                day_names = ['M', 'Tu', 'W', 'Th', 'F', 'Sa', 'Su']
                if len(unique_days) == 7:
                    combined_rule['displayDays'] = 'Daily'
                elif unique_days == [0, 1, 2, 3, 4]:
                    combined_rule['displayDays'] = 'Weekdays'
                elif unique_days == [0, 1, 2, 3, 4, 5]:
                    combined_rule['displayDays'] = 'M-Sa'
                elif unique_days == [5, 6]:
                    combined_rule['displayDays'] = 'Weekends'
                else:
                    combined_rule['displayDays'] = ', '.join([day_names[d] for d in unique_days])
                
                # Format the combined rule
                display_text = format_rule_for_modal(combined_rule)
                
                if display_text and display_text not in seen:
                    seen.add(display_text)
                    formatted.append(display_text)
        
        # Now add meter schedules and sort everything chronologically
        if meters:
            # Get cap color aggregation for vehicle type determination
            cap_color_agg = aggregate_blockface_cap_colors(meters)
            
            # Extract all schedules from all meters
            all_meter_schedules = []
            for meter in meters:
                all_meter_schedules.extend(meter.get('schedules', []))
            
            meter_displays = self._format_meter_schedules(all_meter_schedules, meters, cap_color_agg)
            formatted.extend(meter_displays)
        
        # Sort by broad type groups, then chronologically within each group
        # This ensures meter rules are grouped together rather than scattered by time
        def get_type_group_and_time(display_text: str) -> tuple:
            """
            Determine type group for display ordering.
            Returns (group_priority, start_time, display_text) for sorting.
            
            Display Order (Broad Type Grouping):
            1. Non-metered regulations (time-limit, RPP, no-parking) - shown first
            2. Meter schedules (ALL meter rules grouped together) - shown second
            3. Street cleaning (absolute prohibition) - shown last
            
            Within each group, rules are sorted chronologically by start time.
            This prevents meter schedules from being scattered throughout the list.
            """
            text_lower = display_text.lower()
            start_time = self._extract_start_time(display_text)
            
            # Group 1: Non-metered regulations (priority 1)
            # Includes: time limits, RPP zones, no parking (non-meter)
            if any(keyword in text_lower for keyword in ['limit', 'permit', 'no parking', 'tow-away']):
                if 'meter' not in text_lower:  # Exclude meter-related
                    return (1, start_time, display_text)
            
            # Group 2: Meter schedules (priority 2)
            # Includes: all meter-related rules (metered, commercial meter, etc.)
            if 'meter' in text_lower or 'commercial meter' in text_lower:
                return (2, start_time, display_text)
            
            # Group 3: Street cleaning (priority 3)
            # Absolute prohibition - shown last for emphasis
            if 'street cleaning' in text_lower or 'cleaning' in text_lower:
                return (3, start_time, display_text)
            
            # Default: treat as non-metered (priority 1)
            return (1, start_time, display_text)
        
        # Sort by: (1) type group, (2) start time within group
        formatted_with_groups = [get_type_group_and_time(text) for text in formatted]
        formatted_with_groups.sort(key=lambda x: (x[0], x[1]))
        
        return [text for _, _, text in formatted_with_groups]
    
    def _extract_start_time(self, display_text: str) -> int:
        """Extract start time in minutes from display text for sorting"""
        import re
        
        # Handle non-string types
        if not isinstance(display_text, str):
            return 0
        
        # Match time patterns like "3am", "12pm", "6:30am"
        time_pattern = r'(\d{1,2})(?::(\d{2}))?(am|pm)'
        match = re.search(time_pattern, display_text.lower())
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            period = match.group(3)
            
            # Convert to 24-hour
            if period == 'pm' and hour < 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            
            return hour * 60 + minute
        return 0  # Default to midnight if no time found
    
    def _format_meter_schedules(self, schedules: List[Dict], meters: List[Dict], cap_color_agg: Dict[str, Any] = None) -> List[str]:
        """
        Format meter schedules as display strings with vehicle type labels and aggregation.
        
        Format Rules:
        - TOW: "No Parking [days] [time]" (not "Tow-Away Zone")
        - Operating: "[duration] [vehicle_type] [days] [time]" (NO rates)
          * Vehicle type based on cap color aggregation:
            - COMMERCIAL (Yellow/Red) → "Commercial Meter"
            - GENERAL (Green/Grey/Gray) → "Meter"
            - Other types → "Meter"
        - Aggregation: Merge schedules with same time limit, vehicle type, and days
          * Takes widest time window when overlapping
        - No schedules: "Check meter for schedule and rate"
        - Special event: "Oracle Park Schedule and Rates may apply. See schedule."
        
        Args:
            schedules: List of meter schedule dicts
            meters: List of meter dicts
            cap_color_agg: Cap color aggregation result from aggregate_blockface_cap_colors()
        
        Returns:
            List of formatted meter schedule strings
        """
        # Check for special event zones first
        in_ballpark = any(m.get('in_ballpark_zone') for m in meters)
        in_arena = any(m.get('in_arena_zone') for m in meters)
        
        # Determine vehicle type label based on cap color aggregation
        vehicle_type = "Meter"  # Default
        if cap_color_agg:
            restriction_type = cap_color_agg.get('restriction_type', 'GENERAL')
            if restriction_type == 'COMMERCIAL':
                vehicle_type = "Commercial Meter"
            # GENERAL and all other types use "Meter"
        
        formatted = []
        seen = set()
        
        # Add special event message if applicable
        if in_ballpark or in_arena:
            if in_ballpark and in_arena:
                zone_name = "Special Event"
            elif in_ballpark:
                zone_name = "Oracle Park"
            else:
                zone_name = "Chase Center"
            
            # Note: Frontend will need to hyperlink the word "schedule"
            special_msg = f"{zone_name} Schedule and Rates may apply. See schedule."
            formatted.append(special_msg)
        
        # Process schedules and track if any are valid
        valid_schedules_found = False
        operating_schedules = []  # Collect for aggregation
        
        for schedule in schedules:
            schedule_type = schedule.get('schedule_type', '')
            
            # Handle TOW schedules - display as "No Parking"
            if schedule_type in ('Tow', 'TOW'):
                days_applied = schedule.get('days_applied')
                from_time = schedule.get('from_time')
                to_time = schedule.get('to_time')
                
                from src.core.regulation_normalizer import parse_days, format_day_display, parse_time_to_minutes
                days = parse_days(days_applied)
                if not days:
                    continue
                
                days_display = format_day_display(days)
                from_min = parse_time_to_minutes(from_time)
                to_min = parse_time_to_minutes(to_time)
                
                if from_min is not None and to_min is not None:
                    from_str = self._format_simple_time(from_min)
                    to_str = self._format_simple_time(to_min)
                    time_range = f"{from_str}-{to_str}"
                    display = f"No Parking {days_display} {time_range}"
                else:
                    display = f"No Parking {days_display}"
                
                if display not in seen:
                    seen.add(display)
                    formatted.append(display)
                continue
            
            # Handle Operating schedules - collect for aggregation
            days_applied = schedule.get('days_applied')
            from_time = schedule.get('from_time')
            to_time = schedule.get('to_time')
            
            # Parse time_limit string (e.g., "30 minutes" → 30)
            time_limit_str = schedule.get('time_limit', '')
            time_limit = None
            if time_limit_str:
                # Extract numeric value from string like "30 minutes" or "240 minutes"
                import re
                match = re.search(r'(\d+)', str(time_limit_str))
                if match:
                    time_limit = int(match.group(1))
            
            from src.core.regulation_normalizer import parse_days, format_day_display, parse_time_to_minutes, format_duration_display
            days = parse_days(days_applied)
            if not days:
                continue
            
            from_min = parse_time_to_minutes(from_time)
            to_min = parse_time_to_minutes(to_time)
            
            if from_min is None or to_min is None:
                continue
            
            # Store schedule for aggregation
            operating_schedules.append({
                'days': days,
                'from_min': from_min,
                'to_min': to_min,
                'time_limit': time_limit
            })
            valid_schedules_found = True
        
        # Aggregate operating schedules by time limit and days
        if operating_schedules:
            aggregated = self._aggregate_meter_schedules(operating_schedules, vehicle_type, in_ballpark, in_arena)
            for display in aggregated:
                if display not in seen:
                    seen.add(display)
                    formatted.append(display)
        
        # If no valid schedules were found, show fallback message
        if not valid_schedules_found:
            from src.core.regulation_normalizer import format_meter_without_schedule
            fallback = format_meter_without_schedule(in_ballpark or in_arena)
            formatted.append(fallback)
        
        return formatted
    
    def _aggregate_meter_schedules(self, schedules: List[Dict], vehicle_type: str,
                                   in_ballpark: bool, in_arena: bool) -> List[str]:
        """
        Aggregate meter schedules with same time limit and days.
        Merges overlapping time windows to show widest range.
        
        Args:
            schedules: List of schedule dicts with days, from_min, to_min, time_limit
            vehicle_type: "Meter" or "Commercial Meter"
            in_ballpark: Whether in special event zone
            in_arena: Whether in special event zone
        
        Returns:
            List of formatted display strings
        """
        from src.core.regulation_normalizer import format_day_display, format_duration_display
        from collections import defaultdict
        
        # Group by (time_limit, days_tuple)
        groups = defaultdict(list)
        for sched in schedules:
            days_tuple = tuple(sorted(sched['days']))
            time_limit = sched.get('time_limit')
            key = (time_limit, days_tuple)
            groups[key].append(sched)
        
        # Format each group
        formatted = []
        for (time_limit, days_tuple), group_scheds in groups.items():
            days = list(days_tuple)
            
            # Find widest time window (earliest start, latest end)
            earliest_start = min(s['from_min'] for s in group_scheds)
            latest_end = max(s['to_min'] for s in group_scheds)
            
            # Format components
            days_display = format_day_display(days)
            from_str = self._format_simple_time(earliest_start)
            to_str = self._format_simple_time(latest_end)
            time_range = f"{from_str}-{to_str}"
            
            # Format duration if present
            duration_text = ""
            if time_limit and time_limit > 0:
                duration_display = format_duration_display(time_limit)
                duration_text = f"{duration_display} "
            
            # Build display string
            suffix = " all other days" if (in_ballpark or in_arena) else ""
            display = f"{duration_text}{vehicle_type} {days_display} {time_range}{suffix}"
            formatted.append(display)
        
        return formatted
    
    def _format_simple_time(self, minutes: int) -> str:
        """Format time in simplified format (9am, 6pm, 12pm)"""
        hours = minutes // 60
        mins = minutes % 60
        
        if hours == 0:
            hour_12 = 12
            period = 'am'
        elif hours < 12:
            hour_12 = hours
            period = 'am'
        elif hours == 12:
            hour_12 = 12
            period = 'pm'
        else:
            hour_12 = hours - 12
            period = 'pm'
        
        # Only show minutes if not on the hour
        if mins == 0:
            return f"{hour_12}{period}"
        else:
            return f"{hour_12}:{mins:02d}{period}"
    
    def _aggregate_meter_info(self, meters: List[Dict]) -> Dict[str, Any]:
        """
        Aggregate meter information with business logic from rule_engine.
        """
        if not meters:
            return {
                'has_meters': False,
                'meter_count': 0
            }
        
        # Apply cap color business logic
        cap_color_agg = aggregate_blockface_cap_colors(meters)
        
        # Apply TOW schedule business logic
        tow_agg = aggregate_blockface_tow_schedules(meters)
        
        # Prioritize schedules and collect all schedules from all meters
        all_schedules = []
        for meter in meters:
            meter_schedules = meter.get('schedules', [])
            prioritized = prioritize_meter_schedules(meter_schedules)
            all_schedules.extend(prioritized)
        
        # Get rate range from all meter schedules
        rates = [s.get('rate_per_hour', 0) for s in all_schedules if s.get('rate_per_hour')]
        rate_range = {
            'min': min(rates) if rates else 0,
            'max': max(rates) if rates else 0,
            'min_formatted': f"${min(rates):.2f}/hr" if rates else "$0.00/hr",
            'max_formatted': f"${max(rates):.2f}/hr" if rates else "$0.00/hr"
        }
        
        return {
            'has_meters': True,
            'meter_count': len(meters),
            'cap_color_aggregation': cap_color_agg,
            'tow_aggregation': tow_agg,
            'rate_range': rate_range,
            'schedule_count': len(all_schedules),
            'eligible_for_standard_car': cap_color_agg.get('eligible_for_curby_user', True)
        }
    
    def _format_location_display(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Format location information for display"""
        street_name = segment.get('street') or segment.get('streetName', 'Unknown Street')
        cardinal = segment.get('cardinalDirection', segment.get('side', ''))
        from_addr = segment.get('fromAddress', '')
        to_addr = segment.get('toAddress', '')
        from_street = segment.get('fromStreet')
        to_street = segment.get('toStreet')
        
        # Format main location text
        if from_addr and to_addr:
            location_text = f"{street_name} ({cardinal}, {from_addr}-{to_addr})"
        else:
            location_text = f"{street_name} ({cardinal})"
        
        # Format cross streets
        if from_street and to_street:
            cross_streets_text = f"{from_street} → {to_street}"
        elif from_street or to_street:
            cross_streets_text = from_street or to_street
        else:
            cross_streets_text = None
        
        return {
            'location_text': location_text,
            'cross_streets_text': cross_streets_text,
            'street_name': street_name,
            'cardinal_direction': cardinal,
            'address_range': f"{from_addr}-{to_addr}" if from_addr and to_addr else None
        }


async def main():
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found")
    
    client = AsyncIOMotorClient(mongodb_uri)
    db = client.curby
    
    print("=" * 80)
    print("GENERATING INTERPRETATION LAYER")
    print("=" * 80)
    
    # Initialize generator
    generator = InterpretationGenerator()
    
    # Get all segments
    print("\n1. Loading street segments...")
    segments = await db.street_segments.find({}).to_list(None)
    print(f"   Found {len(segments)} segments")
    
    # Generate interpretations
    print("\n2. Generating interpretations...")
    updated_count = 0
    
    for idx, segment in enumerate(segments):
        if idx % 1000 == 0:
            print(f"   Progress: {idx}/{len(segments)}")
        
        # Generate interpretation
        interpretation = generator.generate_interpretation(segment)
        
        # Update segment
        await db.street_segments.update_one(
            {"_id": segment["_id"]},
            {"$set": {"interpretation": interpretation}}
        )
        updated_count += 1
    
    print(f"\n✓ Generated interpretations for {updated_count} segments")
    
    # Verify
    print("\n3. Verifying...")
    with_interpretation = await db.street_segments.count_documents({"interpretation": {"$exists": True}})
    
    print(f"   ✓ Segments with interpretation: {with_interpretation}")
    
    # Sample check
    sample = await db.street_segments.find_one({"interpretation": {"$exists": True}})
    if sample:
        interp = sample.get('interpretation', {})
        print(f"\n   Sample interpretation structure:")
        print(f"     - version: {interp.get('version')}")
        print(f"     - parking_status: {interp.get('parking_status', {}).get('status')}")
        print(f"     - rules_display count: {len(interp.get('rules_display', []))}")
        print(f"     - has_meters: {interp.get('meter_info', {}).get('has_meters')}")
        print(f"     - manual_overrides: {len(interp.get('manual_overrides_applied', []))}")
    
    client.close()
    print("\n" + "=" * 80)
    print("✓ INTERPRETATION LAYER COMPLETE!")
    print("=" * 80)
    print("\nThe 'interpretation' array now contains:")
    print("  - Business logic from rule_engine.py")
    print("  - Manual overrides from manual_data_overrides.json")
    print("  - Display formatting from regulation_normalizer.py")
    print("  - UX-ready presentation for frontend")

if __name__ == "__main__":
    asyncio.run(main())