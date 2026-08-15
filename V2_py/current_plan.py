# current_plan.py
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

def show_current_plan():
    st.title("Current Plan")
    
    player_data_all = st.session_state.get('player_data_all')
    draft_order = st.session_state.get('draft_order', [])
    position_colors = st.session_state.get('position_colors', {})
    slot_counts = st.session_state.get('slot_counts', {})
    tier_baselines = st.session_state.get('tier_baselines', {})
    your_team_default = st.session_state.get('my_team', draft_order[0] if draft_order else None)
    num_teams = len(draft_order) if draft_order else 1
    
    if player_data_all is None or player_data_all.empty:
        st.warning("No player data available.")
        return
    
    # === CREATE TABS: BUILD PLAN vs SCARCITY vs STRATEGY ===
    tab_scarcity, tab_build, tab_strategy = st.tabs(["📊 Position Scarcity", "🎯 Build Plan (Round Strategy)", "🔍 Build a Strategy"])
    
    # ============================================================================
    # === TAB 1: POSITION SCARCITY (RESTORED FROM OLD VERSION) ===
    # ============================================================================
    with tab_scarcity:
        st.write("**Build Your Draft Plan - Select Position for Each Round**")
        st.write("*For each round, select which position to draft. See the expected player and points.*")
        
        # Initialize hypothetical picks in session state if not present
        if 'hypothetical_picks' not in st.session_state:
            st.session_state['hypothetical_picks'] = {}
        
        # Get available players (not yet drafted)
        available_players = player_data_all[player_data_all["pick_number"] == 0].copy()
        
        # Add positions to available data for this tab
        available_players_strategy = available_players.copy()
        # Drop players without ADP (they can't be assigned to a draft round)
        available_players_strategy = available_players_strategy.dropna(subset=['adp', 'points'])
        
        if available_players_strategy.empty:
            st.warning("No players with ADP data available for round strategy.")
            # Show scarcity tab instead
            st.info("Go to 'Position Scarcity' tab to see position urgency analysis.")
        
        available_players_strategy['draft_round'] = (np.ceil(available_players_strategy['adp'] / num_teams)).fillna(1).astype(int)
        available_players_strategy['draft_round'] = available_players_strategy['draft_round'].clip(lower=1, upper=21)
        
        # Get available positions
        available_positions_list = sorted(available_players_strategy['position'].unique())
        
        # Create a 3-column layout for round selection (for mobile/tablet)
        st.write("**Select Position for Each Round:**")
        
        # Use columns to organize selectors in a grid
        cols = st.columns(3)
        for round_num in range(1, 22):
            col_idx = (round_num - 1) % 3
            
            with cols[col_idx]:
                selected_pos = st.selectbox(
                    f"Round {round_num}",
                    ["—"] + available_positions_list,
                    key=f"round_{round_num}_pos",
                    index=0
                )
                
                # If a position is selected for this round, find the best player
                if selected_pos != "—":
                    # Find players at this position in this draft round
                    round_players = available_players_strategy[
                        (available_players_strategy['position'] == selected_pos) &
                        (available_players_strategy['draft_round'] == round_num)
                    ].sort_values('POS_Value_Normalized', ascending=False) if 'POS_Value_Normalized' in available_players_strategy.columns else available_players_strategy[
                        (available_players_strategy['position'] == selected_pos) &
                        (available_players_strategy['draft_round'] == round_num)
                    ]
                    
                    if not round_players.empty:
                        best_player = round_players.iloc[0]
                        st.session_state['hypothetical_picks'][round_num] = {
                            'position': selected_pos,
                            'player_name': best_player['name_x'],
                            'player_id': best_player.get('espn_id', ''),
                            'points': best_player.get('points', 0),
                            'ppg': best_player.get('PPG', 0),
                            'norm_value': best_player.get('POS_Value_Normalized', 0)
                        }
                        
                        # Display the selected player
                        st.write(f"📍 **{best_player['name_x']}**")
                        st.caption(f"{best_player.get('points', 0):.0f} pts | {best_player.get('POS_Value_Normalized', 0):.2f} norm val")
                    else:
                        st.caption("No players available in this round")
                else:
                    # Remove from hypothetical if deselected
                    if round_num in st.session_state['hypothetical_picks']:
                        del st.session_state['hypothetical_picks'][round_num]
        
        # Show hypothetical roster summary
        if st.session_state['hypothetical_picks']:
            st.divider()
            st.write("**Draft Plan Summary:**")
            
            hyp_picks = st.session_state['hypothetical_picks']
            total_points = sum(p['points'] for p in hyp_picks.values())
            avg_norm_val = np.mean([p['norm_value'] for p in hyp_picks.values()]) if hyp_picks else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Points", f"{total_points:.0f}")
            with col2:
                st.metric("Avg Norm Value", f"{avg_norm_val:.2f}")
            with col3:
                st.metric("Picks Selected", len(hyp_picks))
            
            # Show roster table
            roster_rows = []
            for round_num in sorted(hyp_picks.keys()):
                pick = hyp_picks[round_num]
                roster_rows.append({
                    'Round': round_num,
                    'Position': pick['position'],
                    'Player': pick['player_name'],
                    'Points': round(pick['points'], 1),
                    'PPG': round(pick['ppg'], 2),
                    'Norm Value': round(pick['norm_value'], 2)
                })
            
            roster_df = pd.DataFrame(roster_rows)
            st.dataframe(roster_df, use_container_width=True, hide_index=True)
            
            if st.button("🗑️ Clear All Selections"):
                st.session_state['hypothetical_picks'] = {}
                st.rerun()
    
    # ============================================================================
    # === TAB 2: BUILD PLAN (ROUND STRATEGY) ===
    # ============================================================================
    with tab_build:
        st.write("**Position Scarcity Analysis** — Your Team's Draft Urgency")
        
        # Debug: show slot_counts for troubleshooting
        with st.expander("🔧 Debug: League Configuration"):
            st.write(f"**slot_counts:** {slot_counts}")
            st.write(f"**num_teams:** {num_teams}")
            st.write(f"**tier_baselines keys:** {list(tier_baselines.keys())}")
        
        # Always analyze YOUR TEAM
        team_to_analyze = st.session_state.get('my_team', your_team_default)
        st.caption(f"📍 Analyzing: **{team_to_analyze}**")
        
        # Get picks made by your team
        team_picks = player_data_all[(player_data_all['pick_number'] > 0) & (player_data_all['owner'] == team_to_analyze)]
        
        # Count filled slots by position (BASE positions only, not including FLEX)
        filled_by_position = {}
        for pos in slot_counts.keys():
            if pos not in ["IR", "", "FLEX", "BENCH", "BE"]:
                filled_by_position[pos] = len(team_picks[team_picks['position'] == pos])
        
        # Available players (not yet drafted)
        available_players_scarcity = player_data_all[player_data_all["pick_number"] == 0]
        
        if available_players_scarcity.empty:
            st.warning("No available players remaining!")
        else:
            # Explanatory notes in expander (not intrusive on mobile)
            with st.expander("ℹ️ How to read this table"):
                st.write("""
                - **Tier** = which slot you're filling (RB1=1st RB slot, RB2=2nd RB slot, etc.)
                - **Baseline** = average PPG of that tier from the full player pool at draft start
                - **Value** = Player's PPG minus baseline (anything >0 is above average, >1 is significantly above)
                - **Starters Left** = available players ABOVE this tier's baseline (true starter quality)
                - **Drafted (ADP≤Best)** = competitors' picks at this position with ADP ≤ best available (scarcity indicator)
                - 🔴 **CRITICAL**: Not enough starters for remaining slots or very scarce
                - 🟠 **HIGH**: Multiple empty slots or high scarcity
                - 🟡 **MEDIUM**: One empty slot + moderate scarcity
                - 🟢 **LOW**: Slots filled or abundant starters
                """)
            
            st.write("")
            
            # Calculate position urgency for BASE positions only (not including FLEX capacity)
            position_analysis = []
            
            # Process BASE positions (RB, WR, TE, QB, etc.) WITHOUT FLEX capacity
            # Only show positions that are actually active in this league (slot_counts > 0)
            for pos in slot_counts.keys():
                # Filter out non-active positions: bench, flex, IR, empty, composite positions
                if pos in ["IR", "", "FLEX", "BENCH", "BE"] or "/" in pos:
                    continue
                
                total_slots = slot_counts.get(pos, 0)
                if total_slots == 0:
                    # Skip positions not in this league
                    continue
                filled_slots = filled_by_position.get(pos, 0)
                empty_slots = total_slots - filled_slots
                
                # Determine which tier we're currently drafting from (based on filled slots)
                current_tier = filled_slots
                
                # Get available players at this position
                pos_players = available_players_scarcity[available_players_scarcity['position'] == pos].sort_values('PPG', ascending=False)
                
                # Get tier baseline for current tier
                tier_baseline = 0
                if pos in tier_baselines and current_tier in tier_baselines[pos]:
                    tier_baseline = tier_baselines[pos][current_tier]
                
                # Count available players ABOVE this tier's baseline
                available_above_tier = len(pos_players[pos_players['PPG'] >= tier_baseline]) if tier_baseline > 0 else len(pos_players)
                
                # Best available at this position
                best_available = pos_players.iloc[0] if len(pos_players) > 0 else None
                best_available_value = 0
                if best_available is not None:
                    best_available_value = best_available['PPG'] - tier_baseline
                
                # Calculate ELASTICITY: value cost if we wait one round
                # (how much PPG do we lose by skipping this position now?)
                next_round_available = pos_players.iloc[num_teams] if len(pos_players) > num_teams else None
                elasticity = 0
                if best_available is not None and next_round_available is not None:
                    elasticity = round(best_available['PPG'] - next_round_available['PPG'], 1)
                elif best_available is not None and len(pos_players) > 0:
                    # If not enough players for full round, use average drop to next available
                    elasticity = round(best_available['PPG'] - pos_players.iloc[min(1, len(pos_players)-1)]['PPG'], 1)
                
                # ADP-aware scarcity: only count drafted players with ADP <= best_available's ADP
                adp_aware_drafted = 0
                if best_available is not None and pd.notna(best_available.get('adp')):
                    best_available_adp = best_available['adp']
                    adp_aware_drafted = len(player_data_all[
                        (player_data_all['position'] == pos) & 
                        (player_data_all['pick_number'] > 0) &
                        (player_data_all['adp'] <= best_available_adp)
                    ])
                    scarcity_ratio = adp_aware_drafted / num_teams if num_teams > 0 else 0
                else:
                    scarcity_ratio = 0
                
                # Urgency: PRIMARY = Elasticity (value cliff), SECONDARY = empty slots needed
                # High elasticity means steep drop-off if you wait → CRITICAL
                # Low elasticity means gentle drop-off → can afford to wait
                
                if elasticity > 5.0 and empty_slots > 0:
                    # High cliff + need to fill slots = CRITICAL
                    urgency_score = 2.5
                elif elasticity > 3.0 and empty_slots > 0:
                    # Steep cliff + need to fill = HIGH
                    urgency_score = 1.5
                elif elasticity > 1.5 and empty_slots > 0:
                    # Moderate cliff + need to fill = MEDIUM
                    urgency_score = 1.0
                elif elasticity > 0.5 and empty_slots > 0:
                    # Gentle cliff + need to fill = LOW but watch
                    urgency_score = 0.5
                else:
                    # Very flat cliff or no needs = RELAXED
                    urgency_score = 0.2
                
                # Also factor in scarcity: if running out of starters, boost urgency
                if available_above_tier <= empty_slots:
                    urgency_score += 0.8  # Running out of starters - boost priority
                
                # Always show position (not filtered by urgency), prioritized in sorted table
                position_analysis.append({
                    'Position': pos,
                    'Slots': f"{filled_slots}/{total_slots}",
                    'Empty': empty_slots,
                    'Tier': current_tier + 1,  # Display 1-indexed
                    'Baseline': round(tier_baseline, 1),
                    'Best Available': best_available['name_x'] if best_available is not None else 'NONE',
                    'PPG': round(best_available['PPG'], 1) if best_available is not None else 0,
                    'Value': round(best_available_value, 1),
                    'Elasticity': elasticity,  # PPG cost if you wait 1 round
                    'ADP': round(best_available['adp'], 0) if best_available is not None and pd.notna(best_available.get('adp')) else 'N/A',
                    'Starters Left': available_above_tier,
                    'Drafted (ADP≤Best)': adp_aware_drafted,
                    'Scarcity %': f"{int(scarcity_ratio * 100)}%",
                    'Urgency': urgency_score,
                })
            
            # Debug: check if position_analysis has data
            if not position_analysis:
                st.warning(f"⚠️ No position data found. slot_counts keys: {list(slot_counts.keys())}")
            else:
                # Debug: show what was calculated for each position
                with st.expander("🔧 Debug: Position Analysis Data"):
                    st.write(f"**Tier Baselines loaded:** {tier_baselines.keys()}")
                    st.write(f"**Position Analysis entries:** {len(position_analysis)}")
                    for item in position_analysis:
                        st.write(f"**{item['Position']}**: Baseline={item['Baseline']}, Best={item['Best Available']}, PPG={item['PPG']}, Value={item['Value']}, Elasticity={item['Elasticity']}, Urgency={item['Urgency']:.2f}, Slots={item['Slots']}, Tier={item['Tier']}")
                
                # Sort by urgency (highest first = most critical to address)
                position_priority = pd.DataFrame(position_analysis).sort_values('Urgency', ascending=False)
                
                # Display position priority
                st.write(f"### Position Priority for **{team_to_analyze}**")
                
                # Color coded display with View button
                for idx, row in position_priority.iterrows():
                    pos_color = position_colors.get(row['Position'], '#CCCCCC')
                    urgency_val = row['Urgency']
                    
                    if urgency_val > 1.5:
                        priority_level = "🔴 CRITICAL"
                    elif urgency_val > 1.0:
                        priority_level = "🟠 HIGH"
                    elif urgency_val > 0.5:
                        priority_level = "🟡 MEDIUM"
                    else:
                        priority_level = "🟢 LOW"
                    
                    col1, col2, col3, col4, col5 = st.columns([0.7, 2, 1.8, 1.2, 1])
                    
                    with col1:
                        st.markdown(f"<div style='background-color:{pos_color}; padding:8px; border-radius:4px; text-align:center; font-weight:bold; color:white;'>{row['Position']}</div>", unsafe_allow_html=True)
                    
                    with col2:
                        st.write(f"**{row['Best Available']}** | {row['PPG']} PPG")
                        elasticity_text = f"Elasticity: {row['Elasticity']:.1f}" if row['Elasticity'] > 0 else "Elasticity: N/A"
                        st.write(f"*Value: {row['Value']:+.1f} | Tier {int(row['Tier'])} base: {row['Baseline']} | {elasticity_text}*")
                    
                    with col3:
                        st.write(f"Slots: {row['Slots']}")
                        st.write(f"Starters: {row['Starters Left']} | Scarcity: {row['Scarcity %']}")
                    
                    with col4:
                        st.write(priority_level)
                    
                    with col5:
                        if st.button("📊", key=f"view_{row['Position']}_{idx}", help="View players at this position"):
                            pass  # Placeholder for view action
            
                # Show team's current roster (actual picks made)
                st.divider()
                st.write(f"### {team_to_analyze}'s Draft Picks")
                
                if not team_picks.empty:
                    # Build roster with tier baselines
                    roster_rows = []
                    total_ppg = 0
                    total_marg_val = 0
                    
                    # Sort by pick number to show draft order
                    team_picks_sorted = team_picks.sort_values('pick_number')
                    
                    for idx, pick in team_picks_sorted.iterrows():
                        pos = pick['position']
                        
                        # Find which slot number this is for this position
                        pos_picks_before = len(team_picks_sorted[(team_picks_sorted['position'] == pos) & (team_picks_sorted['pick_number'] < pick['pick_number'])])
                        slot_num = pos_picks_before + 1
                        slot_label = f"{pos}{slot_num}"
                        
                        # Get tier baseline for this slot
                        tier_baseline = 0
                        if pos in tier_baselines and (slot_num - 1) in tier_baselines[pos]:
                            tier_baseline = tier_baselines[pos][slot_num - 1]
                        
                        # Calculate marginal value (PPG - baseline)
                        player_ppg = pick['PPG']
                        marginal_value = player_ppg - tier_baseline
                        
                        # Total projected points (PPG * 17 games)
                        total_fpts = player_ppg * 17
                        
                        roster_rows.append({
                            'Slot': pos,
                            'S#': slot_label,
                            'Player': pick['name_x'],
                            'Pick #': int(pick['pick_number']),
                            'FPTS': round(total_fpts, 1),
                            'PPG': round(player_ppg, 1),
                            'Marg Val': round(marginal_value, 1),
                            'Baseline': round(tier_baseline, 1),
                        })
                        total_ppg += player_ppg
                        total_marg_val += marginal_value
                    
                    roster_df = pd.DataFrame(roster_rows)
                    
                    # Display as formatted table
                    st.dataframe(
                        roster_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'Slot': st.column_config.TextColumn(width="small"),
                            'S#': st.column_config.TextColumn(width="small"),
                            'Pick #': st.column_config.NumberColumn(format="%d", width="small"),
                            'Player': st.column_config.TextColumn(width="large"),
                            'FPTS': st.column_config.NumberColumn(format="%.1f", width="small"),
                            'PPG': st.column_config.NumberColumn(format="%.1f", width="small"),
                            'Marg Val': st.column_config.NumberColumn(format="%.1f", width="small"),
                            'Baseline': st.column_config.NumberColumn(format="%.1f", width="small"),
                        }
                    )
                    
                    # Summary stats
                    st.write("")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total PPG", round(total_ppg, 1))
                    with col2:
                        st.metric("Avg Marg Val", round(total_marg_val / len(roster_df), 2) if len(roster_df) > 0 else 0)
                    with col3:
                        st.metric("Total Marg Val", round(total_marg_val, 1))
                    with col4:
                        st.metric("Picks Made", len(team_picks))
                else:
                    st.write(f"No picks made yet.")
    
    # ============================================================================
    # === TAB 3: BUILD A STRATEGY (POINT RANGES BY ROUND - FROM OLD CONSIDER_OPTIONS) ===
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
                    
                    st.plotly_chart(fig, use_container_width=True)
                
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
                        st.session_state[f'target_rounds_{pos}'] = target_rounds
                        st.success(f"🎯 {pos} targets: Rounds {', '.join(map(str, sorted(target_rounds)))}")
                    else:
                        st.caption("Select rounds ↑")
    
    