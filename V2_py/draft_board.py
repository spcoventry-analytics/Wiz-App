import streamlit as st

def show_draft_board():
    st.title("Draft Board")
    st.write("Draft board will display each team's picks in columns. Player data and pick status will be added once finalized.")

    # Get teams and rounds from session state
    teams = st.session_state.get('teams')
    num_rounds = st.session_state.get('num_rounds')

    if not teams or not num_rounds:
        st.warning("Draft board info not set. Please configure your league first.")
        return

    team_colors = {
        "Team 1": "#f94144", "Team 2": "#f3722c", "Team 3": "#f8961e", "Team 4": "#f9844a", "Team 5": "#f9c74f", "Team 6": "#90be6d", 
        "Team 7": "#43aa8b", "Team 8": "#4d908e", "Team 9": "#577590", "Team 10": "#219ebc", "Team 11": "#277DA1", "Team 12": "#0f4c5c"}
    position_colors = {
        "QB": "#9dd9d2", "RB": "#5c374c", "WR": "#392f5a", "TE": "#985277", 
        "DL": "#918450", "LB": "#d8c99b", "DB": "#585123", "Def": "#babd8d", 
        "K": "#c200fb"}

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
    cols = st.columns(len(teams))
    for idx, team in enumerate(teams):
        cols[idx].markdown(f"**{team}**")

    # Build table rows
    for rnd in rounds:
        cols = st.columns(len(teams))
        for idx, team in enumerate(teams):
            # Placeholder for player cell
            cols[idx].markdown(f"`Round {rnd}`\n*Player info here*\n<!-- Add color, keeper, traded pick, etc. -->")