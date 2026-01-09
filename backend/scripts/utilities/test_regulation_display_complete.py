"""
Comprehensive Test Suite for Regulation Display Formatting
===========================================================

Tests all regulation types with standardized exception suffixes.

Date: December 31, 2024
Status: Complete test coverage for all regulation types
"""

import pytest
from regulation_normalizer import RuleDisplayFormatter


class TestRuleDisplayFormatter:
    """Test suite for RuleDisplayFormatter with all regulation types"""
    
    # ========================================================================
    # STREET CLEANING TESTS
    # ========================================================================
    
    def test_street_cleaning_basic(self):
        """Test basic street cleaning display"""
        rule = {
            'type': 'street-sweeping',
            'displayDays': 'Th',
            'startTimeMin': 0,
            'endTimeMin': 360,
            'regulation': 'Street Sweeping'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "Street Cleaning Th 12am-6am"
    
    def test_street_cleaning_weekday(self):
        """Test street cleaning with weekday"""
        rule = {
            'type': 'street-sweeping',
            'displayDays': 'M',
            'startTimeMin': 480,
            'endTimeMin': 600,
            'regulation': 'Street Sweeping'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "Street Cleaning M 8am-10am"
    
    # ========================================================================
    # TIME-LIMITED PARKING TESTS
    # ========================================================================
    
    def test_time_limit_with_rpp(self):
        """Test time limit with RPP exception - standardized suffix"""
        rule = {
            'type': 'time-limit',
            'displayDays': 'Weekdays',
            'displayDuration': '2hr',
            'startTimeMin': 480,
            'endTimeMin': 1080,
            'permitArea': 'W',
            'regulation': 'Time limited'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "2hr limit Weekdays 8am-6pm except permit"
    
    def test_time_limit_without_rpp(self):
        """Test time limit without RPP - no suffix"""
        rule = {
            'type': 'time-limit',
            'displayDays': 'M-F',
            'displayDuration': '4hr',
            'startTimeMin': 420,
            'endTimeMin': 1080,
            'regulation': 'Time limited'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "4hr limit M-F 7am-6pm"
    
    def test_time_limit_government_permit(self):
        """Test time limit with government permit - standardized suffix"""
        rule = {
            'type': 'time-limit',
            'displayDays': 'Weekdays',
            'displayDuration': '2hr',
            'startTimeMin': 480,
            'endTimeMin': 1080,
            'regulation': 'Government permit',
            'exceptions': 'Government permit holders exempt'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "2hr limit Weekdays 8am-6pm except government permit"
    
    def test_time_limit_all_day(self):
        """Test time limit without time restriction"""
        rule = {
            'type': 'time-limit',
            'displayDays': 'Daily',
            'displayDuration': '2hr',
            'permitArea': 'X',
            'regulation': 'Time limited'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "2hr limit Daily except permit"
    
    # ========================================================================
    # NO PARKING TESTS
    # ========================================================================
    
    def test_no_parking_any_time(self):
        """Test no parking any time - no days/time"""
        rule = {
            'type': 'no-parking',
            'regulation': 'No parking any time'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "No Parking"
    
    def test_no_parking_with_time(self):
        """Test no parking with time restriction"""
        rule = {
            'type': 'no-parking',
            'displayDays': 'M-Su',
            'startTimeMin': 180,
            'endTimeMin': 360,
            'regulation': 'Limited No Parking'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "No Parking M-Su 3am-6am"
    
    def test_no_parking_with_permit_exception(self):
        """Test no parking with permit exception - standardized suffix"""
        rule = {
            'type': 'no-parking',
            'displayDays': 'M-F',
            'startTimeMin': 480,
            'endTimeMin': 1080,
            'permitArea': 'Y',
            'regulation': 'Limited No Parking',
            'exceptions': 'RPP holders are exempt'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "No Parking M-F 8am-6pm except permit"
    
    def test_no_parking_overnight(self):
        """Test no overnight parking"""
        rule = {
            'type': 'no-parking',
            'displayDays': 'M, Th',
            'startTimeMin': 0,
            'endTimeMin': 240,
            'regulation': 'No overnight parking'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "No Parking M, Th 12am-4am"
    
    def test_no_parking_time_only(self):
        """Test no parking with time but no days"""
        rule = {
            'type': 'no-parking',
            'startTimeMin': 1080,
            'endTimeMin': 360,
            'regulation': 'No overnight parking'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "No Parking 6pm-6am"
    
    # ========================================================================
    # OVERSIZED VEHICLE TESTS
    # ========================================================================
    
    def test_oversized_vehicle(self):
        """Test oversized vehicle restriction - informational only"""
        rule = {
            'type': 'oversized-vehicle',
            'regulation': 'No oversized vehicles'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "No oversized vehicles"
    
    # ========================================================================
    # METERED PARKING TESTS
    # ========================================================================
    
    def test_meter_with_limit(self):
        """Test metered parking with time limit"""
        rule = {
            'type': 'metered',
            'displayDays': 'M-Sa',
            'displayDuration': '2hr',
            'startTimeMin': 540,
            'endTimeMin': 1080,
            'rate': '4.00',
            'regulation': 'Metered parking'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "2hr Meter M-Sa 9am-6pm ($4.00/hr)"
    
    def test_meter_without_limit(self):
        """Test metered parking without time limit"""
        rule = {
            'type': 'metered',
            'displayDays': 'M-Sa',
            'displayDuration': 'No',
            'startTimeMin': 540,
            'endTimeMin': 1080,
            'rate': '4.00',
            'regulation': 'Metered parking'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "Meter M-Sa 9am-6pm ($4.00/hr)"
    
    def test_meter_different_rate(self):
        """Test metered parking with different rate"""
        rule = {
            'type': 'metered',
            'displayDays': 'Weekdays',
            'displayDuration': '4hr',
            'startTimeMin': 480,
            'endTimeMin': 1080,
            'rate': '2.50',
            'regulation': 'Metered parking'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "4hr Meter Weekdays 8am-6pm ($2.50/hr)"
    
    # ========================================================================
    # SKIP TESTS (Paid/Pay + Permit)
    # ========================================================================
    
    def test_skip_paid_permit(self):
        """Test that Paid + Permit regulations are skipped"""
        rule = {
            'type': 'time-limit',
            'regulation': 'Paid + Permit',
            'displayDays': 'M-F',
            'displayDuration': '2hr'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result is None
    
    def test_skip_pay_or_permit(self):
        """Test that Pay or Permit regulations are skipped"""
        rule = {
            'type': 'time-limit',
            'regulation': 'Pay or Permit',
            'displayDays': 'M-F',
            'displayDuration': '2hr'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result is None
    
    # ========================================================================
    # RPP ZONE TESTS
    # ========================================================================
    
    def test_skip_standalone_rpp(self):
        """Test that standalone RPP zones are skipped"""
        rule = {
            'type': 'rpp-zone',
            'permitArea': 'W',
            'regulation': 'RPP Area W'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result is None
    
    # ========================================================================
    # TOW-AWAY TESTS
    # ========================================================================
    
    def test_tow_away_zone(self):
        """Test tow-away zone display"""
        rule = {
            'type': 'tow-away',
            'displayDays': 'M-F',
            'startTimeMin': 480,
            'endTimeMin': 1080,
            'regulation': 'Tow-away zone'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "Tow-Away Zone M-F 8am-6pm"
    
    # ========================================================================
    # EXCEPTION SUFFIX TESTS
    # ========================================================================
    
    def test_exception_suffix_rpp_area(self):
        """Test exception suffix with RPP area"""
        rule = {
            'type': 'time-limit',
            'permitArea': 'W',
            'regulation': 'Time limited'
        }
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == "except permit"
    
    def test_exception_suffix_government(self):
        """Test exception suffix with government permit"""
        rule = {
            'type': 'time-limit',
            'regulation': 'Government permit',
            'exceptions': 'Government permit holders exempt'
        }
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == "except government permit"
    
    def test_exception_suffix_rpp_exception_text(self):
        """Test exception suffix with RPP exception text"""
        rule = {
            'type': 'time-limit',
            'regulation': 'Time limited',
            'exceptions': 'RPP holders are exempt from time limits'
        }
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == "except permit"
    
    def test_exception_suffix_none(self):
        """Test no exception suffix when not applicable"""
        rule = {
            'type': 'time-limit',
            'regulation': 'Time limited',
            'exceptions': 'None. Regulation applies to all vehicles.'
        }
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == ""
    
    # ========================================================================
    # EDGE CASES
    # ========================================================================
    
    def test_time_range_midnight(self):
        """Test time range crossing midnight"""
        rule = {
            'type': 'no-parking',
            'displayDays': 'Daily',
            'startTimeMin': 1320,  # 10pm
            'endTimeMin': 360,     # 6am
            'regulation': 'No overnight parking'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "No Parking Daily 10pm-6am"
    
    def test_time_with_minutes(self):
        """Test time display with minutes"""
        rule = {
            'type': 'street-sweeping',
            'displayDays': 'Tu',
            'startTimeMin': 510,  # 8:30am
            'endTimeMin': 630,    # 10:30am
            'regulation': 'Street Sweeping'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "Street Cleaning Tu 8:30am-10:30am"
    
    def test_fallback_regulation_text(self):
        """Test fallback to regulation text for unknown types"""
        rule = {
            'type': 'unknown-type',
            'regulation': 'Special Regulation'
        }
        result = RuleDisplayFormatter.format_rule_display_text(rule)
        assert result == "Special Regulation"


class TestExceptionSuffixLogic:
    """Detailed tests for exception suffix determination"""
    
    def test_rpp_area1(self):
        """Test RPP detection via rpparea1"""
        rule = {'rpparea1': 'W', 'regulation': 'Time limited'}
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == "except permit"
    
    def test_rpp_area2(self):
        """Test RPP detection via rpparea2"""
        rule = {'rpparea2': 'X', 'regulation': 'Time limited'}
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == "except permit"
    
    def test_rpp_area3(self):
        """Test RPP detection via rpparea3"""
        rule = {'rpparea3': 'Y', 'regulation': 'Time limited'}
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == "except permit"
    
    def test_permit_area(self):
        """Test RPP detection via permitArea"""
        rule = {'permitArea': 'Z', 'regulation': 'Time limited'}
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == "except permit"
    
    def test_government_in_regulation(self):
        """Test government permit detection in regulation text"""
        rule = {'regulation': 'Government permit only'}
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == "except government permit"
    
    def test_government_in_exceptions(self):
        """Test government permit detection in exceptions"""
        rule = {
            'regulation': 'Time limited',
            'exceptions': 'Government permit holders exempt'
        }
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == "except government permit"
    
    def test_permit_in_details(self):
        """Test permit detection in regdetails"""
        rule = {
            'regulation': 'Limited No Parking',
            'regdetails': 'Portuguese Consulate permit holders exempt'
        }
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == "except permit"
    
    def test_no_exception_applies_to_all(self):
        """Test no suffix when regulation applies to all"""
        rule = {
            'regulation': 'Time limited',
            'exceptions': 'None. Regulation applies to all vehicles.'
        }
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == ""
    
    def test_no_exception_blank(self):
        """Test no suffix when exceptions field is blank"""
        rule = {'regulation': 'Time limited', 'exceptions': ''}
        suffix = RuleDisplayFormatter._get_exception_suffix(rule)
        assert suffix == ""


if __name__ == '__main__':
    pytest.main([__file__, '-v'])