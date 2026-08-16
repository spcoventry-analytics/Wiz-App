#!/usr/bin/env python3
"""
Test position cleaning function on actual draft data
"""

import pandas as pd
import glob
import os

def clean_positions(player_data):
    """
    Clean position data by:
    1. Replacing UNK with position_x fallback
    2. Normalizing position variants (CB→DB, S→DB, DE→DL, DT→DL)
    
    Returns cleaned DataFrame.
    """
    df = player_data.copy()
    
    # Helper function to normalize position variants
    def normalize_pos(pos):
        if not pos or pos in ["", None]:
            return pos
        pos = str(pos).upper()
        if pos in ["CB", "S"]:
            return "DB"
        if pos in ["DE", "DT"]:
            return "DL"
        return pos
    
    # Clean each row
    for idx, row in df.iterrows():
        current_pos = row.get('position')
        fallback_pos = row.get('position_x')
        
        # If position is UNK, use position_x fallback
        if current_pos == "UNK" and fallback_pos and fallback_pos not in ["", None]:
            df.loc[idx, 'position'] = normalize_pos(fallback_pos)
        # Normalize all positions (including already-set positions)
        elif current_pos and current_pos not in ["", None]:
            normalized = normalize_pos(current_pos)
            if normalized != current_pos:
                df.loc[idx, 'position'] = normalized
    
    return df

print("=" * 60)
print("TESTING POSITION DATA CLEANING")
print("=" * 60)

# Load draft_results CSV
csv_files = glob.glob(f"draft_results_54926_*.csv")
latest_csv = max(csv_files, key=os.path.getmtime)
player_data = pd.read_csv(latest_csv)

print(f"\n📁 Loaded: {os.path.basename(latest_csv)} ({len(player_data)} players)")

# Check before cleaning
print("\n" + "=" * 60)
print("BEFORE CLEANING:")
print("=" * 60)

positions_before = player_data['position'].value_counts().sort_index()
print(f"Position value counts:")
for pos, count in positions_before.items():
    print(f"  {pos}: {count}")

# Check Cedric Gray before
cedric_before = player_data[player_data['name_x'] == 'Cedric Gray']
if not cedric_before.empty:
    print(f"\n✓ Cedric Gray before: position={cedric_before.iloc[0]['position']}, position_x={cedric_before.iloc[0]['position_x']}")

# Clean the data
print("\nCleaning positions...")
player_data_clean = clean_positions(player_data)

# Check after cleaning
print("\n" + "=" * 60)
print("AFTER CLEANING:")
print("=" * 60)

positions_after = player_data_clean['position'].value_counts().sort_index()
print(f"Position value counts:")
for pos, count in positions_after.items():
    print(f"  {pos}: {count}")

# Check Cedric Gray after
cedric_after = player_data_clean[player_data_clean['name_x'] == 'Cedric Gray']
if not cedric_after.empty:
    print(f"\n✓ Cedric Gray after: position={cedric_after.iloc[0]['position']}, position_x={cedric_after.iloc[0]['position_x']}")
    if cedric_after.iloc[0]['position'] == 'LB':
        print("✅ Cedric Gray successfully cleaned: UNK → LB")
    else:
        print(f"❌ Cedric Gray cleaning failed: expected LB, got {cedric_after.iloc[0]['position']}")

# Check some CB/S players
print("\n" + "=" * 60)
print("SAMPLE: Defensive Backs (CB → DB, S → DB)")
print("=" * 60)

cb_players = player_data[player_data['position_x'] == 'CB'].head(2)
s_players = player_data[player_data['position_x'] == 'S'].head(2)

for _, row in pd.concat([cb_players, s_players]).iterrows():
    name = row['name_x']
    pos_x_before = row['position_x']
    
    # Find in cleaned data
    cleaned_row = player_data_clean[player_data_clean['name_x'] == name]
    if not cleaned_row.empty:
        pos_after = cleaned_row.iloc[0]['position']
        if pos_after == 'DB':
            print(f"✅ {name}: {pos_x_before} → {pos_after}")
        else:
            print(f"❌ {name}: {pos_x_before} → {pos_after} (expected DB)")

# Check some DE/DT players
print("\n" + "=" * 60)
print("SAMPLE: Defensive Line (DE → DL, DT → DL)")
print("=" * 60)

de_players = player_data[player_data['position_x'] == 'DE'].head(2)
dt_players = player_data[player_data['position_x'] == 'DT'].head(2)

for _, row in pd.concat([de_players, dt_players]).iterrows():
    name = row['name_x']
    pos_x_before = row['position_x']
    
    # Find in cleaned data
    cleaned_row = player_data_clean[player_data_clean['name_x'] == name]
    if not cleaned_row.empty:
        pos_after = cleaned_row.iloc[0]['position']
        if pos_after == 'DL':
            print(f"✅ {name}: {pos_x_before} → {pos_after}")
        else:
            print(f"❌ {name}: {pos_x_before} → {pos_after} (expected DL)")

# Verify UNK is gone
print("\n" + "=" * 60)
print("VERIFICATION:")
print("=" * 60)

unk_count = (player_data_clean['position'] == 'UNK').sum()
if unk_count == 0:
    print("✅ All UNK positions cleaned successfully (count = 0)")
else:
    print(f"❌ Still have UNK positions remaining: {unk_count}")

print("\n" + "=" * 60)
print("✅ CLEANING TEST COMPLETE")
print("=" * 60)
