import streamlit as st

def show_draft_board():
    st.title("Draft Board")
    st.write("Draft board will display each team's picks in columns. Player data and pick status will be added once finalized.")

    # Outline for draft board table
    teams = ["Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6", "Team 7", "Team 8", "Team 9", "Team 10", "Team 11", "Team 12"]  # Example team names
    rounds = list(range(1, 16))  # Example: 15 rounds

    # Build table header
    cols = st.columns(len(teams))
    for idx, team in enumerate(teams):
        cols[idx].markdown(f"**{team}**")

    # Build table rows
    for rnd in rounds:
        cols = st.columns(len(teams))
        for idx, team in enumerate(teams):
            # Placeholder for player cell
            # TODO: When player data is finalized, display:
            # - Player name
            # - Player position (color coded)
            # - Keeper status (if applicable)
            # - Traded pick indicator (if pick belongs to another team)
            # - Any other relevant info
            cols[idx].markdown(f"`Round {rnd}`\n*Player info here*\n<!-- Add color, keeper, traded pick, etc. -->")