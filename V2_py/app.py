import streamlit as st
from streamlit_option_menu import option_menu
import requests

# Import page modules
from draft_board import show_draft_board
from enter_pick import show_enter_pick
from consider_options import show_consider_options
from current_plan import show_current_plan
from configuration import show_configuration
# Football API
from espn_api.football import League

# Set page config for mobile friendliness
st.set_page_config(page_title="Fantasy Football Draft Board", layout="wide")

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
