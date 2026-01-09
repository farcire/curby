# Rule Display Centralization Plan

**Date**: December 31, 2024  
**Status**: 📋 PLANNING  
**Goal**: Centralize ALL rule display/formatting logic in regulation_normalizer.py

---

## 🎯 OBJECTIVES

Based on the modal UI requirements:

### 1. **Centralize Rule Display Logic**
- Move ALL rule formatting from frontend to backend
- Single source of truth in [`regulation_normalizer.py`](regulation_normalizer.py)
- Backend pre-computes display strings during ingestion
- Frontend simply renders pre-computed strings

### 2. **Implement Rule Sorting**
**Primary Sort**: Frequency (most common → least common)
- Street Cleaning (most common/important)
- Time-limited parking
- Metered parking
- RPP zones
- Other restrictions

**Secondary Sort**: Monday-first
- Rules containing Monday come before other days
- Within same frequency tier, Monday rules first

### 3. **Add "Next Upcoming Restriction" Calculation**
- Calculate next occurrence of absolute prohibitions (street sweeping, tow-away)
- Pre-compute or provide data for frontend to calculate
- Display format: "Thu 12:00AM" (as shown in mockup)

---

## 📊 CURRENT STATE ANALYSIS

### Frontend Rule Formatting (NEEDS REMOVAL)

**File**: [`frontend/src/utils/ruleFormatter.ts`](frontend/src/utils/ruleFormatter.ts)
- Lines 19-159: `formatRulesForDisplay()` - Complex formatting logic
- Lines 165-189: `formatTimeRange()` - Time formatting
- Lines 199-226: `formatDays()` - Day formatting
- Lines 232-249: `findConsecutiveRanges()` - Day range logic

**File**: [`frontend/src/utils/sfmtaDataFetcher.ts`](frontend/src/utils/sfmtaDataFetcher.ts)
- Lines 181-423: `transformBackendRule()` - Rule transformation and description building
- Lines 237-274: `formatTime()` - Time parsing
- Lines 277-302: `parseHoursField()` - Hours field parsing

**File**: [`frontend/src/components/BlockfaceDetail.tsx`](frontend/src/components/BlockfaceDetail.tsx)
- Lines 46-78: `getNextRestriction()` - Next restriction calculation
- Lines 93: Calls `formatRulesForDisplay()`

**Problem**: Logic is scattered across 3 frontend files with duplicate parsing/formatting

---

## ✅ BACKEND NORMALIZATION (ALREADY EXISTS)

**File**: [`backend/regulation_normalizer.py`](backend/regulation_normalizer.py)
- ✅ Day parsing (lines 54-206)
- ✅ Time parsing (lines 310-471)
- ✅ Duration parsing (lines 537-632)
- ✅ Display formatting (lines 639-929)
- ✅ Complete normalization (lines 722-861)

**What's Missing**:
- ❌ Rule sorting logic
- ❌ Next restriction calculation
- ❌ Complete display string generation for modal

---

## 🏗️ PROPOSED ARCHITECTURE

### Backend: Pre-Compute Everything

```python
# In regulation_normalizer.py - NEW PART 11

class RuleDisplayFormatter:
    """
    Complete rule display formatting for modal UI.
    Pre-computes all display strings during ingestion.
    """
    
    # Frequency-based sorting (most common first)
    RULE_FREQUENCY_ORDER = {
        'street-sweeping': 1,    # Most common/important
        'time-limit': 2,
        'metered': 3,
        'rpp-zone': 4,
        'no-parking': 5,
        'tow-away': 6,
        'parking-regulation': 7  # Least common
    }
    
    @classmethod
    def format_rule_for_modal(cls, rule: Dict) -> Dict:
        """
        Format a single rule for modal display.
        
        Returns:
            {
                'display_text': 'Street Cleaning 12am-6am Thu',
                'sort_priority': 1,
                'has_monday': True,
                'frequency_tier': 1,
                'is_absolute_prohibition': True,
                'next_occurrence': {...}  # For restrictions only
            }
        """
        pass
    
    @classmethod
    def sort_rules_for_display(cls, rules: List[Dict]) -> List[Dict]:
        """
        Sort rules by:
        1. Frequency (most common first)
        2. Monday-first (within same frequency)
        
        Returns sorted list with display_text ready for UI
        """
        pass
    
    @classmethod
    def calculate_next_restriction(cls, rules: List[Dict], current_datetime: datetime) -> Optional[Dict]:
        """
        Calculate next upcoming absolute prohibition.
        
        Only considers:
        - Street sweeping
        - Tow-away zones
        - Meter TOW schedules
        - ALTERNATE passenger loading (when active)
        
        Returns:
            {
                'type': 'street-sweeping',
                'datetime': datetime object,
                'display': 'Thu 12:00AM',
                'description': 'Street Cleaning'
            }
        """
        pass
```

### Frontend: Simple Rendering

```typescript
// frontend/src/components/BlockfaceDetail.tsx

// Rules come pre-sorted and pre-formatted from backend
const rules = blockface.rules; // Already sorted!

// Display
{rules.map(rule => (
  <li key={rule.id}>
    {rule.display_text}  // Pre-computed by backend
  </li>
))}

// Next restriction
{blockface.next_restriction && (
  <div>
    Next restriction: {blockface.next_restriction.display}
  </div>
)}
```

---

## 📋 IMPLEMENTATION PLAN

### Phase 1: Backend Enhancement ✅ (Partially Done)
- [x] Day/time/duration parsing exists
- [ ] Add rule sorting logic to regulation_normalizer.py
- [ ] Add next restriction calculation
- [ ] Add complete display string generation
- [ ] Update ingestion to pre-compute all display fields

### Phase 2: Backend Integration
- [ ] Update `ingest_data_cnn_segments.py` to call new formatters
- [ ] Pre-compute `display_text` for each rule
- [ ] Pre-compute `sort_priority` for each rule
- [ ] Calculate `next_restriction` at segment level
- [ ] Store in MongoDB

### Phase 3: Frontend Simplification
- [ ] Remove `ruleFormatter.ts` (logic moved to backend)
- [ ] Simplify `sfmtaDataFetcher.ts` (no more transformation)
- [ ] Update `BlockfaceDetail.tsx` to use pre-computed fields
- [ ] Remove all frontend parsing/formatting logic

### Phase 4: Testing & Validation
- [ ] Verify rule sorting matches requirements
- [ ] Verify next restriction calculation
- [ ] Verify modal display matches mockups
- [ ] Test with various rule combinations

---

## 🎨 MODAL DISPLAY REQUIREMENTS

Based on mockups provided:

### Banner (Green or Red)
```
✅ You can park here!
🚫 Don't park here!
```

### Location Header
```
📍 19TH ST (North, 2700-2798)
```

### Cross Streets (if available)
```
York St → Bryant St
```

### Rules Section
```
RULES:
• Street Cleaning 12am-6am Daily
• time-limit 8am-6pm Mon-Fri
```

**Sorting**:
1. Street Cleaning (most common/important)
2. Rules with Monday (if applicable)
3. Other rules

### Next Restriction (if can park)
```
⚠️ Next restriction: Thu 12:00AM
```

---

## 🔧 DATA STRUCTURE

### Current (Scattered)
```javascript
// Frontend does all the work
{
  rules: [{
    type: 'street-sweeping',
    day: 'Thursday',
    startTime: '00:00',
    endTime: '06:00'
    // Frontend formats this into display string
  }]
}
```

### Proposed (Pre-Computed)
```javascript
// Backend pre-computes everything
{
  rules: [{
    type: 'street-sweeping',
    
    // Raw canonical data (for logic)
    activeDays: [3],
    startTimeMin: 0,
    endTimeMin: 360,
    
    // Pre-computed display (for UI)
    display_text: 'Street Cleaning 12am-6am Thu',
    sort_priority: 1,
    frequency_tier: 1,
    has_monday: false,
    is_absolute_prohibition: true
  }],
  
  // Pre-computed next restriction
  next_restriction: {
    type: 'street-sweeping',
    datetime_iso: '2025-01-02T00:00:00',
    display: 'Thu 12:00AM',
    description: 'Street Cleaning'
  }
}
```

---

## ✅ BENEFITS

### For Backend
- ✅ Single source of truth for all formatting
- ✅ Consistent display across all interfaces
- ✅ Easier to maintain and update
- ✅ Better testability

### For Frontend
- ✅ Simpler code (just render pre-computed strings)
- ✅ Faster rendering (no parsing/formatting)
- ✅ Smaller bundle size (remove formatting logic)
- ✅ Consistent with backend data model

### For Users
- ✅ Consistent display format
- ✅ Faster load times
- ✅ Accurate next restriction calculation
- ✅ Better sorted rules (most important first)

---

## 🚀 NEXT STEPS

1. Implement `RuleDisplayFormatter` class in regulation_normalizer.py
2. Add sorting logic (frequency → Monday-first)
3. Add next restriction calculation
4. Update ingestion to use new formatter
5. Update frontend to use pre-computed fields
6. Remove frontend formatting logic
7. Test and validate

---

**Status**: Planning complete, ready for implementation  
**Estimated Effort**: 4-6 hours  
**Priority**: HIGH (improves UX and maintainability)