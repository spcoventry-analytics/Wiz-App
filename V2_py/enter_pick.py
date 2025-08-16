import streamlit as st
import pandas as pd
from datetime import datetime

def show_enter_pick():
    st.header("Enter Draft Pick")
    player_summary = st.session_state.get('player_summary')
    player_summary = player_summary[player_summary["pick_number"] == 0]
    if player_summary is None or player_summary.empty:
        st.warning("No player summary data available. Please visit 'Consider Options' first.")
        return


    # Start filters empty
    position = st.selectbox("Position (optional)", [""] + list(player_summary["position"].unique()))
    team = st.selectbox("NFL Team (optional)", [""] + list(player_summary["team_x"].unique()))

    # Filter player names if position or team is selected
    filtered_players = player_summary.copy()
    if position:
        filtered_players = filtered_players[filtered_players["position"] == position]
    if team:
        filtered_players = filtered_players[filtered_players["team_x"] == team]

    name = st.selectbox("Player Name", filtered_players["name_x"].unique())

    # Filter for ESPN ID
    filtered = player_summary[(player_summary["name_x"] == name)]
    if position:
        filtered = filtered[filtered["position"] == position]
    if team:
        filtered = filtered[filtered["team_x"] == team]
    espn_ids = filtered["espn_id"].unique()
    if len(espn_ids) == 1:
        # If only one ESPN ID matches, use it
        espn_id = espn_ids[0]
        st.success(f"ESPN ID: {espn_id}")
        can_submit = True
        
    else:
        st.warning("Select filters until only one ESPN ID is found.")
        can_submit = False

    # Pick number and league team
    pick_number = st.number_input("Pick Number", min_value=1, step=1)
    league_team = st.selectbox("League Team", st.session_state.get('teams', []))

    if st.button("Submit Pick", disabled=not can_submit):
        # Add pick metadata columns
        player_data_all[player_summary["espn_id"] == espn_id]["pick_number"] = pick_number
        write_csv(st.session_state['csv_filename'], player_data_all)
        st.success(f"Pick submitted to {csv_filename}!")
        st.session_state['show_enter_pick'] = False


