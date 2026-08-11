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
    pick_position = st.radio("Position (optional)", [""] + list(available_players["position"].unique()), horizontal=True, key="enter_pick_position")
    pick_team = st.selectbox("NFL Team (optional)", [""] + sorted(list(available_players["team_x"].unique().astype(str))), key="enter_pick_team")



    # Filter player names if position or team is selected
    filtered_players = available_players.copy()
    if pick_position:
        filtered_players = filtered_players[filtered_players["position"] == pick_position]
    if pick_team:
        filtered_players = filtered_players[filtered_players["team_x"] == pick_team]

    pick_name = st.selectbox("Player Name", filtered_players["name_x"].unique(), key="enter_pick_name")

    # Filter for unique player ID (name + position + team)
    filtered = available_players[(available_players["name_x"] == pick_name)]
    if pick_position:
        filtered = filtered[filtered["position"] == pick_position]
    if pick_team:
        filtered = filtered[filtered["team_x"] == pick_team]
    
    pick_unique_ids = filtered["unique_player_id"].unique()
    if len(pick_unique_ids) == 1:
        # If only one player matches (position + team narrowed it down), use it
        pick_unique_id = pick_unique_ids[0]
        st.success(f"Player ID: {pick_unique_id}")
        can_submit = True
    else:
        st.warning("Select filters until only one player version is found (e.g., for multi-position eligible players).")
        can_submit = False

    # Pick number and league team
    # Find next available pick number
    next_pick_number = int(st.session_state['player_data_all']["pick_number"].max()) + 1 if st.session_state['player_data_all']["pick_number"].max() > 0 else 1
    if "pick_number_input" not in st.session_state:
        st.session_state["pick_number_input"] = next_pick_number
    pick_number = st.number_input("Pick Number", min_value=1, step=1, value=st.session_state["pick_number_input"], key="enter_pick_number")
    # pick_number = st.number_input("Pick Number", 
    #     min_value= st.session_state["pick_number_input"], 
    #     step=1, 
    #     value=st.session_state["pick_number_input"], 
    #     key="enter_pick_number")
    draft_order = st.session_state.get('draft_order', st.session_state.get('teams', []))
    pick_league_team = st.radio("League Team", draft_order, horizontal=True, key="enter_pick_league_team")

    if st.button("Submit Pick", disabled=not can_submit, key="enter_pick_submit"):
        # Get the ESPN ID of the selected player
        selected_player_row = st.session_state['player_data_all'][
            st.session_state['player_data_all']["unique_player_id"] == pick_unique_id
        ]
        
        if selected_player_row.empty:
            st.error("No matching player found to update. Please check filters.")
        else:
            # Get the ESPN ID to find ALL position variants of this player
            pick_espn_id = selected_player_row.iloc[0]["espn_id"]
            
            # Mark ALL rows with this ESPN ID as drafted (handles multi-position eligible players)
            all_variants = st.session_state['player_data_all'][
                st.session_state['player_data_all']["espn_id"] == pick_espn_id
            ]
            
            st.write(f"Removing {len(all_variants)} row(s) for ESPN ID {pick_espn_id}:")
            st.write(all_variants[['name_x', 'position', 'team_x']])
            
            # Update all variants with same ESPN ID
            st.session_state['player_data_all'].loc[
                st.session_state['player_data_all']["espn_id"] == pick_espn_id, 
                "pick_number"
            ] = pick_number
            st.session_state['player_data_all'].loc[
                st.session_state['player_data_all']["espn_id"] == pick_espn_id, 
                "owner"
            ] = pick_league_team
            
            st.session_state['player_data_all'].to_csv(st.session_state['csv_filename'], index=False)
            st.success(f"Player {pick_name} ({pick_position} - {pick_team}) has been assigned to pick {pick_number} for team {pick_league_team}.")
            if len(all_variants) > 1:
                st.info(f"✓ All {len(all_variants)} position variants removed from board (multi-position eligible player)")
            st.success(f"Pick submitted to {st.session_state['csv_filename']}!")
            st.session_state["pick_number_input"] = st.session_state['player_data_all']['pick_number'].max() + 1
            # Hide the entry form after submission  This does not work but we are moving on
            if "hide_enter_pick" in globals():
                hide_enter_pick()
            else:
                st.session_state['show_enter_pick'] = False
