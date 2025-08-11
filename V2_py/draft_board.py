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