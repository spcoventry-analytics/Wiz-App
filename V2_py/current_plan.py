# current_plan.py
import streamlit as st
import numpy as np
import pandas as pd

def show_current_plan():
    st.title("Current Plan")
    st.write("Space to display the current plan here.")
    position_colors = st.session_state.get('position_colors', {})
    player_data_all = st.session_state.get('player_data_all')

    keep_columns = ['name_x', 'position', 'team_x', # who 
                   'points', 'floor', 'ceiling', 'position_rank', "tier", 'adp', "depth", # what
                   'age', 'college', 'draft_year_x', 'weight', 'espn_id', "pick_number"] # Bio and History would be next

    tier_edges = [1, 11, 21, 31, 41, 51, 1000]  # 5 tiers: 1-10, 11-20, 21-30, 31-40, 41+
    tier_labels = [1, 2, 3, 4, 5, 6]
    player_data_all['tier'] = pd.cut(player_data_all['position_rank'], bins=tier_edges, labels=tier_labels, right=False)

    # Calculate average for each position and tier
    tier_avgs = player_data_all.groupby(['position', 'tier'])[['points', 'adp']].mean().reset_index()
    tier_avgs = tier_avgs.sort_values(by=['adp'])
    available_players = player_data_all[player_data_all["pick_number"] == 0]
    tier_counts = available_players.groupby(['position', 'tier']).size().reset_index(name='available_count')
    tier_avgs = pd.merge(tier_avgs, tier_counts, on=['position', 'tier'], how='left')
    # Rolling averages later

    if available_players is None or available_players.empty:
        st.warning("No available players to draft. All picks have been made or data is missing.")
        return
    # Tiers
    st.write("### Average Points by Position and Tier:")
    st.dataframe(tier_avgs)
    
    