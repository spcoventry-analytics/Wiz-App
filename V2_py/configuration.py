# configuration.py
import streamlit as st

def show_configuration():
    st.title("Configuration")
    st.write("Select your league, user, and season. View the ESPN API credentials from Streamlit secrets.")

    st.markdown("""
    **ESPN API Setup**
    - Credentials are securely stored in Streamlit secrets.
    - **Do NOT share your ESPN_S2 and SWID values when pushing this app to Streamlit Cloud or any public repository.**
    - For help finding your cookies, see the [espn-api documentation](https://github.com/cwendt94/espn-api).
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

        # Print league.settings for inspection (as JSON for clarity)
        st.write("### League Settings Object:")
        st.json(vars(league.settings))

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
            st.write(f"**Draft Rounds:** {num_rounds}")
        else:
            st.warning("Could not fetch league name. Check credentials and season.")
    except Exception as e:
        st.error(f"Error connecting to ESPN API via espn-api package: {e}")
    

