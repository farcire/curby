"""
Rule Engine - Business Logic for Parking Rules
===============================================

Handles:
- Cap color normalization and blockface aggregation
- Meter schedule priority and selection
- TOW schedule aggregation (FIXED: uses 'schedules' not 'base_schedules')
- Rule filtering (72hr RPP, etc.)
- Manual override integration

This module contains ONLY business logic - no parsing, no display formatting.

Usage:
    from rule_engine import (
        normalize_cap_color,
        aggregate_blockface_cap_colors,
        prioritize_meter_schedules,
        aggregate_blockface_tow_schedules
    )
"""

from typing import List, Dict, Any, Optional


# ============================================================================
# CAP COLOR NORMALIZATION (Meter Vehicle Restrictions)
# ============================================================================

class CapColorNormalizer:
    """
    Normalize meter cap colors to standardized vehicle restrictions.
    
    Complete Cap Color Legend (Dec 31, 2024):
    - BLACK = Motorcycle only
    - BROWN = Tour Bus only
    - GREY = General parking (Curby users eligible)
    - GREEN = General parking (Curby users eligible)
    - PURPLE = Boat Trailer only
    - RED = Commercial Vehicles 6+ wheels
    - YELLOW = Commercial Vehicle
    
    For Curby Users (standard cars): Only GREY and GREEN are eligible
    """
    
    CAR_ELIGIBLE_COLORS = {'GREY', 'GRAY', 'GREEN', 'GRN'}
    MOTORCYCLE_COLORS = {'BLACK', 'BLK'}
    TOUR_BUS_COLORS = {'BROWN', 'BRN'}
    BOAT_TRAILER_COLORS = {'PURPLE', 'PRP', 'PURP'}
    COMMERCIAL_COLORS = {'YELLOW', 'YLW', 'RED'}
    
    @classmethod
    def normalize(cls, cap_color: Any) -> Dict[str, Any]:
        """
        Normalize a single meter cap color.
        
        Returns:
            {
                'canonical': {
                    'color': str,
                    'restriction': str,
                    'is_restricted': bool,
                    'vehicle_type': str
                },
                'display': {
                    'restriction_text': str,
                    'user_eligible': bool
                }
            }
        """
        # Handle None, empty, or NaN
        if not cap_color or str(cap_color).upper().strip() in ('', 'NAN', 'NONE', 'NULL'):
            return {
                'canonical': {
                    'color': 'GREY',
                    'restriction': 'GENERAL',
                    'is_restricted': False,
                    'vehicle_type': 'Standard vehicles'
                },
                'display': {
                    'restriction_text': 'General parking',
                    'user_eligible': True
                }
            }
        
        cap_upper = str(cap_color).upper().strip()
        
        # GREY or GREEN = General parking
        if cap_upper in cls.CAR_ELIGIBLE_COLORS:
            return {
                'canonical': {
                    'color': cap_upper,
                    'restriction': 'GENERAL',
                    'is_restricted': False,
                    'vehicle_type': 'Standard vehicles'
                },
                'display': {
                    'restriction_text': 'General parking',
                    'user_eligible': True
                }
            }
        
        # BLACK = Motorcycle only
        if cap_upper in cls.MOTORCYCLE_COLORS:
            return {
                'canonical': {
                    'color': 'BLACK',
                    'restriction': 'MOTORCYCLE',
                    'is_restricted': True,
                    'vehicle_type': 'Motorcycle'
                },
                'display': {
                    'restriction_text': 'Motorcycle only',
                    'user_eligible': False
                }
            }
        
        # BROWN = Tour Bus only
        if cap_upper in cls.TOUR_BUS_COLORS:
            return {
                'canonical': {
                    'color': 'BROWN',
                    'restriction': 'TOUR_BUS',
                    'is_restricted': True,
                    'vehicle_type': 'Tour Bus'
                },
                'display': {
                    'restriction_text': 'Tour Bus only',
                    'user_eligible': False
                }
            }
        
        # PURPLE = Boat Trailer only
        if cap_upper in cls.BOAT_TRAILER_COLORS:
            return {
                'canonical': {
                    'color': 'PURPLE',
                    'restriction': 'BOAT_TRAILER',
                    'is_restricted': True,
                    'vehicle_type': 'Boat Trailer'
                },
                'display': {
                    'restriction_text': 'Boat Trailer only',
                    'user_eligible': False
                }
            }
        
        # YELLOW or RED = Commercial
        if cap_upper in cls.COMMERCIAL_COLORS:
            text = 'Commercial Vehicles 6+ wheels' if cap_upper == 'RED' else 'Commercial Vehicle'
            return {
                'canonical': {
                    'color': cap_upper,
                    'restriction': 'COMMERCIAL',
                    'is_restricted': True,
                    'vehicle_type': 'Commercial'
                },
                'display': {
                    'restriction_text': text,
                    'user_eligible': False
                }
            }
        
        # Unknown - default to general but flag
        return {
            'canonical': {
                'color': cap_upper,
                'restriction': 'UNKNOWN',
                'is_restricted': False,
                'vehicle_type': 'Unknown'
            },
            'display': {
                'restriction_text': f'Unknown: {cap_upper}',
                'user_eligible': True
            }
        }
    
    @classmethod
    def aggregate_blockface(cls, meters: List[Dict]) -> Dict[str, Any]:
        """
        Aggregate cap colors at blockface level using majority rule.
        
        Rules:
        - All meters eligible → Block eligible
        - Majority eligible → Block eligible
        - Majority ineligible → Block ineligible
        """
        if not meters:
            return {
                'is_restricted': False,
                'restriction_type': 'NONE',
                'eligible_meter_count': 0,
                'ineligible_meter_count': 0,
                'meter_count': 0,
                'majority_rule': 'NONE',
                'eligible_for_curby_user': False,
                'display_text': 'No meters',
                'display_restriction': None
            }
        
        eligible_count = 0
        ineligible_count = 0
        restriction_types = {}
        
        for meter in meters:
            cap = meter.get('cap_color')
            normalized = cls.normalize(cap)
            
            if normalized['display']['user_eligible']:
                eligible_count += 1
            else:
                ineligible_count += 1
                rtype = normalized['canonical']['restriction']
                restriction_types[rtype] = restriction_types.get(rtype, 0) + 1
        
        total = len(meters)
        
        # Determine eligibility
        if eligible_count == total:
            rule = 'ALL_ELIGIBLE'
            eligible = True
            text = f"All {total} meters: General parking"
            restriction = None
        elif eligible_count > ineligible_count:
            rule = 'MAJORITY_ELIGIBLE'
            eligible = True
            text = f"Majority ({eligible_count}/{total}) general parking"
            restriction = None
        elif ineligible_count == total:
            rule = 'ALL_INELIGIBLE'
            eligible = False
            main_type = max(restriction_types, key=restriction_types.get)
            text = f"All {total} meters: {main_type} only"
            restriction = main_type
        else:
            rule = 'MAJORITY_INELIGIBLE'
            eligible = False
            main_type = max(restriction_types, key=restriction_types.get)
            text = f"Majority ({ineligible_count}/{total}) restricted"
            restriction = main_type
        
        return {
            'is_restricted': ineligible_count > 0,
            'restriction_type': restriction or 'GENERAL',
            'eligible_meter_count': eligible_count,
            'ineligible_meter_count': ineligible_count,
            'meter_count': total,
            'majority_rule': rule,
            'eligible_for_curby_user': eligible,
            'restriction_breakdown': restriction_types,
            'display_text': text,
            'display_restriction': restriction
        }


# ============================================================================
# METER SCHEDULE PRIORITY AND SELECTION
# ============================================================================

class MeterScheduleSelector:
    """
    Select effective meter schedule based on priority hierarchy.
    
    Priority: TOW > ALTERNATE > OP > PRE+FREE
    
    CRITICAL FIX: Database stores schedules in meter['schedules'], not meter['base_schedules']
    Schedule types in database use title case: 'Tow', 'Alternate', 'Operating Schedule'
    """
    
    SCHEDULE_PRIORITY = {
        'Tow': 1,                    # Database uses title case
        'TOW': 1,                    # Legacy support
        'Alternate': 2,
        'ALTERNATE': 2,
        'Operating Schedule': 3,
        'OP': 3,
        'Pre': 4,                    # Same priority as Free
        'PRE': 4,
        'Free': 4,
        'FREE': 4
    }
    
    @classmethod
    def prioritize(cls, schedules: List[Dict]) -> List[Dict]:
        """
        Sort meter schedules by priority (TOW > ALTERNATE > OP > PRE+FREE).
        
        Returns:
            Sorted list with highest priority first
        """
        if not schedules:
            return []
        
        return sorted(
            schedules,
            key=lambda s: cls.SCHEDULE_PRIORITY.get(s.get('schedule_type', 'OP'), 99)
        )
    
    @classmethod
    def aggregate_blockface_tow(cls, meters: List[Dict]) -> Dict[str, Any]:
        """
        Aggregate TOW schedules at blockface level with majority rule.
        
        CRITICAL FIX: Uses meter.get('schedules', []) not meter.get('base_schedules', [])
        CRITICAL FIX: Checks schedule.get('schedule_type') == 'Tow' (title case)
        
        Rules:
        - All meters have TOW → Check for overlap
        - Majority have TOW → Use majority rule
        - Mixed → Use majority rule
        """
        if not meters:
            return {
                'has_tow': False,
                'all_have_tow': False,
                'tow_schedules': [],
                'meters_with_tow': 0,
                'meters_without_tow': 0,
                'majority_rule': 'OPERATING',
                'blockface_rule': 'NO_TOW',
                'display_text': 'No meters on this block'
            }
        
        all_tow_schedules = []
        meters_with_tow = 0
        meters_without_tow = 0
        
        for meter in meters:
            meter_has_tow = False
            # CRITICAL FIX: Use 'schedules' not 'base_schedules'
            for schedule in meter.get('schedules', []):
                # CRITICAL FIX: Check for 'Tow' (title case) not 'TOW'
                if schedule.get('schedule_type') == 'Tow':
                    meter_has_tow = True
                    all_tow_schedules.append({
                        'days_applied': schedule.get('days_applied'),
                        'from_time': schedule.get('from_time'),
                        'to_time': schedule.get('to_time')
                    })
            
            if meter_has_tow:
                meters_with_tow += 1
            else:
                meters_without_tow += 1
        
        total_meters = len(meters)
        all_have_tow = (meters_with_tow == total_meters)
        
        # Determine majority rule
        if meters_with_tow > meters_without_tow:
            majority_rule = 'TOW'
            majority_text = f"Majority ({meters_with_tow}/{total_meters}) have tow-away"
        else:
            majority_rule = 'OPERATING'
            majority_text = f"Majority ({meters_without_tow}/{total_meters}) are operating"
        
        # Determine blockface rule
        if all_have_tow:
            blockface_rule = 'ALL_TOW'
            display_text = f"All {total_meters} meters have tow-away schedules"
        elif majority_rule == 'TOW':
            blockface_rule = 'MAJORITY_TOW'
            display_text = majority_text
        else:
            blockface_rule = 'MAJORITY_OPERATING'
            display_text = majority_text
        
        return {
            'has_tow': meters_with_tow > 0,
            'all_have_tow': all_have_tow,
            'tow_schedules': all_tow_schedules,
            'meters_with_tow': meters_with_tow,
            'meters_without_tow': meters_without_tow,
            'majority_rule': majority_rule,
            'blockface_rule': blockface_rule,
            'display_text': display_text
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def normalize_cap_color(cap_color: Any) -> Dict[str, Any]:
    """Normalize a single cap color."""
    return CapColorNormalizer.normalize(cap_color)


def aggregate_blockface_cap_colors(meters: List[Dict]) -> Dict[str, Any]:
    """Aggregate cap colors at blockface level."""
    return CapColorNormalizer.aggregate_blockface(meters)


def prioritize_meter_schedules(schedules: List[Dict]) -> List[Dict]:
    """Sort meter schedules by priority (TOW > ALTERNATE > OP > PRE+FREE)."""
    return MeterScheduleSelector.prioritize(schedules)


def aggregate_blockface_tow_schedules(meters: List[Dict]) -> Dict[str, Any]:
    """
    Aggregate TOW schedules at blockface level.
    
    CRITICAL FIX: Uses meter['schedules'] not meter['base_schedules']
    CRITICAL FIX: Checks for 'Tow' (title case) not 'TOW'
    """
    return MeterScheduleSelector.aggregate_blockface_tow(meters)