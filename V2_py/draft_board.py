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

    # EDIT FORM (RENDER FIRST so it shows at top)
    if st.session_state.get('edit_pick_mode', False):
        st.info("### ✏️ Edit Pick")
        
        # Find the pick being edited
        edit_pick = st.session_state['player_data_all'][
            st.session_state['player_data_all']['unique_player_id'] == st.session_state.get('edit_pick_id')
        ]
        
        if not edit_pick.empty:
            pick_row = edit_pick.iloc[0]
            st.write(f"**Pick #{st.session_state.get('edit_pick_number')}:** {pick_row['name_x']} ({pick_row['position']}) - {pick_row['team_x']}")
            st.write(f"**Currently drafted by:** {pick_row['owner']}")
            
            col1, col2 = st.columns(2)
            
            # Edit pick number
            with col1:
                new_pick_number = st.number_input(
                    "Pick Number",
                    min_value=1,
                    value=int(st.session_state.get('edit_pick_number', 1)),
                    key="edit_pick_number_input"
                )
            
            # Edit team
            with col2:
                new_team = st.selectbox(
                    "League Team",
                    draft_order,
                    index=draft_order.index(pick_row['owner']) if pick_row['owner'] in draft_order else 0,
                    key="edit_team_select"
                )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✓ Save Changes", key="save_edit_pick"):
                    # Update both pick number and owner
                    st.session_state['player_data_all'].loc[
                        st.session_state['player_data_all']['unique_player_id'] == st.session_state['edit_pick_id'],
                        'pick_number'
                    ] = new_pick_number
                    st.session_state['player_data_all'].loc[
                        st.session_state['player_data_all']['unique_player_id'] == st.session_state['edit_pick_id'],
                        'owner'
                    ] = new_team
                    st.session_state['player_data_all'].to_csv(st.session_state['csv_filename'], index=False)
                    st.session_state['edit_pick_mode'] = False
                    st.success(f"✓ Pick updated to #{new_pick_number} for {new_team}!")
                    st.rerun()
            
            with col2:
                if st.button("✕ Cancel", key="cancel_edit_pick"):
                    st.session_state['edit_pick_mode'] = False
                    st.rerun()
        st.divider()
    
    # DRAFT BOARD (RENDER BELOW EDIT FORM)
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
                    # Show pick number, fantasy team owner, position, player name, and NFL team
                    display_text = f"""**#{int(pick['pick_number'])}** | ({pick['position']}) - ({pick['team_x']}) 
                    \n **{pick['name_x']}** """
                    col1, col2 = cols[idx].columns([3, 1])
                    col1.markdown(display_text)
                    if col2.button("✏️", key=f"edit_pick_{int(pick['pick_number'])}"):
                        st.session_state['edit_pick_mode'] = True
                        st.session_state['edit_pick_id'] = pick['unique_player_id']
                        st.session_state['edit_pick_number'] = int(pick['pick_number'])
                        st.rerun()
            else:
                cols[idx].markdown(f"`Round {rnd}`\n*No pick*")