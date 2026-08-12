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
    
    # Calculate default team based on snake draft logic
    draft_order = st.session_state.get('draft_order', st.session_state.get('teams', []))
    num_teams = len(draft_order)
    
    if num_teams > 0:
        # Snake draft: alternating direction each round
        # Round 0: normal order, Round 1: reversed, Round 2: normal, etc.
        round_num = (pick_number - 1) // num_teams
        position_in_round = (pick_number - 1) % num_teams
        
        if round_num % 2 == 0:
            # Even round (0, 2, 4...): normal order
            default_team = draft_order[position_in_round]
        else:
            # Odd round (1, 3, 5...): reversed order
            default_team = draft_order[num_teams - 1 - position_in_round]
        
        default_index = draft_order.index(default_team) if default_team in draft_order else 0
    else:
        default_team = ""
        default_index = 0
    
    pick_league_team = st.radio("League Team", draft_order, horizontal=True, key="enter_pick_league_team", index=default_index)

    if st.button("Submit Pick", disabled=not can_submit, key="enter_pick_submit"):
        # Get the ESPN ID of the selected player
        selected_player_row = st.session_state['player_data_all'][
            st.session_state['player_data_all']["unique_player_id"] == pick_unique_id
        ]
        
        if selected_player_row.empty:
            st.error("No matching player found to update. Please check filters.")
        else:
            # Get the ESPN ID to find ALL position variants of this player (e.g., Travis Hunter)
            pick_espn_id = selected_player_row.iloc[0]["espn_id"]
            
            # Mark ALL rows with this ESPN ID as drafted (handles multi-position eligible players)
            all_variants = st.session_state['player_data_all'][
                st.session_state['player_data_all']["espn_id"] == pick_espn_id
            ]
            
            # Also get same_name_group to handle duplicate names (e.g., two Josh Allens on BUF)
            same_name_group = selected_player_row.iloc[0].get("same_name_group", "")
            same_name_variants = st.session_state['player_data_all'][
                st.session_state['player_data_all']["same_name_group"] == same_name_group
            ] if same_name_group else pd.DataFrame()
            
            # Combine both: ESPN ID variants + same-name variants
            all_to_draft = pd.concat([all_variants, same_name_variants]).drop_duplicates(subset=["unique_player_id"])
            
            st.write(f"Removing {len(all_to_draft)} row(s):")
            st.write(all_to_draft[['name_x', 'position', 'team_x']])
            
            # Update all variants with same ESPN ID OR same name_team combo
            st.session_state['player_data_all'].loc[
                st.session_state['player_data_all']["unique_player_id"].isin(all_to_draft["unique_player_id"]), 
                "pick_number"
            ] = pick_number
            st.session_state['player_data_all'].loc[
                st.session_state['player_data_all']["unique_player_id"].isin(all_to_draft["unique_player_id"]), 
                "owner"
            ] = pick_league_team
            
            st.session_state['player_data_all'].to_csv(st.session_state['csv_filename'], index=False)
            st.success(f"Player {pick_name} ({pick_position} - {pick_team}) has been assigned to pick {pick_number} for team {pick_league_team}.")
            if len(all_to_draft) > 1:
                st.info(f"✓ All {len(all_to_draft)} player variants removed from board (includes same-name players)")
            st.success(f"Pick submitted to {st.session_state['csv_filename']}!")
            st.session_state["pick_number_input"] = st.session_state['player_data_all']['pick_number'].max() + 1
            # Hide the entry form after submission  This does not work but we are moving on
            if "hide_enter_pick" in globals():
                hide_enter_pick()
            else:
                st.session_state['show_enter_pick'] = False
