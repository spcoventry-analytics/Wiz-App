import streamlit as st
import pandas as pd
from datetime import datetime

def show_enter_pick():
    st.header("Enter Draft Pick")

    player_data_all = st.session_state.get('player_data_all')
    available_players = player_data_all[player_data_all["pick_number"] == 0]
    if available_players is None or available_players.empty:
        st.warning("No available players to draft. All picks have been made or data is missing.")
        return

    # Start filters empty
    position = st.radio("Position (optional)", [""] + list(available_players["position"].unique()), horizontal=True)
    team = st.selectbox("NFL Team (optional)", [""] + sorted(list(available_players["team_x"].unique().astype(str))))

    

    # Filter player names if position or team is selected
    filtered_players = available_players.copy()
    if position:
        filtered_players = filtered_players[filtered_players["position"] == position]
    if team:
        filtered_players = filtered_players[filtered_players["team_x"] == team]

    name = st.selectbox("Player Name", filtered_players["name_x"].unique())

    # Filter for ESPN ID
    filtered = available_players[(available_players["name_x"] == name)]
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
    # Find next available pick number
    next_pick = int(st.session_state['player_data_all']["pick_number"].max()) + 1 if st.session_state['player_data_all']["pick_number"].max() > 0 else 1
    if "pick_number_input" not in st.session_state:
        st.session_state["pick_number_input"] = next_pick
    pick_number = st.number_input("Pick Number", min_value=st.session_state["pick_number_input"], step=1, value=st.session_state["pick_number_input"])
    league_team = st.radio("League Team", st.session_state.get('teams', []), horizontal=True)

    if st.button("Submit Pick", disabled=not can_submit):
        # Add pick metadata columns
        st.session_state['player_data_all'].loc[st.session_state['player_data_all']["espn_id"] == espn_id, "pick_number"] = pick_number
        st.session_state['player_data_all'].loc[st.session_state['player_data_all']["espn_id"] == espn_id, "owner"] = league_team
        st.session_state['player_data_all'].to_csv(st.session_state['csv_filename'], index=False)
        st.success(f"Player {name} has been assigned to pick {pick_number} for team {league_team}.")
        st.success(f"Pick submitted to {st.session_state['csv_filename']}!")
        st.session_state["pick_number_input"] = st.session_state['player_data_all']['pick_number'].max() + 1
        # Hide the entry form after submission  This does not work but we are moving on
        if "hide_enter_pick" in globals():
            hide_enter_pick()
        else:
            st.session_state['show_enter_pick'] = False
