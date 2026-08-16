import pandas as pd

df = pd.read_csv('draft_results_54926_2026.csv')

# Show columns
print('Columns:', list(df.columns[:20]))
print()

# Check Cedric Gray
cedric = df[df['name_x'] == 'Cedric Gray']
if not cedric.empty:
    print('Cedric Gray:')
    print(f'  position: {cedric.iloc[0]["position"]}')
    print(f'  position_x: {cedric.iloc[0]["position_x"]}')
    print()

# Check how many UNK in each column
print(f'UNK in position column: {(df["position"] == "UNK").sum()}')
print(f'UNK in position_x column: {(df["position_x"] == "UNK").sum()}')
print()

# Show some UNK players and their position_x fallback
unk_players = df[df['position'] == 'UNK'].head(5)
print('Sample UNK players with position_x fallback:')
for idx, row in unk_players.iterrows():
    print(f'  {row["name_x"]}: position={row["position"]}, position_x={row["position_x"]}')
