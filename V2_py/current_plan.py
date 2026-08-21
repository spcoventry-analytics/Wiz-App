# current_plan.py
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from config_manager import ConfigManager
from configuration import normalize_position

def show_current_plan():
    st.title("Current Plan")
    
    player_data_all = st.session_state.get('player_data_all')
    draft_order = st.session_state.get('draft_order', [])
    position_colors = st.session_state.get('position_colors', {})
    slot_counts = st.session_state.get('slot_counts', {})
    tier_baselines = st.session_state.get('tier_baselines', {})
    your_team_default = st.session_state.get('my_team', draft_order[0] if draft_order else None)
    num_teams = len(draft_order) if draft_order else 1
    config_filename = st.session_state.get('config_filename')
    
    # Load strategy and plan from config on page load
    if config_filename and 'loaded_strategy' not in st.session_state:
        try:
            loaded_strategy = ConfigManager.load_strategy(config_filename)
            # Populate session_state with loaded strategy
            for pos, rounds in loaded_strategy.items():
                st.session_state[f'target_rounds_{pos}'] = rounds
            st.session_state['loaded_strategy'] = True
        except:
            st.session_state['loaded_strategy'] = False
    
    if config_filename and 'loaded_plan' not in st.session_state:
        try:
            loaded_plan = ConfigManager.load_plan(config_filename)
            st.session_state['draft_plan'] = loaded_plan
            
            # Initialize plan_picks dict if not present
            if 'plan_picks' not in st.session_state:
                st.session_state['plan_picks'] = {}
            
            # Convert loaded plan list to plan_picks dict by round
            for pick in loaded_plan:
                round_num = pick.get('round')
                if round_num:
                    st.session_state['plan_picks'][round_num] = pick
                    # Also populate position state for proper defaults
                    position = pick.get('position')
                    if position:
                        st.session_state[f'plan_pos_{round_num}'] = position
            
            st.session_state['loaded_plan'] = True
        except:
            st.session_state['loaded_plan'] = False
    
    if player_data_all is None or player_data_all.empty:
        st.warning("No player data available.")
        return
    
    # === CREATE TABS: BUILD STRATEGY → BUILD PLAN → HYPOTHETICAL ROSTER ===
    tab_strategy, tab_build, tab_roster = st.tabs(["🔍 Build a Strategy", "🎯 Build Plan", "📊 Hypothetical Roster"])
    
    # ============================================================================
    # === TAB 1: BUILD A STRATEGY (POINT RANGES BY ROUND) ===
    # ============================================================================
    with tab_strategy:
        st.write("**Strategy Builder: Point Ranges by Draft Round**")
        st.write("*See how points per player vary by draft round for each position. Select target rounds for your strategy.*")
        
        st.markdown("---")
        
        # Get available players
        available_players_strat = player_data_all[player_data_all["pick_number"] == 0].copy()
        
        # Get position filter - limited to positions with slots in the hypothetical roster
        available_positions_strat = [pos for pos in slot_counts.keys() if pos not in ["IR", "", "FLEX", "BENCH", "BE"] and "/" not in pos]
        position_filter = st.radio("Filter by Position:", ["All"] + available_positions_strat, horizontal=True)
        
        if position_filter != "All":
            available_players_strat = available_players_strat[available_players_strat['position'] == position_filter]
        
        if available_players_strat.empty:
            st.warning("No players available for strategy building.")
        else:
            # Separate offensive and defensive handling
            offensive_strat = available_players_strat[available_players_strat['position'].isin(['QB', 'RB', 'WR', 'TE'])].copy()
            defensive_strat = available_players_strat[available_players_strat['position'].isin(['LB', 'DL', 'DB'])].copy()
            
            # For offensive players: require ADP for round calculation
            offensive_strat = offensive_strat.dropna(subset=['adp']).copy()
            offensive_strat['draft_round'] = np.ceil(offensive_strat['adp'].fillna(999) / num_teams).astype(int)
            offensive_strat['draft_round'] = offensive_strat['draft_round'].clip(lower=1, upper=21)
            
            # For defensive players: use PPG (no ADP required)
            defensive_strat['PPG'] = defensive_strat['PPG'].fillna(0)
            defensive_strat['draft_round'] = 21  # Placeholder round for defense
            
            # Combine both
            available_players_strat = pd.concat([offensive_strat, defensive_strat], ignore_index=True)
            
            # Get positions to show
            positions_to_show = [position_filter] if position_filter != "All" else sorted(available_players_strat['position'].unique())
            
            for pos in positions_to_show:
                pos_players = available_players_strat[available_players_strat['position'] == pos].copy()
                
                # Only require ADP/PPG fields for offensive positions
                if pos in ['QB', 'RB', 'WR', 'TE']:
                    pos_players = pos_players.dropna(subset=['PPG', 'floor', 'ceiling', 'points', 'adp'])
                else:
                    # For defensive positions, just need PPG (fillna to 0 if missing)
                    pos_players['PPG'] = pos_players['PPG'].fillna(0)
                    pos_players = pos_players[pos_players['PPG'] >= 0]  # Just remove NaN
                
                if pos_players.empty:
                    continue
                
                # Sort by draft round
                pos_players = pos_players.sort_values('draft_round', ascending=True)
                
                color = position_colors.get(pos, '#1f77b4')
                
                # Create layout: graph on left, round selector on right
                col_graph, col_control = st.columns([4, 1])
                
                with col_graph:
                    fig = go.Figure()
                    
                    # For each round, show the range of available players
                    for round_num in sorted(pos_players['draft_round'].unique()):
                        round_players = pos_players[pos_players['draft_round'] == round_num]
                        
                        if round_players.empty:
                            continue
                        
                        # Get min/max points in this round
                        min_points = round_players['floor'].min()
                        max_points = round_players['ceiling'].max()
                        best_points = round_players['points'].max()
                        worst_points = round_players['points'].min()
                        
                        # Create scatter plot for this round with error bars
                        fig.add_trace(
                            go.Scatter(
                                x=[best_points],  # Position dot at best available
                                y=[f"Round {round_num}"],
                                mode='markers',
                                marker=dict(
                                    size=12,
                                    color=color,
                                    line=dict(color='white', width=1.5)
                                ),
                                error_x=dict(
                                    type='data',
                                    symmetric=False,
                                    array=[max_points - best_points],  # Ceiling above best
                                    arrayminus=[best_points - min_points],  # Floor below best
                                    color=color,
                                    thickness=2.5,
                                    width=6
                                ),
                                customdata=[[
                                    round_players['name_x'].iloc[0],
                                    len(round_players),
                                    worst_points,
                                    best_points,
                                    min_points,
                                    max_points
                                ]],
                                hovertemplate=(
                                    "<b>Round %{y}</b><br>"
                                    "Best Available: %{customdata[0][0]}<br>"
                                    "Players in round: %{customdata[0][1]}<br>"
                                    "Point Range: %{customdata[0][4]:.0f} - %{customdata[0][5]:.0f}<br>"
                                    "Expected: %{customdata[0][2]:.0f} - %{customdata[0][3]:.0f}<extra></extra>"
                                ),
                                showlegend=False,
                            )
                        )
                    
                    # Dynamic plot height: one line per round
                    num_rounds = len(pos_players['draft_round'].unique())
                    dynamic_height = max(300, num_rounds * 40 + 100)
                    
                    fig.update_layout(
                        title=dict(
                            text=f"<b>{pos}</b> — Point Range by Draft Round",
                            font=dict(size=16)
                        ),
                        xaxis_title="Projected Points (Floor to Ceiling)",
                        yaxis=dict(
                            type='category',
                            categoryorder='array',
                            categoryarray=[f"Round {i}" for i in range(1, 22)],
                            autorange='reversed',  # Invert so Round 1 is at top
                            tickfont=dict(size=11),
                        ),
                        height=dynamic_height,
                        template='plotly_white',
                        margin=dict(l=100, r=40, t=60, b=50),
                        hoverlabel=dict(bgcolor="white", font_size=12),
                    )
                    
                    st.plotly_chart(fig, use_container_width=True, key=f"strategy_chart_{pos}")
                
                with col_control:
                    st.write("")  # Spacing
                    st.write("**📌 Target Rounds:**")
                    available_rounds = sorted(pos_players['draft_round'].unique())
                    target_rounds = st.multiselect(
                        f"Select rounds for {pos}",
                        available_rounds,
                        default=st.session_state.get(f'target_rounds_{pos}', []),
                        key=f"target_rounds_{pos}",
                        label_visibility="collapsed"
                    )
                    
                    if target_rounds:
                        st.success(f"🎯 {pos} targets: Rounds {', '.join(map(str, sorted(target_rounds)))}")
                    else:
                        st.caption("Select rounds ↑")
            
            # Save strategy to config after all positions are selected
            if config_filename:
                st.divider()
                if st.button("💾 Save Strategy to Config", use_container_width=True):
                    strategy = {}
                    for pos in positions_to_show:
                        rounds = st.session_state.get(f'target_rounds_{pos}', [])
                        if rounds:
                            strategy[pos] = sorted(rounds)
                    
                    if strategy:
                        ConfigManager.save_strategy(config_filename, strategy)
                        st.success(f"✅ Strategy saved! {len(strategy)} positions configured.")
                    else:
                        st.warning("No positions selected yet. Select at least one round per position.")
    
    # ============================================================================
    # === TAB 2: BUILD PLAN ===
    # ============================================================================
    with tab_build:
        st.write("**Build Your Draft Plan**")
        st.write("*Expand each round to select a position and target player. Strategy targets will be highlighted.*")
        
        # Get available players (separate offensive and defensive handling)
        available_players = player_data_all[player_data_all["pick_number"] == 0].copy()
        
        # For offensive players, require ADP for round calculation
        offensive_players = available_players[available_players['position'].isin(['QB', 'RB', 'WR', 'TE'])].copy()
        offensive_players = offensive_players.dropna(subset=['adp', 'points'])
        offensive_players['draft_round'] = (np.ceil(offensive_players['adp'] / num_teams)).fillna(1).astype(int)
        offensive_players['draft_round'] = offensive_players['draft_round'].clip(lower=1, upper=21)
        
        # For defensive players, use PPG for ranking (no ADP required)
        defensive_players = available_players[available_players['position'].isin(['LB', 'DL', 'DB'])].copy()
        defensive_players['PPG'] = defensive_players['PPG'].fillna(0)  # Ensure PPG has values
        defensive_players['draft_round'] = 21  # Assign to last round as placeholder
        
        # Combine both
        available_players = pd.concat([offensive_players, defensive_players], ignore_index=True)
        
        # Get strategy targets
        strategy_targets = {}
        for pos in ['QB', 'RB', 'WR', 'TE', 'LB', 'DL', 'DB']:
            target_rounds = st.session_state.get(f'target_rounds_{pos}', [])
            if target_rounds:
                strategy_targets[pos] = sorted(target_rounds)
        
        # Initialize plan picks if not present
        if 'plan_picks' not in st.session_state:
            st.session_state['plan_picks'] = {}
        
        # All possible positions (not just available)
        all_positions = ['QB', 'RB', 'WR', 'TE', 'LB', 'DL', 'DB']
        
        # Get keeper rounds to skip for my team
        keepers_dict = st.session_state.get('keepers', {})
        my_team = st.session_state.get('my_team')
        keeper_rounds = set()
        
        if my_team and my_team in keepers_dict:
            my_team_keepers = keepers_dict[my_team]
            for keeper in my_team_keepers:
                # Calculate round from pick number: round = ceil(pick / num_teams)
                pick_num = keeper.get('pick', 0)
                if pick_num > 0:
                    keeper_round = int(np.ceil(pick_num / num_teams))
                    keeper_rounds.add(keeper_round)
        
        # Render expandable rows for each round
        for round_num in range(1, 22):
            # Skip keeper rounds for my team
            if round_num in keeper_rounds:
                continue
            
            pick_key = f'plan_round_{round_num}'
            assigned_pick = st.session_state.get('plan_picks', {}).get(round_num)
            assigned_pos = assigned_pick.get('position') if assigned_pick else None
            
            # Check if this round was targeted in strategy
            strategy_pos_for_round = None
            for pos, target_rounds in strategy_targets.items():
                if round_num in target_rounds:
                    strategy_pos_for_round = pos
                    break
            
            # Determine default position: assigned > strategy > QB
            if assigned_pos:
                current_pos = assigned_pos
            elif strategy_pos_for_round:
                current_pos = strategy_pos_for_round
            else:
                current_pos = st.session_state.get(f'plan_pos_{round_num}', 'QB')
            
            # Determine background color based on whether position assigned
            row_label = f"Round {round_num}"
            if assigned_pos:
                row_label += f" — {assigned_pos}"
                # Color the expander header
                with st.expander(f"🎯 {row_label}", expanded=False):
                    # Show strategy hint if different from assigned
                    if strategy_pos_for_round and strategy_pos_for_round != assigned_pos:
                        st.caption(f"💡 Strategy suggested: {strategy_pos_for_round}")
                    
                    # Position selection with radio buttons
                    st.write("**Select Position:**")
                    
                    selected_pos = st.radio(
                        f"Position for Round {round_num}",
                        all_positions,
                        index=all_positions.index(current_pos) if current_pos in all_positions else 0,
                        key=f"plan_pos_{round_num}",
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                    
                    # Filter players based on position type
                    if selected_pos in ['LB', 'DL', 'DB']:
                        # Defense: no round filtering (no ADP data), just top 15 by PPG
                        round_range_players = available_players[
                            (available_players['position'] == selected_pos) &
                            (available_players['pick_number'] == 0)  # Only undrafted
                        ].copy()
                        
                        # Sort by PPG descending and take top 15 (fill NaN PPG with 0 for sorting)
                        if not round_range_players.empty:
                            round_range_players = round_range_players.fillna({'PPG': 0}).sort_values('PPG', ascending=False).head(15)
                    else:
                        # Offense: filter by round (±1) - only undrafted players
                        round_range_players = available_players[
                            (available_players['position'] == selected_pos) &
                            (available_players['draft_round'] >= max(1, round_num - 1)) &
                            (available_players['draft_round'] <= min(21, round_num + 1)) &
                            (available_players['pick_number'] == 0)  # Only undrafted
                        ].copy()
                        
                        # If no players found, broaden range to ±3 rounds
                        if round_range_players.empty:
                            round_range_players = available_players[
                                (available_players['position'] == selected_pos) &
                                (available_players['draft_round'] >= max(1, round_num - 3)) &
                                (available_players['draft_round'] <= min(21, round_num + 3)) &
                                (available_players['pick_number'] == 0)  # Only undrafted
                            ].copy()
                    
                    # For offensive positions, show gold mine plot
                    if selected_pos in ['QB', 'RB', 'WR', 'TE']:
                        if not round_range_players.empty:
                            st.write("**Players Available in Rounds {}-{} by Value:**".format(
                                max(1, round_num - 1), min(21, round_num + 1)
                            ))
                            
                            # Create scatter plot (gold mine)
                            round_range_players_clean = round_range_players.dropna(subset=['PPG', 'floor', 'ceiling', 'points'])
                            
                            if not round_range_players_clean.empty:
                                round_range_players_clean = round_range_players_clean.sort_values('PPG', ascending=False).head(8)
                                round_range_players_clean = round_range_players_clean.sort_values('points', ascending=True)
                                
                                color = position_colors.get(selected_pos, '#1f77b4')
                                error_minus = round_range_players_clean['points'] - round_range_players_clean['floor']
                                error_plus = round_range_players_clean['ceiling'] - round_range_players_clean['points']
                                
                                fig = go.Figure()
                                
                                fig.add_trace(
                                    go.Scatter(
                                        x=round_range_players_clean['points'],
                                        y=round_range_players_clean['name_x'],
                                        mode='markers',
                                        marker=dict(
                                            size=12,
                                            color=color,
                                            line=dict(color='white', width=1.5)
                                        ),
                                        error_x=dict(
                                            type='data',
                                            symmetric=False,
                                            array=error_plus,
                                            arrayminus=error_minus,
                                            color=color,
                                            thickness=2.5,
                                            width=6,
                                        ),
                                        customdata=round_range_players_clean[['PPG', 'floor', 'ceiling', 'adp']],
                                        hovertemplate=(
                                            "<b>%{y}</b><br>"
                                            "Points: %{x:.1f}<br>"
                                            "Range: %{customdata[1]:.0f} - %{customdata[2]:.0f}<br>"
                                            "PPG: %{customdata[0]:.2f}<br>"
                                            "ADP: %{customdata[3]:.1f}"
                                            "<extra></extra>"
                                        ),
                                        showlegend=False,
                                    )
                                )
                                
                                fig.update_layout(
                                    title=f"<b>{selected_pos}</b> — Value by Points",
                                    xaxis_title="Projected Points",
                                    yaxis_title="Player",
                                    height=300,
                                    template='plotly_white',
                                    margin=dict(l=150, r=40, t=50, b=50),
                                )
                                
                                st.plotly_chart(fig, use_container_width=True, key=f"gold_mine_assigned_{round_num}")
                    
                    # Player selection dropdown (filtered by round and position)
                    st.write("**Select Target Player:**")
                    
                    if selected_pos in ['LB', 'DL', 'DB']:
                        # Defense: sorted by PPG descending (already sorted above)
                        player_list = round_range_players.sort_values('PPG', ascending=False)
                    else:
                        # Offense: sort by PPG (value)
                        player_list = round_range_players.sort_values('PPG', ascending=False)
                    
                    if not player_list.empty:
                        player_options = player_list['name_x'].tolist()
                        default_player = assigned_pick.get('target_player') if assigned_pick else None
                        default_idx = player_options.index(default_player) if default_player in player_options else 0
                        
                        selected_player = st.selectbox(
                            "Player",
                            player_options,
                            index=default_idx,
                            key=f"plan_player_{round_num}",
                            label_visibility="collapsed"
                        )
                        
                        # Save button
                        if st.button(f"💾 Save Round {round_num} Plan", key=f"save_plan_{round_num}", use_container_width=True):
                            st.session_state['plan_picks'][round_num] = {
                                'round': round_num,
                                'position': selected_pos,
                                'target_player': selected_player,
                                'status': 'ACTIVE'
                            }
                            
                            # Save to config
                            if config_filename:
                                plan_list = list(st.session_state['plan_picks'].values())
                                ConfigManager.save_plan(config_filename, plan_list)
                            
                            st.success(f"✅ Round {round_num}: {selected_pos} → {selected_player}")
                            st.rerun()
                    else:
                        st.warning(f"No {selected_pos} players available for this round range.")
            else:
                # Not yet assigned, show as collapsed
                label_hint = row_label
                if strategy_pos_for_round:
                    label_hint += f" → 🎯 {strategy_pos_for_round}"
                with st.expander(f"⭕ {label_hint}", expanded=False):
                    # Show strategy suggestion
                    if strategy_pos_for_round:
                        st.caption(f"📌 Strategy suggests: **{strategy_pos_for_round}** for this round")
                    
                    # Position selection with radio buttons
                    st.write("**Select Position:**")
                    
                    selected_pos = st.radio(
                        f"Position for Round {round_num}",
                        all_positions,
                        index=all_positions.index(current_pos) if current_pos in all_positions else 0,
                        key=f"plan_pos_{round_num}",
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                    
                    # Filter players based on position type
                    if selected_pos in ['LB', 'DL', 'DB']:
                        # Defense: no round filtering (no ADP data), just top 15 by PPG
                        round_range_players = available_players[
                            (available_players['position'] == selected_pos) &
                            (available_players['pick_number'] == 0)  # Only undrafted
                        ].copy()
                        
                        # Sort by PPG descending and take top 15 (fill NaN PPG with 0 for sorting)
                        if not round_range_players.empty:
                            round_range_players = round_range_players.fillna({'PPG': 0}).sort_values('PPG', ascending=False).head(15)
                    else:
                        # Offense: filter by round (±1) - only undrafted players
                        round_range_players = available_players[
                            (available_players['position'] == selected_pos) &
                            (available_players['draft_round'] >= max(1, round_num - 1)) &
                            (available_players['draft_round'] <= min(21, round_num + 1)) &
                            (available_players['pick_number'] == 0)  # Only undrafted
                        ].copy()
                        
                        # If no players found, broaden range to ±3 rounds
                        if round_range_players.empty:
                            round_range_players = available_players[
                                (available_players['position'] == selected_pos) &
                                (available_players['draft_round'] >= max(1, round_num - 3)) &
                                (available_players['draft_round'] <= min(21, round_num + 3)) &
                                (available_players['pick_number'] == 0)  # Only undrafted
                            ].copy()
                    
                    # For offensive positions, show gold mine plot
                    if selected_pos in ['QB', 'RB', 'WR', 'TE']:
                        if not round_range_players.empty:
                            st.write("**Players Available in Rounds {}-{} by Value:**".format(
                                max(1, round_num - 1), min(21, round_num + 1)
                            ))
                            
                            # Create scatter plot (gold mine)
                            round_range_players_clean = round_range_players.dropna(subset=['PPG', 'floor', 'ceiling', 'points'])
                            
                            if not round_range_players_clean.empty:
                                round_range_players_clean = round_range_players_clean.sort_values('PPG', ascending=False).head(8)
                                round_range_players_clean = round_range_players_clean.sort_values('points', ascending=True)
                                
                                color = position_colors.get(selected_pos, '#1f77b4')
                                error_minus = round_range_players_clean['points'] - round_range_players_clean['floor']
                                error_plus = round_range_players_clean['ceiling'] - round_range_players_clean['points']
                                
                                fig = go.Figure()
                                
                                fig.add_trace(
                                    go.Scatter(
                                        x=round_range_players_clean['points'],
                                        y=round_range_players_clean['name_x'],
                                        mode='markers',
                                        marker=dict(
                                            size=12,
                                            color=color,
                                            line=dict(color='white', width=1.5)
                                        ),
                                        error_x=dict(
                                            type='data',
                                            symmetric=False,
                                            array=error_plus,
                                            arrayminus=error_minus,
                                            color=color,
                                            thickness=2.5,
                                            width=6,
                                        ),
                                        customdata=round_range_players_clean[['PPG', 'floor', 'ceiling', 'adp']],
                                        hovertemplate=(
                                            "<b>%{y}</b><br>"
                                            "Points: %{x:.1f}<br>"
                                            "Range: %{customdata[1]:.0f} - %{customdata[2]:.0f}<br>"
                                            "PPG: %{customdata[0]:.2f}<br>"
                                            "ADP: %{customdata[3]:.1f}"
                                            "<extra></extra>"
                                        ),
                                        showlegend=False,
                                    )
                                )
                                
                                fig.update_layout(
                                    title=f"<b>{selected_pos}</b> — Value by Points",
                                    xaxis_title="Projected Points",
                                    yaxis_title="Player",
                                    height=300,
                                    template='plotly_white',
                                    margin=dict(l=150, r=40, t=50, b=50),
                                )
                                
                                st.plotly_chart(fig, use_container_width=True, key=f"gold_mine_unassigned_{round_num}")
                    
                    # Player selection dropdown (filtered by round and position)
                    st.write("**Select Target Player:**")
                    
                    if selected_pos in ['LB', 'DL', 'DB']:
                        # Defense: sorted by PPG descending (already sorted above)
                        player_list = round_range_players.sort_values('PPG', ascending=False)
                    else:
                        # Offense: sort by PPG (value)
                        player_list = round_range_players.sort_values('PPG', ascending=False)
                    
                    if not player_list.empty:
                        player_options = player_list['name_x'].tolist()
                        
                        selected_player = st.selectbox(
                            "Player",
                            player_options,
                            index=0,
                            key=f"plan_player_{round_num}",
                            label_visibility="collapsed"
                        )
                        
                        # Save button
                        if st.button(f"💾 Save Round {round_num} Plan", key=f"save_plan_{round_num}", use_container_width=True):
                            st.session_state['plan_picks'][round_num] = {
                                'round': round_num,
                                'position': selected_pos,
                                'target_player': selected_player,
                                'status': 'ACTIVE'
                            }
                            
                            # Save to config
                            if config_filename:
                                plan_list = list(st.session_state['plan_picks'].values())
                                ConfigManager.save_plan(config_filename, plan_list)
                            
                            st.success(f"✅ Round {round_num}: {selected_pos} → {selected_player}")
                            st.rerun()
                    else:
                        st.warning(f"No {selected_pos} players available for this round range.")
    
    
    # ============================================================================
    # === TAB 3: HYPOTHETICAL ROSTER ===
    # ============================================================================
    with tab_roster:
        st.write("**Hypothetical Roster - Your Draft Plan**")
        st.write("*Keepers → Actual Picks → Planned Picks, then Starting Lineup with Bench*")
        
        keepers_dict = st.session_state.get('keepers', {})
        my_team = st.session_state.get('my_team')
        plan_picks = st.session_state.get('plan_picks', {})
        slot_counts = st.session_state.get('slot_counts', {})
        
        if plan_picks and slot_counts:
            # Build starting roster structure based on slot_counts, preserving ESPN order
            # slot_counts comes from ESPN as OrderedDict with positions in order
            # Note: FLEX positions come as "RB/WR/TE" etc (the "/" indicates flex eligibility)
            starting_slots = []
            for pos, count in slot_counts.items():
                if pos not in ["IR", "", "BENCH", "BE"]:
                    starting_slots.extend([(pos, i+1) for i in range(count)])
            
            # Prepare player lookup - combine keepers, actual picks, and planned picks in order
            all_picks_by_round = {}
            
            # STEP 1: Add keepers (locked in, highest priority)
            # Keepers use same structure as configuration.py: 'player' and 'position' keys
            if my_team and my_team in keepers_dict:
                for keeper in keepers_dict[my_team]:
                    keeper_name = keeper.get('player')
                    keeper_pos = normalize_position(keeper.get('position'))
                    keeper_pick_num = keeper.get('pick', 0)
                    
                    # Calculate round from pick number (same as configuration.py logic)
                    if keeper_pick_num > 0:
                        keeper_round = int(np.ceil(keeper_pick_num / num_teams))
                        keeper_round_key = keeper_round * 100  # Prefix with 100 to sort keepers first
                    else:
                        continue  # Skip keepers without pick number
                    
                    # Match player by name_x, checking position with normalization fallback (like configuration.py)
                    player_match = player_data_all[player_data_all['name_x'] == keeper_name]
                    if not player_match.empty:
                        # If multiple matches, check position with normalization fallback
                        found = False
                        for idx in player_match.index:
                            player_pos = player_data_all.loc[idx, 'position']
                            position_fallback = player_data_all.loc[idx, 'position_x']
                            normalized_fallback = normalize_position(position_fallback)
                            
                            # Match if keeper position == player position OR normalized position_x
                            if (keeper_pos == player_pos) or (keeper_pos == normalized_fallback):
                                player = player_data_all.loc[idx]
                                ppg = player.get('PPG', 0) if not pd.isna(player.get('PPG', 0)) else 0
                                points = player.get('points', 0) if not pd.isna(player.get('points', 0)) else 0
                                
                                all_picks_by_round[keeper_round_key] = {
                                    'position': keeper_pos,
                                    'player_name': keeper_name,
                                    'ppg': ppg,
                                    'points': points,
                                    'round_num': keeper_round,
                                    'source': 'keeper'
                                }
                                found = True
                                break
            
            # STEP 2: Add actual picks already made (from draft_results CSV)
            # BUT: Skip if player is already a keeper (deduplication)
            my_actual_picks = player_data_all[
                (player_data_all['owner'] == my_team) & 
                (player_data_all['pick_number'] > 0)
            ].copy()
            
            # Get keeper player names to avoid duplicates
            keeper_names = set()
            if my_team and my_team in keepers_dict:
                for keeper in keepers_dict[my_team]:
                    keeper_names.add(keeper.get('player'))
            
            for _, actual_pick in my_actual_picks.iterrows():
                player_name = actual_pick.get('name_x')
                
                # Skip this actual pick if it's already counted as a keeper
                if player_name in keeper_names:
                    continue
                
                pick_num = actual_pick.get('pick_number', 0)
                pick_round = int(np.ceil(pick_num / num_teams))
                pick_round = pick_round * 100 + 50  # Sort between keepers and planned picks
                
                ppg = actual_pick.get('PPG', 0) if not pd.isna(actual_pick.get('PPG', 0)) else 0
                points = actual_pick.get('points', 0) if not pd.isna(actual_pick.get('points', 0)) else 0
                
                all_picks_by_round[pick_round] = {
                    'position': actual_pick.get('position'),
                    'player_name': player_name,
                    'ppg': ppg,
                    'points': points,
                    'round_num': int(pick_round / 100),  # Store actual round
                    'source': 'actual'
                }
            
            # STEP 3: Add planned/hypothetical picks
            for round_num in sorted(plan_picks.keys()):
                pick = plan_picks[round_num]
                position = pick.get('position')
                player_name = pick.get('target_player')
                status = pick.get('status', 'ACTIVE')
                
                if status == 'INVALIDATED':
                    continue
                
                # Match target player by name_x with position fallback for duplicates (like configuration.py)
                player_match = player_data_all[player_data_all['name_x'] == player_name]
                if not player_match.empty:
                    # If multiple matches, prefer position match
                    if len(player_match) > 1:
                        pos_matches = player_match[player_match['position'] == position]
                        if not pos_matches.empty:
                            player = pos_matches.iloc[0]
                        else:
                            player = player_match.iloc[0]
                    else:
                        player = player_match.iloc[0]
                    
                    ppg = player.get('PPG', 0) if not pd.isna(player.get('PPG', 0)) else 0
                    points = player.get('points', 0) if not pd.isna(player.get('points', 0)) else 0
                    
                    # Sort key: plan picks go after keepers and actual picks
                    plan_round_key = round_num * 100 + 99
                    all_picks_by_round[plan_round_key] = {
                        'position': position,
                        'player_name': player_name,
                        'ppg': ppg,
                        'points': points,
                        'round_num': round_num,
                        'source': 'planned'
                    }
            
            # Assign players to starting slots
            starters = []
            bench = []
            
            # Keep a working copy of available picks ordered by round (keepers/actual first, then planned)
            available_picks = dict(all_picks_by_round)
            used_player_names = set()  # Track which players have been assigned (prevent duplicates)
            flex_slot_num = 0  # Track FLEX slot number

            # Pass through starting slots in ESPN order
            for slot_pos, slot_num in starting_slots:
                if "/" in slot_pos:
                    # FLEX slot (e.g., "RB/WR/TE")
                    flex_slot_num += 1
                    slot_id = f"FLEX{flex_slot_num}"
                    eligible_positions = [p.strip() for p in slot_pos.split("/")]

                    # Find highest PPG eligible player from remaining available picks
                    # Prioritize keepers/actual, then planned
                    # Skip players already assigned to prevent duplicates
                    best_sort_key = None
                    best_pick_key = None
                    for sort_key, pick in available_picks.items():
                        player_name = pick['player_name']
                        if player_name in used_player_names:
                            continue  # Skip already-used players
                        player_positions = [p.strip() for p in pick['position'].split('/')]
                        if any(p in eligible_positions for p in player_positions):
                            if best_pick_key is None or pick['ppg'] > available_picks[best_sort_key]['ppg']:
                                best_sort_key = sort_key
                                best_pick_key = sort_key

                    if best_pick_key is not None:
                        pick = available_picks.pop(best_pick_key)
                        player_name = pick['player_name']
                        used_player_names.add(player_name)  # Mark as used
                        primary_position = pick['position'].split('/')[0].strip()
                        
                        # Get tier_baseline - ensure defensive positions are included
                        if primary_position in tier_baselines:
                            tier_baseline = tier_baselines[primary_position].get(0, 0)
                        else:
                            # For defensive positions or missing tier_baselines, calculate on the fly
                            pos_players = player_data_all[
                                (player_data_all['position'] == primary_position) &
                                (player_data_all['pick_number'] == 0)
                            ].sort_values('PPG', ascending=False)
                            # Get average of top tier (first num_teams players)
                            if len(pos_players) >= num_teams:
                                tier_baseline = pos_players.iloc[:num_teams]['PPG'].mean()
                            else:
                                tier_baseline = pos_players['PPG'].mean() if not pos_players.empty else 0
                        
                        # Ensure PPG is valid (especially for defensive players)
                        ppg_value = pick['ppg'] if pick['ppg'] > 0 else 0
                        
                        # Calculate edge = PPG - position average
                        edge = ppg_value - tier_baseline

                        starters.append({
                            'Slot ID': slot_id,
                            'SLOT': slot_pos,
                            'Player': pick['player_name'],
                            'FPTS': round(pick['points'], 1),
                            'PPG': round(ppg_value, 1),
                            'Edge': round(edge, 1),
                            'Tier Baseline': round(tier_baseline, 1),
                            'Round': pick['round_num'],
                            'Source': pick.get('source', 'planned')
                        })
                    else:
                        starters.append({
                            'Slot ID': slot_id,
                            'SLOT': slot_pos,
                            'Player': "—",
                            'FPTS': 0,
                            'PPG': 0,
                            'Edge': 0,
                            'Tier Baseline': 0,
                            'Round': None,
                            'Source': '—'
                        })
                else:
                    # Regular position slot (QB, RB, WR, TE, etc.)
                    slot_id = f"{slot_pos}{slot_num}"
                    matched_key = None

                    # Grab the earliest drafted available player for this position
                    # Iterate through sorted keys to prioritize keepers/actual
                    # Skip players already assigned to prevent duplicates
                    for sort_key in sorted(available_picks.keys()):
                        pick = available_picks[sort_key]
                        player_name = pick['player_name']
                        if player_name in used_player_names:
                            continue  # Skip already-used players
                        player_positions = [p.strip() for p in pick['position'].split('/')]
                        if slot_pos in player_positions:
                            matched_key = sort_key
                            break

                    if matched_key is not None:
                        pick = available_picks.pop(matched_key)
                        player_name = pick['player_name']
                        used_player_names.add(player_name)  # Mark as used
                        
                        # Get tier_baseline - ensure defensive positions are included
                        if slot_pos in tier_baselines and (slot_num - 1) in tier_baselines[slot_pos]:
                            tier_baseline = tier_baselines[slot_pos][slot_num - 1]
                        else:
                            # For defensive positions or missing tier_baselines, calculate on the fly
                            pos_players = player_data_all[
                                (player_data_all['position'] == slot_pos) &
                                (player_data_all['pick_number'] == 0)
                            ].sort_values('PPG', ascending=False)
                            # Get average of this tier (slot_num * num_teams players)
                            tier_start = (slot_num - 1) * num_teams
                            tier_end = slot_num * num_teams
                            tier_players = pos_players.iloc[tier_start:tier_end]
                            tier_baseline = tier_players['PPG'].mean() if not tier_players.empty else 0
                        
                        # Ensure PPG is valid (especially for defensive players)
                        ppg_value = pick['ppg'] if pick['ppg'] > 0 else 0
                        
                        # Calculate edge = PPG - position average
                        edge = ppg_value - tier_baseline

                        starters.append({
                            'Slot ID': slot_id,
                            'SLOT': slot_pos,
                            'Player': pick['player_name'],
                            'FPTS': round(pick['points'], 1),
                            'PPG': round(ppg_value, 1),
                            'Edge': round(edge, 1),
                            'Tier Baseline': round(tier_baseline, 1),
                            'Round': pick['round_num'],
                            'Source': pick.get('source', 'planned')
                        })
                    else:
                        starters.append({
                            'Slot ID': slot_id,
                            'SLOT': slot_pos,
                            'Player': "—",
                            'FPTS': 0,
                            'PPG': 0,
                            'Edge': 0,
                            'Tier Baseline': 0,
                            'Round': None,
                            'Source': '—'
                        })

            # Anything remaining in available_picks goes to bench
            for sort_key, pick in sorted(available_picks.items()):
                player_name = pick['player_name']
                if player_name in used_player_names:
                    continue  # Skip if somehow already used
                    
                primary_position = pick['position'].split('/')[0].strip()
                
                # Get tier_baseline - ensure defensive positions are included
                if primary_position in tier_baselines:
                    tier_baseline = tier_baselines[primary_position].get(0, 0)
                else:
                    # For defensive positions or missing tier_baselines, calculate on the fly
                    pos_players = player_data_all[
                        (player_data_all['position'] == primary_position) &
                        (player_data_all['pick_number'] == 0)
                    ].sort_values('PPG', ascending=False)
                    # Get average of top tier (first num_teams players)
                    if len(pos_players) >= num_teams:
                        tier_baseline = pos_players.iloc[:num_teams]['PPG'].mean()
                    else:
                        tier_baseline = pos_players['PPG'].mean() if not pos_players.empty else 0
                
                # Ensure PPG is valid (especially for defensive players)
                ppg_value = pick['ppg'] if pick['ppg'] > 0 else 0
                
                # Calculate edge = PPG - position average
                edge = ppg_value - tier_baseline
                
                bench.append({
                    'Slot ID': 'BENCH',
                    'Position': pick['position'],
                    'Player': pick['player_name'],
                    'FPTS': round(pick['points'], 1),
                    'PPG': round(ppg_value, 1),
                    'Edge': round(edge, 1),
                    'Round': pick['round_num'],
                    'Source': pick.get('source', 'planned')
                })

            # Display Starting Lineup
            if starters:
                st.write("### 🏈 Starting Lineup")
                # Hide scrollbar on starting lineup table
                st.markdown(
                    """
                    <style>
                    [data-testid="stDataFrame"] {max-height: none; overflow: visible;}
                    [data-testid="stDataFrame"] [role="presentation"] {max-height: none; overflow: visible;}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                starters_df = pd.DataFrame(starters)
                # Reorder columns: SLOT, Tier Baseline, Player, FPTS, PPG, Edge, Round, Source
                display_cols = [col for col in ['SLOT', 'Tier Baseline', 'Player', 'FPTS', 'PPG', 'Edge', 'Round', 'Source'] if col in starters_df.columns]
                starters_df = starters_df[display_cols]
                st.dataframe(
                    starters_df,
                    use_container_width=True,
                    hide_index=True,
                    height=(len(starters_df) + 1) * 35 + 3,
                    column_config={
                        'SLOT': st.column_config.TextColumn(width="small"),
                        'Tier Baseline': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'Player': st.column_config.TextColumn(width="large"),
                        'FPTS': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'PPG': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'Edge': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'Round': st.column_config.NumberColumn(format="%d", width="small"),
                        'Source': st.column_config.TextColumn(width="small"),
                    }
                )
                starters_ppg = starters_df[starters_df['PPG'] > 0]['PPG'].sum()
                starters_edge = starters_df['Edge'].sum()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total PPG", round(starters_ppg, 1))
                with col2:
                    st.metric("Total Edge", round(starters_edge, 1))
                with col3:
                    st.metric("Slots Filled", len([s for s in starters if s['Player'] != "—"]))
            
            # Display Bench
            if bench:
                st.write("### 🛋️ Bench")
                bench_df = pd.DataFrame(bench)
                # Reorder columns: Position, Player, FPTS, PPG, Edge, Round, Source
                display_cols = [col for col in ['Position', 'Player', 'FPTS', 'PPG', 'Edge', 'Round', 'Source'] if col in bench_df.columns]
                bench_df = bench_df[display_cols]
                st.dataframe(
                    bench_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Position': st.column_config.TextColumn(width="small"),
                        'Player': st.column_config.TextColumn(width="large"),
                        'FPTS': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'PPG': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'Edge': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'Round': st.column_config.NumberColumn(format="%d", width="small"),
                        'Source': st.column_config.TextColumn(width="small"),
                    }
                )
                bench_ppg = bench_df['PPG'].sum()
                bench_edge = bench_df['Edge'].sum()
                st.caption(f"Bench PPG: {round(bench_ppg, 1)} | Bench Edge: {round(bench_edge, 1)}")
        else:
            if not plan_picks:
                st.info("No plan picks yet. Go to 'Build Plan' tab to start planning your draft.")
            if not slot_counts:
                st.warning("League slot information not loaded. Check that ESPN league was fetched correctly.")
