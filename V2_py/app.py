import streamlit as st
from streamlit_option_menu import option_menu
import requests
import os
import pandas as pd
import glob

# Import page modules
from draft_board import show_draft_board
from enter_pick import show_enter_pick
from consider_options import show_consider_options
from current_plan import show_current_plan
from configuration import show_configuration

from espn_api.football import League

# Set page config for mobile friendliness
st.set_page_config(page_title="Fantasy Football Draft Board", layout="wide")

# Auto-resume existing draft on startup
def auto_resume_existing_draft():
    """Load the latest draft CSV if one exists and hasn't been loaded yet."""
    if st.session_state.get('draft_loaded', False):
        return  # Already loaded
    
    # Find the latest draft_results_*.csv file by modification time
    draft_files = glob.glob("draft_results_*.csv")
    if not draft_files:
        return  # No draft file found
    
    latest_file = max(draft_files, key=os.path.getmtime)
    
    try:
        # Load the draft CSV
        st.session_state['player_data_all'] = pd.read_csv(latest_file)
        
        # Ensure same_name_group column exists (for backwards compatibility)
        if 'same_name_group' not in st.session_state['player_data_all'].columns:
            st.session_state['player_data_all']['same_name_group'] = (
                st.session_state['player_data_all']['name_x'].fillna("") + "_" + 
                st.session_state['player_data_all']['team_x'].fillna("FA").astype(str)
            )
            st.session_state['player_data_all'].to_csv(latest_file, index=False)
        
        st.session_state['csv_filename'] = latest_file
        st.session_state['draft_loaded'] = True
        
        # Extract league_id and season_id from filename (e.g., draft_results_54926_2025.csv)
        parts = latest_file.replace("draft_results_", "").replace(".csv", "").split("_")
        if len(parts) >= 2:
            st.session_state['league_id'] = parts[0]
            st.session_state['season_id'] = parts[1]
    except Exception as e:
        st.warning(f"Could not auto-resume draft from {latest_file}: {e}")

# Call auto-resume before rendering anything
auto_resume_existing_draft()

# Icon-based menu bar across the top
selected = option_menu(
    menu_title=None,
    options=[
        "Current Board",
        "Consider Options",
        "Current Plan",
        "Configuration",
    ],
    icons=[
        "table",
        "search",
        "clipboard-check",
        "gear",
    ],
    orientation="horizontal",
    default_index=0,
    styles={
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "icon": {"color": "#2c3e50", "font-size": "20px"},
        "nav-link": {"font-size": "18px", "text-align": "center", "margin": "0px"},
        "nav-link-selected": {"background-color": "#e0e0e0"},
    }
)

st.session_state['position_colors'] = {
    "QB": "#336699", "RB": "#9ee493", "WR": "#86bbd8", "TE": "#2f4858", 
    "DL": "#7d82b8", "LB": "#613f75", "DB": "#e5c3d1", "Def": "#babd8d", 
    "K": "#5465ff"}


# Display content based on menu selection with Enter Pick toggle
if 'show_enter_pick' not in st.session_state:
    st.session_state['show_enter_pick'] = False

def hide_enter_pick():
    st.session_state['show_enter_pick'] = False

def activate_enter_pick():
    st.session_state['show_enter_pick'] = True

if selected == "Current Board":
    if st.button("Enter Pick", use_container_width=True):
        activate_enter_pick()
    if st.session_state['show_enter_pick']:
        show_enter_pick()
        if st.button("Hide Enter Pick", use_container_width=True):
            hide_enter_pick()
    show_draft_board()
elif selected == "Consider Options":
    if st.button("Enter Pick", use_container_width=True):
        activate_enter_pick()
    if st.session_state['show_enter_pick']:
        show_enter_pick()
        if st.button("Hide Enter Pick", use_container_width=True):
            hide_enter_pick()
    show_consider_options()
elif selected == "Current Plan":
    if st.button("Enter Pick", use_container_width=True):
        activate_enter_pick()
    if st.session_state['show_enter_pick']:
        show_enter_pick()
        if st.button("Hide Enter Pick", use_container_width=True):
            hide_enter_pick()
    show_current_plan()
elif selected == "Configuration":
    show_configuration()

# Check for configuration link in hash
if st.session_state.get('show_config', False) or st.query_params.get('config', [''])[0] == '1' or st.query_params.get('Configuration', [''])[0] == '':
    if st.query_params.get('Configuration', None) == '':
        show_configuration()

# Footer with configuration link
st.markdown("<hr style='margin-top: 2em; margin-bottom: 0.5em;'>", unsafe_allow_html=True)
footer_html = """
<div style='text-align: center; color: #888;'>
    App by Spcoventry Analytics
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
