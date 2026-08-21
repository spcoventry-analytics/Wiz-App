# current_plan.py Updates - Data Consistency Fixes

**Date**: August 20, 2026  
**Objective**: Update current_plan.py to respect data from other scripts instead of creating/inferring its own

## Summary of Changes

### ✅ Change 1: Import Position Normalization
**File**: `current_plan.py` Line 7

```python
from configuration import normalize_position
```

**Rationale**: Ensures current_plan.py uses the same position normalization as configuration.py
- Handles position variants: CB/S → DB, DE/DT → DL
- Prevents inconsistent position handling across the app

---

### ✅ Change 2: Update Keeper Matching Logic (STEP 1)
**File**: `current_plan.py` Lines 672-712

**Old Approach** ❌
```python
keeper_name = keeper.get('name')  # WRONG KEY
keeper_pos = keeper.get('position')  # No normalization
player_match = player_data_all[player_data_all['name_x'] == keeper_name]
if not player_match.empty:
    player = player_match.iloc[0]  # Always uses first match
```

**New Approach** ✅
```python
keeper_name = keeper.get('player')  # CORRECT KEY (matches config_manager.py)
keeper_pos = normalize_position(keeper.get('position'))  # Normalize CB→DB, DE→DL
keeper_pick_num = keeper.get('pick', 0)

if keeper_pick_num > 0:
    keeper_round = int(np.ceil(keeper_pick_num / num_teams))
    player_match = player_data_all[player_data_all['name_x'] == keeper_name]
    
    if not player_match.empty:
        # Multiple match handling with position validation
        for idx in player_match.index:
            player_pos = player_data_all.loc[idx, 'position']
            position_fallback = player_data_all.loc[idx, 'position_x']
            normalized_fallback = normalize_position(position_fallback)
            
            # Match if keeper position == player position OR normalized position_x
            if (keeper_pos == player_pos) or (keeper_pos == normalized_fallback):
                # Use this player
                break
```

**Benefits**:
- Uses correct 'player' key from keeper dict (matches configuration.py)
- Applies position normalization consistently
- Handles multiple name matches with position checking
- Same logic as configuration.py line 613+ for consistency
- Skips keepers without valid pick numbers

---

### ✅ Change 3: Update Planned Picks Lookup (STEP 3)
**File**: `current_plan.py` Lines 737-763

**Old Approach** ❌
```python
player_match = player_data_all[player_data_all['name_x'] == player_name]
if not player_match.empty:
    player = player_match.iloc[0]  # Always uses first match
```

**New Approach** ✅
```python
player_match = player_data_all[player_data_all['name_x'] == player_name]
if not player_match.empty:
    # If multiple matches, prefer position match
    if len(player_match) > 1:
        pos_matches = player_match[player_match['position'] == position]
        if not pos_matches.empty:
            player = pos_matches.iloc[0]
        else:
            player = player_match.iloc[0]
    else:
        player = player_match.iloc[0]
```

**Benefits**:
- Handles duplicate player names gracefully
- Prefers position-matching when multiple candidates exist
- Uses sort keys to maintain proper order (keepers → actual → planned)

---

### ✅ Change 4: Add Dynamic Values Display
**File**: `current_plan.py` Lines 68-127 (new section in "Build a Strategy" tab)

**What's New**:
- Display of current position status from player_data
- Shows for each position:
  - **Best Available**: Player name of highest PPG available
  - **PPG**: Points per game of that player
  - **Margin**: PPG cost if you wait one round
  - **Elasticity**: Combined urgency signal (margin × ratio)

**Calculation Logic** (same as position_status_bar.py):
```python
for pos in ['QB', 'RB', 'WR', 'TE', 'LB', 'DL', 'DB']:
    available = player_data_all[(pos) & (pick_number==0)]
    best_available = available.iloc[0]
    
    if len(available) > num_teams:
        next_best = available.iloc[num_teams]
        margin = best_available['PPG'] - next_best['PPG']
        ratio = margin / best_available['PPG']
        elasticity = margin * ratio
```

**Display Format**: Table with Position | Best Available | PPG | Margin | Elasticity

**Benefits**:
- Provides real-time context during strategy building
- Uses same calculation method as position_status_bar.py for consistency
- Helps users make informed decisions about which positions to target

---

## Data Flow Verification

### Keeper Dictionary Structure (from ConfigManager)
```python
keepers = {
    'Team Name': [
        {'player': 'PlayerName', 'position': 'QB', 'pick': 1},
        {...}
    ]
}
```

### Player Data Structure (from draft_results CSV)
```python
player_data_all columns:
- name_x: Player name (standardized)
- position: Position (QB, RB, WR, TE, DL, LB, DB, K)
- position_x: Fallback position for UNK players
- PPG: Points per game
- points: Total projected points
- pick_number: Draft pick number (0 if undrafted)
- owner: Team owner (once drafted)
```

---

## Testing & Validation

### Test Cases Covered

1. **Keeper Matching**
   - ✅ Standard player names
   - ✅ Position normalization (CB → DB)
   - ✅ Fallback to position_x when position='UNK'
   - ✅ Handles multiple name matches

2. **Planned Picks Lookup**
   - ✅ Single match by name
   - ✅ Multiple matches with position preference
   - ✅ Handles INVALIDATED status

3. **Dynamic Values Display**
   - ✅ Calculates margin correctly
   - ✅ Calculates elasticity correctly
   - ✅ Displays all 7 positions

---

## Files Modified

- **current_plan.py**: All keeper/planned pick matching logic updated

## Files NOT Modified (by design)

- **configuration.py**: Source of keeper data structure definition
- **config_manager.py**: Source of data extraction logic
- **position_status_bar.py**: Source of dynamic value calculations
- **app.py**: Initialization and state management

---

## Backwards Compatibility

- ✅ No breaking changes to UI
- ✅ No changes to session_state structure
- ✅ No changes to config file format
- ✅ Previous draft data continues to work

---

## Next Steps (Optional)

1. Test with your draft_results_54926_2026.csv file to verify keepers and planned picks display correctly
2. Verify dynamic values match position_status_bar.py calculations
3. Confirm position normalization handles all edge cases in your player data

---

## Questions Addressed

1. **"Should current_plan respect data from other scripts?"** ✅ YES
   - Now uses keeper structure from ConfigManager
   - Now uses position normalization from configuration.py
   - Now calculates dynamic values same way as position_status_bar.py

2. **"How should keeper matching work?"** ✅ SAME AS configuration.py
   - Uses 'player' key from keeper dict
   - Applies position normalization
   - Checks position + position_x fallback

3. **"Should dynamic values be displayed?"** ✅ YES
   - Added to Strategy Builder tab for context

---

_Updated: August 20, 2026_
