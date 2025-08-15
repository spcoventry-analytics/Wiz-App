# consider_options.py
import streamlit as st

def show_consider_options():
    st.title("Consider Options")
    st.write("Space to consider options here.")
    st.write("### Merged Player Data:")
    player_data_all = st.session_state.get('player_data_all')
    st.dataframe(player_data_all)
    keep_columns = ['name_x', 'position', 'team_x', # Who
                    'points', 'floor', 'ceiling', 'position_rank', "tier", 'adp',  # What
                    'age', 'college', 'draft_year_x', 'weight', 'espn_id', # Profile
    ] # History
    player_data = player_data_all[keep_columns]
    player_data["pick_number"] = 0
    st.write("### What will appear on picks:")
    st.dataframe(player_data)
    st.session_state['player_summary'] = player_data
