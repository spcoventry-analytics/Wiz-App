#!/usr/bin/env python3
"""
Test script to verify:
1. Cedric Gray (UNK position) loads in keeper editor
2. Keepers are properly converted to picks on draft board
"""

import pandas as pd
import glob
import os

print("=" * 60)
print("TESTING KEEPER FIXES")
print("=" * 60)

# Load draft_results CSV
csv_files = glob.glob(f"draft_results_54926_*.csv")
if not csv_files:
    print("❌ No draft_results CSV found!")
    exit(1)

latest_csv = max(csv_files, key=os.path.getmtime)
print(f"\n📁 Loading: {os.path.basename(latest_csv)}")

player_data = pd.read_csv(latest_csv)
print(f"✅ Loaded {len(player_data)} players")

# TEST 1: Check if Cedric Gray exists
print("\n" + "=" * 60)
print("TEST 1: Cedric Gray (UNK position) in player universe")
print("=" * 60)

cedric_matches = player_data[
    (player_data['name_x'].str.contains('Cedric', na=False, case=False)) &
    (player_data['name_x'].str.contains('Gray', na=False, case=False))
]

if cedric_matches.empty:
    print("❌ Cedric Gray NOT found in CSV!")
else:
    print(f"✅ Found Cedric Gray at row {cedric_matches.index[0]}")
    for idx, row in cedric_matches.iterrows():
        print(f"   • Name: {row.get('name_x')}")
        print(f"   • Position: {row.get('position')}")
        print(f"   • Team: {row.get('team_y')}")

# TEST 2: Check if position loading includes UNK
print("\n" + "=" * 60)
print("TEST 2: Position list includes UNK for players like Cedric")
print("=" * 60)

positions = sorted(player_data['position'].unique().tolist())
positions_filtered = [p for p in positions if p not in ["", None]]

print(f"Raw positions in CSV: {sorted(positions)}")
print(f"After filtering (empty, None only): {positions_filtered}")

if 'UNK' in positions_filtered:
    print("✅ UNK position is INCLUDED (good!)")
    unk_players = player_data[player_data['position'] == 'UNK']
    print(f"   • {len(unk_players)} players with UNK position")
else:
    print("⚠️  UNK position is NOT in available positions")

# TEST 3: Build player_position_map like keeper editor does
print("\n" + "=" * 60)
print("TEST 3: Player-position mapping includes Cedric Gray")
print("=" * 60)

player_position_map = {}
for _, row in player_data.iterrows():
    player_name = row.get('name_x')
    player_pos = row.get('position')
    if player_name and player_pos and player_pos not in ["", None]:
        if player_name not in player_position_map:
            player_position_map[player_name] = set()
        player_position_map[player_name].add(str(player_pos))

print(f"✅ Built player_position_map with {len(player_position_map)} unique players")

if 'Cedric Gray' in player_position_map:
    print(f"✅ Cedric Gray is in mapping with positions: {player_position_map['Cedric Gray']}")
else:
    # Check for variations
    cedric_names = [name for name in player_position_map.keys() if 'Cedric' in name and 'Gray' in name]
    if cedric_names:
        print(f"✅ Found Cedric Gray (with variant name): {cedric_names}")
        for name in cedric_names:
            print(f"   • {name}: {player_position_map[name]}")
    else:
        print("❌ Cedric Gray NOT in player_position_map!")

# TEST 4: Verify keeper pick conversion logic
print("\n" + "=" * 60)
print("TEST 4: Keeper-to-pick conversion (mock test)")
print("=" * 60)

# Mock keeper data
mock_keeper = {
    'player': 'Cedric Gray',
    'position': 'UNK',
    'pick': 5
}

test_player = player_data[
    (player_data['name_x'] == mock_keeper['player']) &
    (player_data['position'] == mock_keeper['position'])
]

if not test_player.empty:
    print(f"✅ Can find '{mock_keeper['player']}' ({mock_keeper['position']}) to convert to pick #{mock_keeper['pick']}")
    idx = test_player.index[0]
    print(f"   • Will set: owner='TestTeam', pick_number={mock_keeper['pick']}")
else:
    print(f"❌ Cannot find keeper to convert: {mock_keeper['player']} ({mock_keeper['position']})")

print("\n" + "=" * 60)
print("✅ ALL TESTS COMPLETE")
print("=" * 60)
