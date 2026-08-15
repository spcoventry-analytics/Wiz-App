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
from config_manager import ConfigManager

from espn_api.football import League

# Set page config for mobile friendliness
st.set_page_config(page_title="Fantasy Football Draft Board", layout="wide")

# Load config on startup
def load_config_on_startup():
    """Load the latest config file and populate session state."""
    if st.session_state.get('config_loaded', False):
        return  # Already loaded
    
    config = ConfigManager.get_latest_config()
    if config:
        league_info = ConfigManager.extract_league_info(config)
        st.session_state['league_id'] = league_info['league_id']
        st.session_state['season_id'] = league_info['season_id']
        st.session_state['teams'] = league_info['draft_order']
        st.session_state['my_team'] = league_info['my_team']
        st.session_state['draft_order'] = league_info['draft_order']
        st.session_state['keepers'] = league_info['keepers']
        st.session_state['current_config_file'] = None  # Will be set after finding matching draft file
        st.session_state['current_plan'] = config.get('current_plan', {})
        st.session_state['config_loaded'] = True
        
        # Fetch ESPN league info to populate slot_counts, position_colors, tier_baselines
        try:
            espn_s2 = st.secrets.get("stephen_espn_s2")
            swid = st.secrets.get("stephen_swid")
            
            if espn_s2 and swid:
                league = League(league_id=int(league_info['league_id']), year=int(league_info['season_id']), espn_s2=espn_s2, swid=swid)
                
                # Extract slot_counts from league.settings.position_slot_counts
                # Using same logic as configuration.py: separate FLEX from regular positions
                if hasattr(league.settings, 'position_slot_counts'):
                    position_slot_counts = league.settings.position_slot_counts
                    
                    # Separate FLEX positions (contain "/") from regular positions
                    slot_counts = {}
                    flex_positions = {}
                    
                    for pos, count in position_slot_counts.items():
                        if count > 0 and pos not in ["BN", "BE", "IR", ""]:
                            if "/" in pos:  # FLEX position
                                flex_positions[pos] = count
                            else:  # Regular position
                                slot_counts[pos] = count
                    
                    st.session_state['slot_counts'] = slot_counts
                    st.session_state['flex_positions'] = flex_positions
                
                # Set up position colors (user's preferred scheme)
                position_colors = {
                    'QB': '#669bbc', 'RB': '#588157', 'WR': '#005D8F', 'TE': '#335c67',
                    'DL': '#ee9b00', 'LB': '#ca6702', 'CB': '#bb3e03', 'DB': '#bb3e03',
                    'DEF': '#ca6702', 'K': '#888888'
                }
                st.session_state['position_colors'] = position_colors
                
                # Calculate tier baselines from league settings
                # Placeholder: will be calculated during draft_board init
                st.session_state['tier_baselines'] = {}
        except Exception as e:
            # If ESPN fetch fails, continue without slot_counts (tabs will show error)
            pass

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
        
        # Calculate tier baselines from player data
        calculate_tier_baselines()
    except Exception as e:
        st.warning(f"Could not auto-resume draft from {latest_file}: {e}")

def calculate_tier_baselines():
    """Calculate PPG baseline for each position tier based on slot_counts and player data."""
    player_data = st.session_state.get('player_data_all')
    slot_counts = st.session_state.get('slot_counts', {})
    num_teams = len(st.session_state.get('draft_order', []))
    
    if player_data is None or player_data.empty or not slot_counts or num_teams == 0:
        st.session_state['tier_baselines'] = {}
        return
    
    tier_baselines = {}
    
    for pos in slot_counts.keys():
        # Skip non-positions
        if pos in ["IR", "", "FLEX", "BENCH", "BE"] or "/" in pos:
            continue
        
        num_starting_slots = slot_counts.get(pos, 0) * num_teams
        pos_players = player_data[player_data['position'] == pos].sort_values('PPG', ascending=False)
        
        tier_baselines[pos] = {}
        
        for tier_num in range(slot_counts.get(pos, 0)):
            # Get the average PPG for this tier (league average if distributed one per team)
            tier_start_idx = tier_num * num_teams
            tier_end_idx = (tier_num + 1) * num_teams
            tier_players = pos_players.iloc[tier_start_idx:tier_end_idx]
            
            if not tier_players.empty:
                baseline_ppg = tier_players['PPG'].mean()
                tier_baselines[pos][tier_num] = baseline_ppg
            else:
                tier_baselines[pos][tier_num] = 0
    
    st.session_state['tier_baselines'] = tier_baselines

# Load config and draft in order
load_config_on_startup()
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
