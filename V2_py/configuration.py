# configuration.py
import streamlit as st
import pandas as pd
import json
from config_manager import ConfigManager
from espn_api.football import League


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
                
                # Edit keepers
                st.write("### Update Keepers")
                available_positions = st.session_state.get('available_positions', ["QB", "RB", "WR", "TE", "DEF", "K"])
                player_position_map = st.session_state.get('player_position_map', {})
                all_player_names = st.session_state.get('available_player_names', [])
                
                updated_keepers = {}
                draft_order = league_info['draft_order']
                
                for team_idx, team in enumerate(draft_order):
                    with st.expander(f"**{team}** - Update Keepers"):
                        current_keepers = league_info['keepers'].get(team, [])
                        num_keepers = st.number_input(
                            f"Number of keepers for {team}",
                            min_value=0,
                            max_value=3,
                            value=len(current_keepers),
                            step=1,
                            key=f"edit_num_keepers_{team}"
                        )
                        
                        team_keepers = []
                        for k_idx in range(num_keepers):
                            col1, col2, col3 = st.columns(3)
                            
                            # Get current keeper data if exists
                            current_keeper = current_keepers[k_idx] if k_idx < len(current_keepers) else None
                            
                            with col2:
                                position = st.selectbox(
                                    "Position",
                                    available_positions,
                                    index=available_positions.index(current_keeper['position']) if current_keeper and current_keeper['position'] in available_positions else 0,
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
                            else:
                                position_players = all_player_names
                            
                            with col1:
                                default_player_idx = 0
                                if current_keeper and current_keeper['player'] in position_players:
                                    default_player_idx = position_players.index(current_keeper['player'])
                                
                                player_name = st.selectbox(
                                    "Player Name",
                                    position_players,
                                    index=default_player_idx,
                                    key=f"edit_keeper_player_{team}_{k_idx}",
                                )
                            
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
                
                # Save updated config
                if st.button("💾 Save Updated Config", use_container_width=True):
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
