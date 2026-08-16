#!/usr/bin/env python3
"""
Test position normalization for keeper editor
"""

import pandas as pd
import glob
import os

# Copy the normalize_position function
def normalize_position(pos):
    """
    Normalize position variants to standard positions.
    Maps granular positions (CB, S, DE, DT, etc.) to standard positions (DB, DL, etc.)
    """
    if not pos or pos in ["", "UNK", None]:
        return pos
    
    pos = str(pos).upper()
    
    # Defensive backs
    if pos in ["CB", "S"]:
        return "DB"
    # Defensive line
    if pos in ["DE", "DT"]:
        return "DL"
    
    return pos

print("=" * 60)
print("TESTING POSITION NORMALIZATION")
print("=" * 60)

# Load draft_results CSV
csv_files = glob.glob(f"draft_results_54926_*.csv")
latest_csv = max(csv_files, key=os.path.getmtime)
player_data = pd.read_csv(latest_csv)

print(f"\n📁 Loaded: {os.path.basename(latest_csv)}")

# Build player_position_map with normalization
player_position_map = {}
for _, row in player_data.iterrows():
    player_name = row.get('name_x')
    player_pos = row.get('position')
    position_fallback = row.get('position_x')
    
    if player_name:
        if player_pos and player_pos not in ["", "UNK", None]:
            # Normal position - use as-is
            if player_name not in player_position_map:
                player_position_map[player_name] = set()
            player_position_map[player_name].add(str(player_pos))
        elif player_pos == "UNK" and position_fallback and position_fallback not in ["", None]:
            # UNK player - use position_x fallback with normalization
            if player_name not in player_position_map:
                player_position_map[player_name] = set()
            normalized_pos = normalize_position(position_fallback)
            player_position_map[player_name].add(normalized_pos)

print(f"✅ Built player_position_map with {len(player_position_map)} players")

# Test normalization
test_cases = [
    ('CB', 'DB'),      # Cornerback → Defensive Back
    ('S', 'DB'),       # Safety → Defensive Back
    ('DE', 'DL'),      # Defensive End → Defensive Line
    ('DT', 'DL'),      # Defensive Tackle → Defensive Line
    ('LB', 'LB'),      # Linebacker → unchanged
    ('QB', 'QB'),      # Quarterback → unchanged
]

print("\n" + "=" * 60)
print("TEST 1: Position Normalization Mapping")
print("=" * 60)

all_pass = True
for pos_in, expected_out in test_cases:
    actual_out = normalize_position(pos_in)
    status = "✅" if actual_out == expected_out else "❌"
    print(f"{status} {pos_in} → {actual_out} (expected {expected_out})")
    if actual_out != expected_out:
        all_pass = False

# Test with players
print("\n" + "=" * 60)
print("TEST 2: Players with Normalized Positions")
print("=" * 60)

# Find some test players
test_positions = {
    'CB': None,  # Cornerback
    'S': None,   # Safety
    'DE': None,  # Defensive End
    'DT': None,  # Defensive Tackle
}

for test_pos in test_positions.keys():
    test_row = player_data[player_data['position_x'] == test_pos]
    if not test_row.empty:
        player_name = test_row.iloc[0]['name_x']
        normalized = normalize_position(test_pos)
        if player_name in player_position_map:
            if normalized in player_position_map[player_name]:
                print(f"✅ {player_name}: {test_pos} → {normalized} in mapping")
            else:
                print(f"❌ {player_name}: {test_pos} → {normalized} NOT in mapping")
                print(f"   Actual positions: {player_position_map[player_name]}")
        else:
            print(f"❌ {player_name} not found in mapping!")

# Test keeper lookup logic
print("\n" + "=" * 60)
print("TEST 3: Keeper Lookup with Normalized Positions")
print("=" * 60)

# Sample keepers with various positions
test_keepers = [
    {'player': 'Cedric Gray', 'position': 'LB'},      # Should find as LB
    {'player': 'Lamar Jackson', 'position': 'QB'},    # Should find as QB
]

# Add a test with a defensive player if we can find one
defensive_player = player_data[player_data['position_x'] == 'CB'].iloc[0] if len(player_data[player_data['position_x'] == 'CB']) > 0 else None
if defensive_player is not None:
    test_keepers.append({'player': defensive_player['name_x'], 'position': 'DB'})  # Look for as DB (normalized from CB)

for keeper in test_keepers:
    keeper_name = keeper['player']
    keeper_pos = normalize_position(keeper['position'])
    
    player_match = player_data[player_data['name_x'] == keeper_name]
    if not player_match.empty:
        found = False
        for idx in player_match.index:
            player_pos = player_data.loc[idx, 'position']
            position_fallback = player_data.loc[idx, 'position_x']
            normalized_fallback = normalize_position(position_fallback)
            
            if (keeper_pos == player_pos) or (keeper_pos == normalized_fallback):
                print(f"✅ Found keeper: {keeper_name} (looking for {keeper['position']}/{keeper_pos})")
                print(f"   • CSV position: {player_pos}, position_x: {position_fallback} → {normalized_fallback}")
                found = True
                break
        
        if not found:
            print(f"❌ Keeper position mismatch: {keeper_name} (looking for {keeper['position']}/{keeper_pos})")
            player_row = player_match.iloc[0]
            print(f"   • CSV position: {player_row['position']}, position_x: {player_row['position_x']}")
    else:
        print(f"❌ Player not found: {keeper_name}")

print("\n" + "=" * 60)
if all_pass:
    print("✅ ALL TESTS PASSED")
else:
    print("⚠️  SOME TESTS FAILED")
print("=" * 60)
