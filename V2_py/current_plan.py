# current_plan.py
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from config_manager import ConfigManager

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
        
        # Get available players
        available_players_strat = player_data_all[player_data_all["pick_number"] == 0].copy()
        
        # Get position filter
        available_positions_strat = sorted(available_players_strat['position'].unique())
        position_filter = st.selectbox("Filter by Position (optional):", ["All"] + available_positions_strat)
        
        if position_filter != "All":
            available_players_strat = available_players_strat[available_players_strat['position'] == position_filter]
        
        if available_players_strat.empty:
            st.warning("No players available for strategy building.")
        else:
            # Calculate draft round for each player
            available_players_strat = available_players_strat.dropna(subset=['adp']).copy()
            available_players_strat['draft_round'] = np.ceil(available_players_strat['adp'].fillna(999) / num_teams).astype(int)
            available_players_strat['draft_round'] = available_players_strat['draft_round'].clip(lower=1, upper=21)
            
            # Get positions to show
            positions_to_show = [position_filter] if position_filter != "All" else sorted(available_players_strat['position'].unique())
            
            for pos in positions_to_show:
                pos_players = available_players_strat[available_players_strat['position'] == pos].copy()
                pos_players = pos_players.dropna(subset=['PPG', 'floor', 'ceiling', 'points', 'adp'])
                
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
        
        # Get available players
        available_players = player_data_all[player_data_all["pick_number"] == 0].copy()
        available_players = available_players.dropna(subset=['adp', 'points'])
        available_players['draft_round'] = (np.ceil(available_players['adp'] / num_teams)).fillna(1).astype(int)
        available_players['draft_round'] = available_players['draft_round'].clip(lower=1, upper=21)
        
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
        st.write("*Starting Lineup with Marginal Value, then Bench Players*")
        
        plan_picks = st.session_state.get('plan_picks', {})
        slot_counts = st.session_state.get('slot_counts', {})
        
        if plan_picks and slot_counts:
            # Build starting roster structure based on slot_counts, preserving ESPN order
            # slot_counts comes from ESPN as OrderedDict with positions in order
            starting_slots = []
            for pos, count in slot_counts.items():
                if pos not in ["IR", "", "BENCH", "BE"] and "/" not in pos:
                    starting_slots.extend([(pos, i+1) for i in range(count)])
            
            # Prepare player lookup - all picks sorted by round
            all_picks_by_round = {}
            
            for round_num in sorted(plan_picks.keys()):
                pick = plan_picks[round_num]
                position = pick.get('position')
                player_name = pick.get('target_player')
                status = pick.get('status', 'ACTIVE')
                
                if status == 'INVALIDATED':
                    continue
                
                player_match = player_data_all[player_data_all['name_x'] == player_name]
                if not player_match.empty:
                    player = player_match.iloc[0]
                    ppg = player.get('PPG', 0) if not pd.isna(player.get('PPG', 0)) else 0
                    points = player.get('points', 0) if not pd.isna(player.get('points', 0)) else 0
                    
                    all_picks_by_round[round_num] = {
                        'position': position,
                        'player_name': player_name,
                        'ppg': ppg,
                        'points': points,
                        'round_num': round_num
                    }
            
            # Assign players to starting slots
            starters = []
            bench = []
            assigned_picks = set()
            
            # Phase 1: Assign position-specific players to their slots (QB1, RB1, RB2, etc.)
            for slot_pos, slot_num in starting_slots:
                if slot_pos == "FLEX":
                    continue  # Handle FLEX separately
                
                slot_filled = False
                target_pos_rank = slot_num  # We want the Nth player at this position
                current_pos_rank = 0
                
                for round_num in sorted(all_picks_by_round.keys()):
                    pick = all_picks_by_round[round_num]
                    if pick['position'] == slot_pos and round_num not in assigned_picks:
                        current_pos_rank += 1
                        if current_pos_rank == target_pos_rank:
                            # Found the Nth player for this position
                            tier_baseline = tier_baselines.get(slot_pos, {}).get(slot_num - 1, 0)
                            marg_val = pick['ppg'] - tier_baseline
                            starters.append({
                                'SLOT': slot_pos,
                                'S#': f"{slot_pos}{slot_num}",
                                'Player': pick['player_name'],
                                'FPTS': round(pick['points'], 1),
                                'AVG': round(pick['ppg'], 1),
                                'Marg Val': round(marg_val, 1),
                                'POS AVG': round(tier_baseline, 1),
                                'Round': round_num
                            })
                            assigned_picks.add(round_num)
                            slot_filled = True
                            break
                
                if not slot_filled:
                    # Slot not filled - show as empty
                    starters.append({
                        'SLOT': slot_pos,
                        'S#': f"{slot_pos}{slot_num}",
                        'Player': "—",
                        'FPTS': 0,
                        'AVG': 0,
                        'Marg Val': 0,
                        'POS AVG': 0,
                        'Round': None
                    })
            
            # Phase 2: Assign remaining players to FLEX slots (best available)
            remaining_picks = {k: v for k, v in all_picks_by_round.items() if k not in assigned_picks}
            
            for slot_pos, slot_num in starting_slots:
                if slot_pos == "FLEX":
                    # Find the highest PPG player from remaining
                    if remaining_picks:
                        best_round = max(remaining_picks.keys(), key=lambda r: remaining_picks[r]['ppg'])
                        pick = remaining_picks.pop(best_round)
                        
                        # FLEX tier baseline is the position's bench baseline (tier 0)
                        tier_baseline = tier_baselines.get(pick['position'], {}).get(0, 0)
                        marg_val = pick['ppg'] - tier_baseline
                        
                        starters.append({
                            'SLOT': 'FLEX',
                            'S#': f"FLEX{slot_num}",
                            'Player': pick['player_name'],
                            'FPTS': round(pick['points'], 1),
                            'AVG': round(pick['ppg'], 1),
                            'Marg Val': round(marg_val, 1),
                            'POS AVG': round(tier_baseline, 1),
                            'Round': best_round
                        })
                    else:
                        # No remaining players for this FLEX slot
                        starters.append({
                            'SLOT': 'FLEX',
                            'S#': f"FLEX{slot_num}",
                            'Player': "—",
                            'FPTS': 0,
                            'AVG': 0,
                            'Marg Val': 0,
                            'POS AVG': 0,
                            'Round': None
                        })
            
            # Phase 3: Everything left goes to bench
            for round_num in sorted(remaining_picks.keys()):
                pick = remaining_picks[round_num]
                tier_baseline = tier_baselines.get(pick['position'], {}).get(0, 0)
                marg_val = pick['ppg'] - tier_baseline
                bench.append({
                    'Position': pick['position'],
                    'Player': pick['player_name'],
                    'FPTS': round(pick['points'], 1),
                    'AVG': round(pick['ppg'], 1),
                    'Marg Val': round(marg_val, 1),
                    'Round': round_num
                })
            
            # Display Starting Lineup
            if starters:
                st.write("### 🏈 Starting Lineup")
                starters_df = pd.DataFrame(starters)
                st.dataframe(
                    starters_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'SLOT': st.column_config.TextColumn(width="small"),
                        'S#': st.column_config.TextColumn(width="small"),
                        'Player': st.column_config.TextColumn(width="large"),
                        'FPTS': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'AVG': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'Marg Val': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'POS AVG': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'Round': st.column_config.NumberColumn(format="%d", width="small"),
                    }
                )
                starters_ppg = starters_df[starters_df['AVG'] > 0]['AVG'].sum()
                starters_marg = starters_df[starters_df['Marg Val'] > 0]['Marg Val'].sum()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Lineup PPG", round(starters_ppg, 1))
                with col2:
                    st.metric("Lineup Marg Val", round(starters_marg, 1))
                with col3:
                    st.metric("Slots Filled", len([s for s in starters if s['Player'] != "—"]))
            
            # Display Bench
            if bench:
                st.write("### 🛋️ Bench")
                bench_df = pd.DataFrame(bench)
                st.dataframe(
                    bench_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Position': st.column_config.TextColumn(width="small"),
                        'Player': st.column_config.TextColumn(width="large"),
                        'FPTS': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'AVG': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'Marg Val': st.column_config.NumberColumn(format="%.1f", width="small"),
                        'Round': st.column_config.NumberColumn(format="%d", width="small"),
                    }
                )
                bench_ppg = bench_df['AVG'].sum()
                st.caption(f"Bench PPG: {round(bench_ppg, 1)}")
        else:
            if not plan_picks:
                st.info("No plan picks yet. Go to 'Build Plan' tab to start planning your draft.")
            if not slot_counts:
                st.warning("League slot information not loaded. Check that ESPN league was fetched correctly.")
