#!/usr/bin/env python3
"""
Test the new position_x fallback logic for UNK players
"""

import pandas as pd
import glob
import os

print("=" * 60)
print("TESTING POSITION_X FALLBACK LOGIC")
print("=" * 60)

# Load draft_results CSV
csv_files = glob.glob(f"draft_results_54926_*.csv")
latest_csv = max(csv_files, key=os.path.getmtime)
player_data = pd.read_csv(latest_csv)

print(f"\n📁 Loaded: {os.path.basename(latest_csv)} ({len(player_data)} players)")

# Extract positions (exclude UNK)
positions = sorted(player_data['position'].unique().tolist())
positions = [p for p in positions if p not in ["", "UNK", None]]

print(f"\n✅ Available positions (UNK excluded): {sorted(positions)}")

# Build player_position_map with position_x fallback
player_position_map = {}
unk_players_converted = 0

for _, row in player_data.iterrows():
    player_name = row.get('name_x')
    player_pos = row.get('position')
    position_fallback = row.get('position_x')
    
    if player_name:
        if player_pos and player_pos not in ["", "UNK", None]:
            # Normal position
            if player_name not in player_position_map:
                player_position_map[player_name] = set()
            player_position_map[player_name].add(str(player_pos))
        elif player_pos == "UNK" and position_fallback and position_fallback not in ["", None]:
            # UNK player - use position_x fallback
            if player_name not in player_position_map:
                player_position_map[player_name] = set()
            player_position_map[player_name].add(str(position_fallback))
            unk_players_converted += 1

print(f"✅ Player-position map built with {len(player_position_map)} players")
print(f"   • {unk_players_converted} UNK players converted using position_x fallback")

# Test: Cedric Gray should be in LB category now
print("\n" + "=" * 60)
print("TEST 1: Cedric Gray (UNK → LB via position_x)")
print("=" * 60)

if 'Cedric Gray' in player_position_map:
    print(f"✅ Cedric Gray found with positions: {player_position_map['Cedric Gray']}")
    if 'LB' in player_position_map['Cedric Gray']:
        print("✅ Cedric Gray is available in LB category!")
else:
    print("❌ Cedric Gray not found!")

# Test: Sample some converted UNK players
print("\n" + "=" * 60)
print("TEST 2: Sample UNK→Position conversions")
print("=" * 60)

unk_rows = player_data[player_data['position'] == 'UNK'].head(5)
print(f"Sample UNK players converted via position_x:")
for _, row in unk_rows.iterrows():
    name = row['name_x']
    pos_x = row['position_x']
    if name in player_position_map and pos_x in player_position_map[name]:
        print(f"  ✅ {name}: UNK → {pos_x}")
    else:
        print(f"  ❌ {name}: conversion failed")

# Test: Keeper lookup logic
print("\n" + "=" * 60)
print("TEST 3: Keeper lookup with position matching")
print("=" * 60)

test_keepers = [
    {'player': 'Cedric Gray', 'position': 'LB'},  # UNK player stored as LB
    {'player': 'Lamar Jackson', 'position': 'QB'},  # Normal player
]

for keeper in test_keepers:
    # Find player by name
    player_match = player_data[player_data['name_x'] == keeper['player']]
    if not player_match.empty:
        found = False
        for idx in player_match.index:
            player_pos = player_data.loc[idx, 'position']
            position_fallback = player_data.loc[idx, 'position_x']
            
            # Check if keeper position matches either
            if (keeper['position'] == player_pos) or (keeper['position'] == position_fallback):
                print(f"✅ Found keeper: {keeper['player']} ({keeper['position']})")
                print(f"   • CSV position: {player_pos}, position_x: {position_fallback}")
                found = True
                break
        if not found:
            print(f"❌ Keeper position mismatch: {keeper['player']} ({keeper['position']})")
    else:
        print(f"❌ Player not found: {keeper['player']}")

print("\n" + "=" * 60)
print("✅ ALL TESTS COMPLETE")
print("=" * 60)
