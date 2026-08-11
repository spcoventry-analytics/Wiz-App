# configuration.py
import streamlit as st
import pandas as pd
import requests
import time
import json
import nfl_data_py as nfl

from bs4 import BeautifulSoup
from espn_api.football import League


def show_configuration():
    st.title("Configuration")
    st.write("Select your league, user, and season. View the ESPN API credentials from Streamlit secrets.")

    st.markdown("""
    **ESPN API Setup**
    https://www.pro-football-reference.com/
    https://apps.fantasyfootballanalytics.net/
    """)

    family_users = ["stephen", "courtney", "adrianne", "beka", "patric", "evi", "victoria"]

    league_options = {
        "Cujos League": {
            "league_id": st.secrets.get("cujos_league_id", ""),
            "espn_s2": st.secrets.get("stephen_espn_s2", ""),
            "swid": st.secrets.get("stephen_swid", "")
        },
        "Family League": None  # Will be set below
    }

    selected_league = st.selectbox("Select League", list(league_options.keys()))

    if selected_league == "Family League":
        selected_user = st.selectbox("Select User", family_users)
        creds = {
            "league_id": st.secrets.get("family_league_id", ""),
            "espn_s2": st.secrets.get(f"{selected_user}_espn_s2", ""),
            "swid": st.secrets.get(f"{selected_user}_swid", "")
        }
    else:
        creds = league_options[selected_league]

    season_id = st.text_input("Season ID (Year)", value="2025", help="Enter the fantasy football season year.")

    st.write(f"**League ID:** {creds['league_id']}")
    st.write(f"**Season ID:** {season_id}")

    # Store selected league/user/season in session state for use elsewhere
    st.session_state['league_id'] = creds['league_id']
    st.session_state['espn_s2'] = creds['espn_s2']
    st.session_state['swid'] = creds['swid']
    st.session_state['season_id'] = season_id

    # Fetch and display league name using espn-api package
    try:
        from espn_api.football import League
        league = League(
            league_id=creds['league_id'],
            year=int(season_id),
            espn_s2=creds['espn_s2'],
            swid=creds['swid']
        )
        league_name = getattr(league.settings, 'name', None)
        teams = [team.team_name for team in league.teams]

        # Calculate draft rounds from position_slot_counts
        slot_counts = getattr(league.settings, 'position_slot_counts', {})
        num_rounds = sum(
            v for k, v in slot_counts.items() if k not in ["IR", ""]
        )
        st.session_state['teams'] = teams
        st.session_state['num_rounds'] = num_rounds
        
        if league_name:
            st.success(f"Connected to league: {league_name}")
            st.write("### Teams in this league:")
            for team in teams:
                st.write(team)
            # Draft Rounds
            st.write(f"**Draft Rounds:** {num_rounds}")

            # Draft Order UI
            st.write("### Set Draft Order (enter a number for each team)")
            draft_order_inputs = {}
            for team in teams:
                draft_order_inputs[team] = st.number_input(f"Draft position for {team}", min_value=1, max_value=len(teams), step=1, value=teams.index(team)+1, key=f"draft_order_{team}")
            # Sort teams by entered draft position
            sorted_teams = sorted(teams, key=lambda t: draft_order_inputs[t])
            st.session_state['draft_order'] = sorted_teams
            st.write("Current Draft Order:", st.session_state['draft_order'])
        else:
            st.warning("Could not fetch league name. Check credentials and season.")
    except Exception as e:
            st.error(f"Error connecting to ESPN API via espn-api package: {e}")
            return
    st.session_state['csv_filename'] = f"draft_results_{st.session_state['league_id']}_{st.session_state['season_id']}.csv"
    
    # Check if draft CSV exists
    import os
    draft_exists = os.path.exists(st.session_state['csv_filename'])
    
    # Let user choose: load existing or start fresh
    col1, col2 = st.columns(2)
    with col1:
        load_existing = st.button("📂 Load Existing Draft", disabled=not draft_exists)
    with col2:
        start_fresh = st.button("🆕 Start Fresh Draft")
    
    if start_fresh:
        st.session_state['force_fresh_draft'] = True
        st.rerun()
    
    if draft_exists and not st.session_state.get('force_fresh_draft', False):
        if load_existing:
            st.session_state['player_data_all'] = pd.read_csv(st.session_state['csv_filename'])
            st.success(f"Loaded draft CSV: {st.session_state['csv_filename']}")
        else:
            st.info(f"Existing draft found: {st.session_state['csv_filename']} — Click 'Load Existing Draft' to resume or 'Start Fresh' for a new draft")
            return
    
    if st.session_state.get('force_fresh_draft', False) or not draft_exists:
        try:
            # Force fresh draft if user clicked button or no file exists
            if draft_exists and st.session_state.get('force_fresh_draft', False):
                st.warning(f"Starting fresh draft — deleting {st.session_state['csv_filename']}")
                os.remove(st.session_state['csv_filename'])
                st.session_state['force_fresh_draft'] = False
        except Exception as e:
            st.error(f"Could not delete existing file: {e}")
            return
    
    try:
        # Normalize player_map to always have player_id and name columns
        players_data = []
        for k, v in league.player_map.items():
            if isinstance(k, int) or (isinstance(k, str) and k.isdigit()):
                # id: name
                players_data.append({"player_id": k, "name": v})
            else:
                # name: id
                players_data.append({"player_id": v, "name": k})
        espn_players_df = pd.DataFrame(players_data).drop_duplicates()
        #st.write("### League Player Universe (IDs and Names only, unique)")
        #st.dataframe(espn_players_df)

        # Print league.settings for inspection (as JSON for clarity)
        #st.write("### League Settings Object:")
        #st.json(vars(league.settings))
        #st.write("### League Object:")
        #st.json(vars(league))
        #st.write("League attributes and methods:")
        #st.write(dir(league))

        # Display the player_map as a DataFrame
        #st.write("### Player Class ID crosswalk:")
        crosswalk = nfl.import_ids()
        #st.write(crosswalk)  # Uncomment to display the crosswalk data

        # Merge Data
        merged_data = pd.merge(espn_players_df, crosswalk, left_on="player_id", right_on="espn_id", how="left")
        if selected_league == "Cujos League":
            cujos_raw = pd.read_csv("cujos_raw_stats_2025_wk0.csv")  # This was a rush option Is should have folders for each league and let it pick the year.
            st.write("### Cujos Raw Data:")
            merged_data = pd.merge(merged_data, cujos_raw, left_on="mfl_id", right_on="id", how="left")
            cujos_proj = pd.read_csv("cujos_projections_2025_wk0.csv")  # Assuming this is the projection data
            merged_data = pd.merge(merged_data, cujos_proj, left_on="player", right_on="player", how="left")
        if selected_league == "Family League":
            family_raw = pd.read_csv("family_raw_stats_2025_wk0.csv")
            st.write("### Family Raw Data:")
            merged_data = pd.merge(merged_data, family_raw, left_on="mfl_id", right_on="id", how="left")
            family_proj = pd.read_csv("family_projections_2025_wk0.csv")
            merged_data = pd.merge(merged_data, family_proj, left_on="player", right_on="player", how="left")
        st.write("### Merged Player Data:")

        # IMPORTANT: Create unique player identifier (name + position + team)
        # This allows multi-position eligible players (Travis Hunter) AND handles different players with same name
        merged_data["points"] = pd.to_numeric(merged_data["points"], errors="coerce")
        merged_data["team_x"] = merged_data["team_x"].fillna("FA").astype(str)
        merged_data["position"] = merged_data["position"].fillna("UNK").astype(str)
        
        # Create unique_player_id: "name_position_team" to avoid cross-position picks
        merged_data["unique_player_id"] = (
            merged_data["name_x"].fillna("") + "_" + 
            merged_data["position"] + "_" + 
            merged_data["team_x"]
        )
        
        # Check for actual duplicates (same unique_player_id from merge errors)
        # Keep only the row with the highest projected points for true duplicates
        if merged_data.duplicated(subset=["unique_player_id"], keep=False).any():
            merged_data = merged_data.sort_values("points", ascending=False, na_position="last")
            merged_data = merged_data.drop_duplicates(subset=["unique_player_id"], keep="first")
        
        merged_data["pick_number"] = 0
        merged_data["owner"] = ""
        merged_data["PPG"] = merged_data["points"] / 17
        merged_data = merged_data.sort_values("PPG", ascending=False)
        merged_data["depth"] = merged_data.apply(
            lambda row: (
                9 if pd.isnull(row["team_x"]) or pd.isnull(row["position"]) or pd.isnull(row["points"])
                else merged_data[
                    (merged_data["team_x"] == row["team_x"]) &
                    (merged_data["position"] == row["position"]) &
                    (merged_data["points"] >= row["points"])
                ].shape[0]
            ),
            axis=1
        )
        #merged_data["team_x"].fillna("FA", inplace=True)
        #merged_data["team_x"].replace(None, "FA", inplace=True)
        st.session_state['player_data_all'] = merged_data
        st.session_state['player_data_all'].to_csv(st.session_state['csv_filename'], index=False)
        st.success(f"Draft csv created: {st.session_state['csv_filename']}!")
    except Exception as e:
        st.error(f"Error creating player data: {e}")
        return

    keep_columns = ['name_x', 'position', 'team_x', # who 
                   'points', 'floor', 'ceiling', 'position_rank', "tier", 'adp', "depth", # what
                   'age', 'college', 'draft_year_x', 'weight', 'PPG', 'espn_id', "pick_number"] # Bio and History would be next
    st.session_state['player_summary'] = st.session_state['player_data_all'][keep_columns]
    st.write("### Next pick after loading:")
    st.session_state["pick_number_input"] = st.session_state['player_data_all']['pick_number'].max() + 1
    st.write(st.session_state["pick_number_input"])
    st.write("### Key Facts:")
    st.dataframe(st.session_state['player_summary'])