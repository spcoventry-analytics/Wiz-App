# consider_options.py
import streamlit as st
import numpy as np
import pandas as pd

def show_consider_options():
    st.title("Consider Options")
    
    position_colors = st.session_state.get('position_colors', {})
    player_data_all = st.session_state.get('player_data_all')

    keep_columns = ['name_x', 'position', 'team_x', # who 
                   'points', 'floor', 'ceiling', 'position_rank', "tier", 'adp', "depth", # what
                   'age', 'college', 'draft_year_x', 'weight', 'espn_id', "pick_number"] # Bio and History would be next

    # tier_edges = [1, 11, 21, 31, 41, 51, 1000]  # 5 tiers: 1-10, 11-20, 21-30, 31-40, 41+
    # tier_labels = [1, 2, 3, 4, 5, 6]
    # player_data_all['tier'] = pd.cut(player_data_all['position_rank'], bins=tier_edges, labels=tier_labels, right=False)
    
    # # Calculate average for each position and tier
    # tier_avgs = player_data_all.groupby(['position', 'tier'])['points'].mean().reset_index()
    # tier_avgs = tier_avgs[:6]

    available_players = player_data_all[player_data_all["pick_number"] == 0]
    # Rolling averages later

    if available_players is None or available_players.empty:
        st.warning("No available players to draft. All picks have been made or data is missing.")
        return
    # Tiers

    # ADP 
    adp = available_players.sort_values(by="adp", ascending=True)
    adp_columns = [col for col in keep_columns if col in adp.columns]
    adp = adp[adp_columns].head(10)

    st.write("### Top 10 Players by ADP:")
    #st.dataframe(adp)

    # Start filters empty
    position = st.radio("Position (optional)", [""] + list(available_players["position"].unique()), horizontal=True)
    team = st.selectbox("NFL Team (optional)", [""] + sorted(list(available_players["team_x"].unique().astype(str))))

    # Filter player names if position or team is selected
    filtered_players = available_players.copy()
    if position:
        filtered_players = filtered_players[filtered_players["position"] == position]
    if team:
        filtered_players = filtered_players[filtered_players["team_x"] == team]

    st.write("### Available Players:")
    
    existing_columns = [col for col in keep_columns if col in filtered_players.columns]
    SHOW = pd.DataFrame(filtered_players)
    SHOW = SHOW[existing_columns]
    SHOW = SHOW.sort_values(by=["position", "points"], ascending=[True, False])
    st.dataframe(SHOW)



