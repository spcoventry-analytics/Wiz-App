import streamlit as st
import pandas as pd
from datetime import datetime

def show_enter_pick():
    st.header("Enter Draft Pick")
    player_summary = st.session_state.get('player_summary')
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
        # Get full player_summary row for selected espn_id
        player_row = player_summary[player_summary["espn_id"] == espn_id].copy()
        # Add pick metadata columns
        player_row["pick_number"] = pick_number
        player_row["league_team"] = league_team
        player_row["timestamp"] = datetime.now().isoformat()
        # Name CSV file by league_id and season_id
        league_id = st.session_state.get('league_id', 'unknown_league')
        season_id = st.session_state.get('season_id', 'unknown_season')
        csv_filename = f"draft_results_{league_id}_{season_id}.csv"
        file_exists = False
        try:
            with open(csv_filename, "r") as f:
                file_exists = True
        except FileNotFoundError:
            pass
        player_row.to_csv(csv_filename, mode="a", header=not file_exists, index=False)
        st.success(f"Pick submitted to {csv_filename}!")


