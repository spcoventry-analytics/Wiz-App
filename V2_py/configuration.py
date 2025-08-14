# configuration.py
import streamlit as st
import pandas as pd
import requests
import time
import json
from bs4 import BeautifulSoup
from espn_api.football import League

def show_configuration():
    st.title("Configuration")
    st.write("Select your league, user, and season. View the ESPN API credentials from Streamlit secrets.")

    st.markdown("""
    **ESPN API Setup**
    https://www.pro-football-reference.com/
    https://apps.fantasyfootballanalytics.net/
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
            # Draft Rounds
            st.write(f"**Draft Rounds:** {num_rounds}")
        else:
            st.warning("Could not fetch league name. Check credentials and season.")
    except Exception as e:
            st.error(f"Error connecting to ESPN API via espn-api package: {e}")

        # Normalize player_map to always have player_id and name columns
    players_data = []
    for k, v in league.player_map.items():
        if isinstance(k, int) or (isinstance(k, str) and k.isdigit()):
            # id: name
            players_data.append({"player_id": k, "name": v})
        else:
            # name: id
            players_data.append({"player_id": v, "name": k})

    players_df = pd.DataFrame(players_data).drop_duplicates()
    st.write("### League Player Universe (IDs and Names only, unique)")
    st.dataframe(players_df)

    # Print league.settings for inspection (as JSON for clarity)
    st.write("### League Settings Object:")
    #st.json(vars(league.settings))
    st.write("### League Object:")
    #st.json(vars(league))

    st.write("League attributes and methods:")
    #st.write(dir(league))

    # from espn_api.football import Player
    # st.write("### Player Class Attributes and Methods:")
    # st.write(dir(Player))
    st.write("### I'll scrape so hard I'll cut a bitch:")
    # --- ESPN public site scraping for bio, stats, splits ---
    def get_espn_player_bio(player_id):
        url = f"https://www.espn.com/nfl/player/bio/_/id/{player_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        bio_data = {}
        # Try table first
        bio_table = soup.find('table')
        if bio_table:
            for row in bio_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) == 2:
                    bio_data[cells[0].text.strip()] = cells[1].text.strip()
        else:
            # Try Card Bio section (handle multiple class names)
            card_bio = soup.find('section', attrs={"data-testid": "bio"})
            if not card_bio:
                # Fallback: try by class name
                card_bio = soup.find('section', class_='Card Bio')
            if card_bio:
                items = card_bio.find_all('div', class_='Bio__Item')
                for item in items:
                    label = item.find('span', class_='Bio__Label')
                    value = item.find('span', class_='clr-gray-01')
                    if label and value:
                        # If value contains links, get text from link
                        link = value.find('a')
                        if link:
                            val_text = link.text.strip()
                        else:
                            val_text = value.text.strip()
                        bio_data[label.text.strip()] = val_text
        # Debug: If bio_data is empty, save raw HTML for inspection
        if not bio_data:
            with open(f"espn_players/player_{player_id}_bio_debug.html", "w", encoding="utf-8") as f:
                f.write(response.text)
        return bio_data

    def get_espn_player_stats(player_id):
        url = f"https://www.espn.com/nfl/player/stats/_/id/{player_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all tables and select the one with player stat categories
        stats_tables = soup.find_all('table')
        stats_data = {}
        stat_keywords = ["GP"]
        for table in stats_tables:
            # Get header row
            header_row = table.find('tr')
            if header_row:
                headers = [cell.text.strip() for cell in header_row.find_all(['th', 'td'])]
                # Check if this table is likely a player stats table
                if any(keyword in headers for keyword in stat_keywords):
                    key = 'Stats'
                    rows = []
                    for row in table.find_all('tr'):
                        cells = [cell.text.strip() for cell in row.find_all(['th', 'td'])]
                        rows.append(cells)
                    stats_data[key] = rows
                    break  # Only take the first matching stats table
        # If no player stats table found, fallback to previous logic
        if not stats_data:
            for table in stats_tables:
                caption = table.find('caption')
                key = caption.text.strip() if caption else 'Stats'
                rows = []
                for row in table.find_all('tr'):
                    cells = [cell.text.strip() for cell in row.find_all(['th', 'td'])]
                    rows.append(cells)
                stats_data[key] = rows
        return stats_data

    def get_espn_player_splits(player_id):
        url = f"https://www.espn.com/nfl/player/splits/_/id/{player_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        splits_tables = soup.find_all('table')
        splits_data = {}
        for table in splits_tables:
            caption = table.find('caption')
            key = caption.text.strip() if caption else 'Splits'
            rows = []
            for row in table.find_all('tr'):
                cells = [cell.text.strip() for cell in row.find_all(['th', 'td'])]
                rows.append(cells)
            splits_data[key] = rows
        return splits_data

