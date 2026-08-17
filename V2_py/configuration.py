# configuration.py
import streamlit as st
import pandas as pd
import json
import glob
import os
from config_manager import ConfigManager
from espn_api.football import League


def normalize_position(pos):
    """
    Normalize position variants to standard positions.
    Maps granular positions (CB, S, DE, DT, etc.) to standard positions (DB, DL, etc.)
    
    Mappings:
    - CB, S → DB (Cornerback, Safety → Defensive Back)
    - DE, DT → DL (Defensive End, Defensive Tackle → Defensive Line)
    - Other positions pass through unchanged
    """
    if not pos or pos in ["", "UNK", None]:
        return pos
    
    pos = str(pos).upper()
    
    # Defensive backs
    if pos in ["CB", "S"]:
        return "DB"
    # Defensive line
    if pos in ["DE", "DT"]:
        return "DL"
    
    # Pass through unchanged
    return pos


def show_configuration():
    st.title("Configuration")
    
    st.write("Manage your draft setup and configurations.")
    
    # === MAIN WORKFLOW SELECTION ===
    st.markdown("---")
    st.subheader("📋 What would you like to do?")
    
    workflow = st.radio(
        "Select workflow:",
        ["🆕 Start New League Config", "✏️ Edit Existing Config", "🎯 Practice from Existing Config", "🏆 Live Draft"],
        horizontal=True
    )
    
    # === WORKFLOW 1: START NEW LEAGUE CONFIG ===
    if workflow == "🆕 Start New League Config":
        st.write("**Create a new league configuration with keepers**")
        
        # Initialize fetch state
        if 'league_fetched' not in st.session_state:
            st.session_state['league_fetched'] = False
        if 'fetched_league_obj' not in st.session_state:
            st.session_state['fetched_league_obj'] = None
        if 'available_positions' not in st.session_state:
            st.session_state['available_positions'] = []
        if 'available_player_names' not in st.session_state:
            st.session_state['available_player_names'] = []
        
        col1, col2 = st.columns(2)
        with col1:
            league_id = st.text_input("League ID", help="ESPN League ID", key="config_league_id")
            season_id = st.text_input("Season ID (Year)", value="2026", help="Fantasy football season year", key="config_season_id")
        
        with col2:
            st.write("")  # Spacing
            st.write("")
            if st.button("🔄 Fetch League Info from ESPN", use_container_width=True):
                if league_id and season_id:
                    try:
                        with st.spinner("Fetching league data..."):
                            # Get ESPN credentials from secrets
                            espn_s2 = st.secrets.get("stephen_espn_s2")
                            swid = st.secrets.get("stephen_swid")
                            
                            # Create league object with credentials if available
                            if espn_s2 and swid:
                                league = League(league_id=int(league_id), year=int(season_id), espn_s2=espn_s2, swid=swid)
                            else:
                                league = League(league_id=int(league_id), year=int(season_id))
                            
                            st.session_state['fetched_league_obj'] = league
                            
                            # Extract league name (try multiple attribute paths)
                            league_name = getattr(league, 'league_name', None)
                            if not league_name and hasattr(league, 'settings'):
                                league_name = getattr(league.settings, 'name', f"League {league_id}")
                            
                            # Extract positions from league settings (scoring format defines eligible positions)
                            positions = []
                            flex_positions = {}  # Store FLEX information for value calculations
                            
                            # Try multiple ways to get positions
                            if hasattr(league, 'settings'):
                                # Method 1: position_slot_counts (THIS IS THE KEY!)
                                if hasattr(league.settings, 'position_slot_counts'):
                                    position_slot_counts = league.settings.position_slot_counts
                                    
                                    # Extract positions: only actual positions (not FLEX, not bench, not empty)
                                    for pos, count in position_slot_counts.items():
                                        if count > 0 and pos not in ["BN", "BE", "IR", ""]:
                                            # Skip FLEX positions (contain /) - store separately for value calc
                                            if "/" in pos:
                                                flex_positions[pos] = count
                                            else:
                                                positions.append(pos)
                                    
                                    st.write(f"✅ **Extracted {len(positions)} positions**: {sorted(positions)}")
                                    if flex_positions:
                                        st.write(f"📋 **FLEX slots** (for value calculations): {flex_positions}")
                                else:
                                    st.write("❌ position_slot_counts not found")
                                
                                # Method 2: _raw_scoring_settings (fallback)
                                if not positions and hasattr(league.settings, '_raw_scoring_settings'):
                                    st.write("Using _raw_scoring_settings as fallback...")
                                    scoring_settings = league.settings._raw_scoring_settings
                                    if isinstance(scoring_settings, dict):
                                        for pos_key, pos_data in scoring_settings.items():
                                            if pos_key not in ["BN", "BE", "IR", ""]:
                                                if "/" not in pos_key:
                                                    positions.append(pos_key)
                                                else:
                                                    flex_positions[pos_key] = 1
                            else:
                                st.write("❌ league.settings does NOT exist")
                            
                            # Remove duplicates and sort
                            positions = sorted(list(set(positions)))
                            
                            # Fallback to common positions if not found in settings
                            if not positions:
                                st.write("⚠️ Using fallback positions (extraction failed)")
                                positions = ["QB", "RB", "WR", "TE", "DEF", "K"]
                            
                            st.session_state['available_positions'] = positions
                            st.session_state['flex_positions'] = flex_positions  # Store for later use
                            
                            # Extract player data with positions from league
                            # Build a dict of player_name -> position from league
                            player_position_map = {}  # player_name -> set of positions
                            
                            # Try to get player data from league.teams or league object
                            if hasattr(league, 'teams'):
                                for team in league.teams:
                                    if hasattr(team, 'roster'):
                                        for player in team.roster:
                                            player_name = getattr(player, 'name', None)
                                            player_pos = getattr(player, 'eligibleSlots', None)
                                            if player_name:
                                                if player_name not in player_position_map:
                                                    player_position_map[player_name] = set()
                                                if player_pos:
                                                    if isinstance(player_pos, list):
                                                        player_position_map[player_name].update(player_pos)
                                                    else:
                                                        player_position_map[player_name].add(str(player_pos))
                                                # Note: If no position data, player_position_map[player_name] will be empty set
                            
                            # Also extract from player_map as fallback
                            if hasattr(league, 'player_map'):
                                for k, v in league.player_map.items():
                                    if isinstance(v, str) and v not in player_position_map:
                                        player_position_map[v] = set()
                                    elif isinstance(k, str) and k not in player_position_map:
                                        player_position_map[k] = set()
                            
                            st.session_state['player_position_map'] = player_position_map
                            st.session_state['available_player_names'] = sorted(list(player_position_map.keys()))
                            st.session_state['league_fetched'] = True
                            
                            st.success(f"✅ Fetched league: {league_name} ({len(league.teams)} teams)")
                            st.info(f"✓ {len(st.session_state['available_player_names'])} players loaded")
                            st.info(f"✓ Positions: {', '.join(positions)}")
                    except Exception as e:
                        st.error(f"❌ Failed to fetch league: {e}")
                        st.error("ESPN fetch is **required** — it provides:")
                        st.error("  • Player universe and ADP data")
                        st.error("  • Position eligibility rules")
                        st.error("  • Scoring settings")
                        st.info("Please verify:")
                        st.info("  • League ID is correct")
                        st.info("  • ESPN credentials in .streamlit/secrets.toml are valid")
                else:
                    st.error("Please enter League ID and Season ID")
        
        # Require ESPN fetch before proceeding
        if not st.session_state.get('league_fetched', False):
            st.warning("⚠️ Please fetch league info first (ESPN data is required for player universe, positions, and scoring)")
            st.stop()
        
        # Draft order setup
        st.write("### Draft Order")
        num_teams = st.number_input("Number of Teams", min_value=2, max_value=16, value=10, step=1, key="config_num_teams")
        
        draft_order = []
        team_cols = st.columns(2)
        for i in range(num_teams):
            col_idx = i % 2
            with team_cols[col_idx]:
                team_name = st.text_input(f"Team {i+1} Name", key=f"new_team_{i}")
                if team_name:
                    draft_order.append(team_name)
        
        # Your team selection
        st.write("### Your Team")
        my_team = st.selectbox("Which team are you managing?", draft_order if draft_order else ["No teams entered yet"], key="new_my_team")
        
        # Keepers setup
        st.write("### Keepers by Team (Snake Draft)")
        keepers = {}
        
        # Get available positions and player data
        available_positions = st.session_state.get('available_positions', ["QB", "RB", "WR", "TE", "DEF", "K"])
        player_position_map = st.session_state.get('player_position_map', {})
        all_player_names = st.session_state.get('available_player_names', [])
        
        for team_idx, team in enumerate(draft_order):
            with st.expander(f"**{team}** - Add Keepers"):
                num_keepers = st.number_input(
                    f"Number of keepers for {team}", 
                    min_value=0, 
                    max_value=3, 
                    value=0, 
                    step=1, 
                    key=f"num_keepers_{team}"
                )
                
                team_keepers = []
                for k_idx in range(num_keepers):
                    col1, col2, col3 = st.columns(3)
                    
                    # Position comes first (to filter players)
                    with col2:
                        position = st.selectbox(
                            "Position",
                            available_positions,
                            key=f"keeper_pos_{team}_{k_idx}",
                            help="Select position to filter players"
                        )
                    
                    # Filter players by selected position
                    position_players = []
                    if position and player_position_map:
                        # Find players eligible for this position
                        for player_name, positions_set in player_position_map.items():
                            if position in positions_set or not positions_set:
                                position_players.append(player_name)
                        position_players = sorted(position_players)
                    elif not player_position_map:
                        # Fallback if no position data
                        position_players = all_player_names
                    else:
                        position_players = all_player_names
                    
                    # Player name (filtered by position)
                    with col1:
                        if position_players:
                            player_name = st.selectbox(
                                "Player Name",
                                position_players,
                                key=f"keeper_player_{team}_{k_idx}",
                                help=f"Players eligible for {position}"
                            )
                        else:
                            player_name = st.text_input(
                                "Player Name",
                                key=f"keeper_player_{team}_{k_idx}",
                                help=f"No players found for {position}"
                            )
                    
                    # Pick number (snake draft calculation)
                    with col3:
                        # Snake draft formula: alternating draft order per round
                        if k_idx % 2 == 0:  # Even keeper round (0, 2, 4...)
                            keeper_pick = k_idx * num_teams + team_idx + 1
                        else:  # Odd keeper round (1, 3, 5...)
                            keeper_pick = (k_idx + 1) * num_teams - team_idx
                        
                        pick_num = st.number_input(
                            "Pick #",
                            value=int(keeper_pick),
                            min_value=1,
                            max_value=300,
                            step=1,
                            key=f"keeper_pick_{team}_{k_idx}",
                            help=f"Snake draft (default: {keeper_pick})"
                        )
                    
                    if player_name:
                        team_keepers.append({
                            "player": player_name,
                            "position": position,
                            "pick": int(pick_num)
                        })
                
                keepers[team] = team_keepers
        
        # Save new config
        if st.button("✅ Create Config", use_container_width=True):
            if league_id and season_id and draft_order and my_team:
                new_config = {
                    "league_id": int(league_id),
                    "season_id": int(season_id),
                    "draft_order": draft_order,
                    "my_team": my_team,
                    "current_plan": {
                        "keepers": keepers,
                        "drafted_players": [],
                        "planned_picks": []
                    }
                }
                
                # Save config with timestamp
                config_filename = ConfigManager.save_config(new_config)
                st.session_state['current_config_file'] = config_filename
                
                # Load it into session state
                league_info = ConfigManager.extract_league_info(new_config)
                st.session_state['league_id'] = league_info['league_id']
                st.session_state['season_id'] = league_info['season_id']
                st.session_state['teams'] = league_info['draft_order']
                st.session_state['my_team'] = league_info['my_team']
                st.session_state['draft_order'] = league_info['draft_order']
                st.session_state['keepers'] = league_info['keepers']
                st.session_state['current_plan'] = new_config.get('current_plan', {})
                st.session_state['config_loaded'] = True
                
                # Set num_rounds for draft board (21 standard rounds)
                st.session_state['num_rounds'] = 21
                
                st.success(f"✅ Config created: {config_filename}")
                st.balloons()
                st.rerun()
            else:
                st.error("Please fill in League ID, Season ID, Draft Order, and Your Team")
    
    # === WORKFLOW 1.5: EDIT EXISTING CONFIG ===
    elif workflow == "✏️ Edit Existing Config":
        st.write("**Edit keepers and draft order in an existing configuration**")
        
        configs = ConfigManager.list_configs()
        
        if not configs:
            st.warning("No configuration files found. Create one using 'Start New League Config'.")
        else:
            selected_config = st.selectbox(
                "Select Configuration to Edit",
                configs,
                help="Choose a config to edit"
            )
            
            if st.button("Load Config for Editing"):
                try:
                    config = ConfigManager.load_config(selected_config)
                    st.session_state['editing_config_file'] = selected_config
                    st.session_state['editing_config'] = config
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to load config: {e}")
            
            # If config is loaded for editing, show edit form
            if st.session_state.get('editing_config_file') == selected_config:
                config = st.session_state.get('editing_config', {})
                league_info = ConfigManager.extract_league_info(config)
                
                st.markdown("---")
                st.write("**Current Configuration:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("League ID", league_info['league_id'])
                with col2:
                    st.metric("Your Team", league_info['my_team'])
                
                st.write(f"**Draft Order:** {', '.join(league_info['draft_order'])}")
                
                # Load league from ESPN if not already loaded for this config
                if st.session_state.get('editing_league_id') != league_info['league_id']:
                    with st.spinner("Loading player data..."):
                        try:
                            # Try to get player data from session state first
                            player_data = st.session_state.get('player_data_all')
                            
                            # If not in session, load from draft_results CSV (full player universe: 2600+ players)
                            if player_data is None or player_data.empty:
                                # Look for draft_results CSV files - these are the full player universe
                                csv_files = glob.glob(f"draft_results_{league_info['league_id']}_*.csv")
                                if csv_files:
                                    # Load the most recent one
                                    latest_csv = max(csv_files, key=os.path.getmtime)
                                    player_data = pd.read_csv(latest_csv)
                                    st.info(f"📁 Loaded full player universe from: {os.path.basename(latest_csv)} ({len(player_data)} players)")
                            
                            if player_data is not None and not player_data.empty:
                                # Extract positions from player data (exclude UNK - will use position_x fallback)
                                positions = sorted(player_data['position'].unique().tolist())
                                positions = [p for p in positions if p not in ["", "UNK", None]]
                                
                                st.session_state['available_positions'] = positions
                                
                                # Build player_position_map with position_x fallback and normalization
                                player_position_map = {}
                                for _, row in player_data.iterrows():
                                    player_name = row.get('name_x')
                                    player_pos = row.get('position')
                                    position_fallback = row.get('position_x')
                                    
                                    # Use position, or fall back to position_x if position is UNK
                                    if player_name:
                                        if player_pos and player_pos not in ["", "UNK", None]:
                                            # Normal position - use as-is (already normalized)
                                            if player_name not in player_position_map:
                                                player_position_map[player_name] = set()
                                            player_position_map[player_name].add(str(player_pos))
                                        elif player_pos == "UNK" and position_fallback and position_fallback not in ["", None]:
                                            # UNK player - use position_x fallback with normalization
                                            if player_name not in player_position_map:
                                                player_position_map[player_name] = set()
                                            normalized_pos = normalize_position(position_fallback)
                                            player_position_map[player_name].add(normalized_pos)
                                
                                st.session_state['player_position_map'] = player_position_map
                                st.session_state['available_player_names'] = sorted(list(player_position_map.keys()))
                                st.session_state['editing_league_id'] = league_info['league_id']
                                st.success(f"✅ Loaded {len(positions)} positions and {len(player_position_map)} players")
                            else:
                                st.error("❌ No player data available. Make sure draft_results_{league_id}_*.csv exists or load Live Draft first.")
                                return
                        
                        except Exception as e:
                            st.error(f"❌ Error loading player data: {e}")
                
                # Edit keepers
                st.write("### Update Keepers")
                
                # Get positions and players from ESPN (already loaded above)
                available_positions = st.session_state.get('available_positions', [])
                player_position_map = st.session_state.get('player_position_map', {})
                all_player_names = st.session_state.get('available_player_names', [])
                
                if not available_positions:
                    st.error("❌ League positions not loaded. Please refresh the page.")
                    return
                
                if not all_player_names:
                    st.warning("⚠️ No players found in league. Make sure you loaded the config correctly.")
                
                updated_keepers = {}
                draft_order = league_info['draft_order']
                
                for team_idx, team in enumerate(draft_order):
                    with st.expander(f"**{team}** - Update Keepers"):
                        current_keepers = league_info['keepers'].get(team, [])
                        
                        st.caption(f"Current keepers: {len(current_keepers)}")
                        
                        num_keepers = st.number_input(
                            f"Number of keepers for {team}",
                            min_value=0,
                            max_value=3,
                            value=len(current_keepers),
                            step=1,
                            key=f"edit_num_keepers_{team}"
                        )
                        
                        # Show warning if reducing keeper count
                        if num_keepers < len(current_keepers):
                            st.warning(f"⚠️ Reducing from {len(current_keepers)} to {num_keepers} keepers. Keepers beyond slot {num_keepers} will be removed.")
                        
                        team_keepers = []
                        for k_idx in range(num_keepers):
                            col1, col2, col3 = st.columns(3)
                            
                            # Get current keeper data if exists
                            current_keeper = current_keepers[k_idx] if k_idx < len(current_keepers) else None
                            
                            # Get current position from keeper or default to first position
                            current_position = current_keeper['position'] if current_keeper and 'position' in current_keeper else available_positions[0]
                            if current_position not in available_positions:
                                current_position = available_positions[0]
                            
                            with col2:
                                # Get safe index for selectbox
                                default_pos_idx = available_positions.index(current_position)
                                
                                position = st.selectbox(
                                    "Position",
                                    available_positions,
                                    index=default_pos_idx,
                                    key=f"edit_keeper_pos_{team}_{k_idx}",
                                    help="Select position to filter players"
                                )
                            
                            # Filter players by position
                            position_players = []
                            if position and player_position_map:
                                for player_name, positions_set in player_position_map.items():
                                    if position in positions_set or not positions_set:
                                        position_players.append(player_name)
                                position_players = sorted(position_players)
                            
                            # If no players filtered by position, show all players as fallback
                            if not position_players:
                                position_players = sorted(all_player_names) if all_player_names else []
                            
                            with col1:
                                default_player_idx = 0
                                if current_keeper and current_keeper.get('player'):
                                    if current_keeper['player'] in position_players:
                                        default_player_idx = position_players.index(current_keeper['player'])
                                
                                # Show player name or placeholder if no options
                                if position_players:
                                    player_name = st.selectbox(
                                        "Player Name",
                                        position_players,
                                        index=default_player_idx,
                                        key=f"edit_keeper_player_{team}_{k_idx}",
                                    )
                                else:
                                    st.warning(f"No players available. Load config with 'Start New League Config' first.")
                                    player_name = ""
                            
                            with col3:
                                default_pick = current_keeper['pick'] if current_keeper else (k_idx * len(draft_order) + team_idx + 1)
                                pick_num = st.number_input(
                                    "Pick #",
                                    value=int(default_pick),
                                    min_value=1,
                                    max_value=300,
                                    step=1,
                                    key=f"edit_keeper_pick_{team}_{k_idx}",
                                )
                            
                            if player_name:
                                team_keepers.append({
                                    "player": player_name,
                                    "position": position,
                                    "pick": int(pick_num)
                                })
                        
                        updated_keepers[team] = team_keepers
                
                # Show summary before saving
                st.divider()
                st.write("### Update Summary")
                has_changes = False
                for team in draft_order:
                    current_keepers = league_info['keepers'].get(team, [])
                    new_keepers = updated_keepers.get(team, [])
                    
                    if current_keepers != new_keepers:
                        has_changes = True
                        with st.expander(f"**{team}**: {len(current_keepers)} → {len(new_keepers)} keepers"):
                            if new_keepers:
                                st.write("**New keepers:**")
                                for k in new_keepers:
                                    st.caption(f"  • {k['player']} ({k['position']}) - Pick #{k['pick']}")
                            else:
                                st.caption("No keepers")
                
                if not has_changes:
                    st.caption("💡 No changes detected. Modify keepers above to see summary.")
                
                # Save updated config
                if st.button("💾 Save Updated Config", use_container_width=True, disabled=not has_changes):
                    config['current_plan']['keepers'] = updated_keepers
                    ConfigManager.save_config(config, st.session_state['editing_config_file'])
                    st.session_state['editing_config_file'] = None
                    st.session_state['editing_config'] = None
                    st.success(f"✅ Config updated: {selected_config}")
                    st.balloons()
                    st.rerun()
    
    # === WORKFLOW 2: PRACTICE FROM EXISTING CONFIG ===
    elif workflow == "🎯 Practice from Existing Config":
        st.write("**Run a practice draft with an existing configuration**")
        
        configs = ConfigManager.list_configs()
        
        if not configs:
            st.warning("No configuration files found. Create one using 'Start New League Config'.")
        else:
            selected_config = st.selectbox(
                "Select Configuration",
                configs,
                help="Choose a config to practice with"
            )
            
            if st.button("Load Config for Practice Draft"):
                try:
                    config = ConfigManager.load_config(selected_config)
                    league_info = ConfigManager.extract_league_info(config)
                    st.session_state['league_id'] = league_info['league_id']
                    st.session_state['season_id'] = league_info['season_id']
                    st.session_state['teams'] = league_info['draft_order']
                    st.session_state['my_team'] = league_info['my_team']
                    st.session_state['draft_order'] = league_info['draft_order']
                    st.session_state['keepers'] = league_info['keepers']
                    st.session_state['current_plan'] = config.get('current_plan', {})
                    st.session_state['current_config_file'] = selected_config
                    st.session_state['config_loaded'] = True
                    
                    # Set num_rounds for draft board
                    st.session_state['num_rounds'] = 21
                    
                    # Convert keepers to actual picks in player_data_all
                    if st.session_state.get('player_data_all') is not None and league_info['keepers']:
                        player_data = st.session_state['player_data_all'].copy()
                        for team, keepers in league_info['keepers'].items():
                            for keeper in keepers:
                                # Find the player in player_data_all by name
                                # Handle position matching with normalization
                                keeper_name = keeper.get('player')
                                keeper_pos = normalize_position(keeper.get('position'))
                                
                                player_match = player_data[player_data['name_x'] == keeper_name]
                                
                                if not player_match.empty:
                                    # Find the first match where position matches either position or normalized position_x
                                    for idx in player_match.index:
                                        player_pos = player_data.loc[idx, 'position']
                                        position_fallback = player_data.loc[idx, 'position_x']
                                        normalized_fallback = normalize_position(position_fallback)
                                        
                                        # Check if keeper position matches either main position or normalized fallback
                                        if (keeper_pos == player_pos) or (keeper_pos == normalized_fallback):
                                            # Mark as picked by this team
                                            player_data.loc[idx, 'owner'] = team
                                            player_data.loc[idx, 'pick_number'] = keeper.get('pick', 0)
                                            break
                        st.session_state['player_data_all'] = player_data
                    
                    st.success(f"✅ Loaded: {selected_config}")
                    st.info("📝 **Next steps:** Go to 'Current Board' to start your practice draft")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to load config: {e}")
            
            # Show config details
            st.markdown("---")
            st.write("**Config Details:**")
            try:
                config = ConfigManager.load_config(selected_config)
                league_info = ConfigManager.extract_league_info(config)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("League ID", league_info['league_id'])
                with col2:
                    st.metric("Season ID", league_info['season_id'])
                with col3:
                    st.metric("Your Team", league_info['my_team'])
                
                st.write("**Draft Order:**", league_info['draft_order'])
                
                if league_info['keepers']:
                    st.write("**Keepers:**")
                    for team, team_keepers in league_info['keepers'].items():
                        if team_keepers:
                            keeper_str = ", ".join([f"{k['player']} ({k['position']})" for k in team_keepers])
                            st.write(f"- {team}: {keeper_str}")
            except Exception as e:
                st.error(f"Could not load config details: {e}")
    
    # === WORKFLOW 3: LIVE DRAFT ===
    else:  # Live Draft
        st.write("**Resume your live league draft**")
        
        configs = ConfigManager.list_configs()
        
        if not configs:
            st.warning("No configuration files found. Create one using 'Start New League Config'.")
        else:
            selected_config = st.selectbox(
                "Select Configuration",
                configs,
                help="Choose your live draft config"
            )
            
            if st.button("Load Live Draft"):
                try:
                    config = ConfigManager.load_config(selected_config)
                    league_info = ConfigManager.extract_league_info(config)
                    st.session_state['league_id'] = league_info['league_id']
                    st.session_state['season_id'] = league_info['season_id']
                    st.session_state['teams'] = league_info['draft_order']
                    st.session_state['my_team'] = league_info['my_team']
                    st.session_state['draft_order'] = league_info['draft_order']
                    st.session_state['keepers'] = league_info['keepers']
                    st.session_state['current_plan'] = config.get('current_plan', {})
                    st.session_state['current_config_file'] = selected_config
                    st.session_state['config_loaded'] = True
                    
                    # Set num_rounds for draft board
                    st.session_state['num_rounds'] = 21
                    
                    st.success(f"✅ Live Draft Loaded: {selected_config}")
                    st.info("🏆 **You're live!** Go to 'Current Board' to manage your draft")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to load config: {e}")
            
            # Show config details
            st.markdown("---")
            st.write("**Config Details:**")
            try:
                config = ConfigManager.load_config(selected_config)
                league_info = ConfigManager.extract_league_info(config)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("League ID", league_info['league_id'])
                with col2:
                    st.metric("Season ID", league_info['season_id'])
                with col3:
                    st.metric("Your Team", league_info['my_team'])
                
                st.write("**Draft Order:**", league_info['draft_order'])
            except Exception as e:
                st.error(f"Could not load config details: {e}")
            
            # Show available saved plans with scores
            st.markdown("---")
            with st.expander("📊 Saved Plans & Scores"):
                st.write("**Available Strategies & Plans**")
                st.write("Score your plans on: Total POS Value | Total Norm Value | Total PPG")
                
                try:
                    # Load player data for scoring
                    import glob
                    csv_files = glob.glob(f"draft_results_{league_info['league_id']}_*.csv")
                    if csv_files:
                        csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                        player_data = pd.read_csv(csv_files[0])
                        
                        # Load tier baselines for scoring
                        from app import calculate_tier_baselines
                        tier_baselines = calculate_tier_baselines(player_data)
                        
                        # Score all available plans
                        plans_data = []
                        for plan_config in configs:
                            try:
                                cfg = ConfigManager.load_config(plan_config)
                                plan = cfg.get('plan', [])
                                
                                if plan:
                                    score = ConfigManager.calculate_plan_score(plan, player_data, tier_baselines)
                                    plans_data.append({
                                        'Config': plan_config,
                                        'Total POS Value': score['total_pos_value'],
                                        'Total Norm Value': score['total_norm_value'],
                                        'Total PPG': score['total_ppg'],
                                        'Picks': len(plan)
                                    })
                            except:
                                pass
                        
                        if plans_data:
                            plans_df = pd.DataFrame(plans_data).sort_values('Total PPG', ascending=False)
                            st.dataframe(plans_df, use_container_width=True, hide_index=True)
                            
                            st.info("💡 **Tip:** Click on a config above to load it and seed your draft with this plan.")
                        else:
                            st.caption("No saved plans found. Build a strategy and plan to score it here.")
                    else:
                        st.warning("No draft_results CSV found. Cannot score plans without player data.")
                except Exception as e:
                    st.warning(f"Could not load plan scores: {e}")

