import streamlit as st
import pandas as pd

def show_draft_board():
    st.title("Draft Board")
    st.write("Draft board will display each team's picks in columns. Player data and pick status will be added once finalized.")

    position_colors = st.session_state.get('position_colors', {})
    team_colors = [
        "#f94144", "#f3722c", "#f8961e", "#f9844a", "#f9c74f", "#90be6d",
        "#43aa8b", "#4d908e", "#577590", "#219ebc", "#277DA1", "#0f4c5c"
    ]

    # Get teams and rounds from session state
    teams = st.session_state.get('teams')
    num_rounds = st.session_state.get('num_rounds')
    draft_order = st.session_state.get('draft_order', teams)
    
    if not teams or not num_rounds:
        st.warning("Draft board info not set. Please configure your league first.")
        return

    match_team_colors = {}
    match_team_colors['color'] = team_colors[:len(teams)] if teams else []

    # board_setup = st.session_state.get('draft_order', st.session_state.get('teams', []))
    # board_setup["picks"] = []
    # board_setup["rounds"] = []
    # board_setup["draft_picks"] = []
    # board_setup["cells"] = [[] for _ in range(num_rounds)]

    draft_picks = st.session_state.get('player_data_all', [])
    draft_picks = draft_picks[draft_picks['pick_number'] > 0]  # Filter out unpicked players

    num_rounds = st.session_state.get('num_rounds')

    def draft_card(pick):
        player = st.session_state['player_data'].get(pick['espn_id'], {}).get('name', 'Unknown Player')
        team_bg = team_colors.get(pick['team'], "#FFFFFF")
        pos_color = position_colors.get(pick['position'], "#CCCCCC")
        st.markdown(
            f"""
            <div style="background-color:{team_bg};padding:10px;border-radius:8px;margin-bottom:10px;">
            <span style="border:2px solid {pos_color};padding:5px 10px;border-radius:5px;">
                <b>{player}</b> ({pick['position']})
            </span>
            <br>
            <small>{pick['team']}</small>
            </div>
            """,
            unsafe_allow_html=True
        )
    rounds = list(range(1, num_rounds + 1))

    # Build table header
    draft_order = st.session_state.get('draft_order', teams)
    cols = st.columns(len(draft_order))
    for idx, team in enumerate(draft_order):
        cols[idx].markdown(f"**{team}**")

    # Build table rows
    draft_picks = st.session_state.get('player_data_all', pd.DataFrame())
    num_teams = len(draft_order)
    for rnd in rounds:
        cols = st.columns(num_teams)
        for idx, team in enumerate(draft_order):
            # Find picks for this team in this round
            team_picks = draft_picks[
                (draft_picks['owner'] == team) &
                (draft_picks['pick_number'] > 0) &
                (((draft_picks['pick_number'] - 1) // num_teams) + 1 == rnd)
            ]
            if not team_picks.empty:
                for _, pick in team_picks.iterrows():
                    cols[idx].markdown(f"`Round {rnd}` ({pick['position']}) \n **{pick['name_x']}**")
            else:
                cols[idx].markdown(f"`Round {rnd}`\n*No pick*")