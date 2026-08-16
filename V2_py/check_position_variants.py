import pandas as pd
import numpy as np

df = pd.read_csv('draft_results_54926_2026.csv')

print('Unique positions in position_x column:')
positions = [p for p in df['position_x'].unique() if pd.notna(p)]
print(sorted(positions))
print()
print('Position counts:')
for pos in sorted(positions):
    count = (df['position_x'] == pos).sum()
    print(f'  {pos}: {count}')
