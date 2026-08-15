# current_plan.py
import streamlit as st
import numpy as np
import pandas as pd

def show_current_plan():
    st.title("Current Plan - Position Priority")
    
    player_data_all = st.session_state.get('player_data_all')
    draft_order = st.session_state.get('draft_order', [])
    position_colors = st.session_state.get('position_colors', {})
    slot_counts = st.session_state.get('slot_counts', {})
    tier_baselines = st.session_state.get('tier_baselines', {})
    your_team_default = st.session_state.get('my_team', draft_order[0] if draft_order else None)
    
    if player_data_all is None or player_data_all.empty:
        st.warning("No player data available.")
        return
    
    if not slot_counts:
        st.warning("League slot structure not loaded. Please configure your league first.")
        return
    
    # Team selector
    team_to_analyze = st.selectbox(
        "Select team to analyze",
        draft_order,
        index=draft_order.index(your_team_default) if your_team_default in draft_order else 0,
        help="See position priorities for this team"
    )
    
    # === SHOW HYPOTHETICAL ROSTER IF ENABLED ===
    if st.session_state.get('show_hypothetical_roster', False) and st.session_state.get('hypothetical_picks'):
        st.divider()
        st.write("### ≡ƒÄ» Hypothetical Draft Plan")
        
        hyp_picks = st.session_state['hypothetical_picks']
        
        # Display hypothetical roster
        hyp_rows = []
        total_hyp_points = 0
        
        for round_num in sorted(hyp_picks.keys()):
            pick = hyp_picks[round_num]
            hyp_rows.append({
                'Round': round_num,
                'Position': pick['position'],
                'Player': pick['player_name'],
                'Points': round(pick['points'], 1),
                'PPG': round(pick['ppg'], 2),
                'Norm Value': round(pick['norm_value'], 2)
            })
            total_hyp_points += pick['points']
        
        hyp_df = pd.DataFrame(hyp_rows)
        st.dataframe(hyp_df, use_container_width=True, hide_index=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Points (Hyp)", f"{total_hyp_points:.0f}")
        with col2:
            st.metric("Picks in Plan", len(hyp_picks))
        with col3:
            st.metric("Avg Norm Value", f"{np.mean([p['norm_value'] for p in hyp_picks.values()]):.2f}")
        
        st.divider()
    
    # Get picks made by this team
    team_picks = player_data_all[(player_data_all['pick_number'] > 0) & (player_data_all['owner'] == team_to_analyze)]
    
    # Count filled slots by position (BASE positions only, not including FLEX)
    filled_by_position = {}
    for pos in slot_counts.keys():
        if pos not in ["IR", "", "FLEX"]:
            filled_by_position[pos] = len(team_picks[team_picks['position'] == pos])
    
    # Available players (not yet drafted)
    available_players = player_data_all[player_data_all["pick_number"] == 0]
    
    if available_players.empty:
        st.warning("No available players remaining!")
        return
    
    # Explanatory notes in expander (not intrusive on mobile)
    with st.expander("Γä╣∩╕Å How to read this table"):
        st.write("""
        - **Tier** = which slot you're filling (RB1=1st RB slot, RB2=2nd RB slot, etc.)
        - **Baseline** = average PPG of that tier from the full player pool at draft start
        - **Value** = Player's PPG minus baseline (anything >0 is above average, >1 is significantly above)
        - **Starters Left** = available players ABOVE this tier's baseline (true starter quality)
        - **Drafted (ADPΓëñBest)** = competitors' picks at this position with ADP Γëñ best available (scarcity indicator)
        - ≡ƒö┤ **CRITICAL**: Not enough starters for remaining slots or very scarce
        - ≡ƒƒá **HIGH**: Multiple empty slots or high scarcity
        - ≡ƒƒí **MEDIUM**: One empty slot + moderate scarcity
        - ≡ƒƒó **LOW**: Slots filled or abundant starters
        """)
    
    st.write("")
    
    # Calculate position urgency for BASE positions only (not including FLEX capacity)
    num_teams = len(draft_order)
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
        pos_players = available_players[available_players['position'] == pos].sort_values('PPG', ascending=False)
        
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
        
        # Urgency: combines slot needs + scarcity
        urgency_score = (empty_slots / total_slots if total_slots > 0 else 0) + (scarcity_ratio * 0.5)
        if empty_slots > 0 and available_above_tier <= empty_slots:
            urgency_score += 1.0  # CRITICAL if not enough starters
        
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
            'ADP': round(best_available['adp'], 0) if best_available is not None and pd.notna(best_available.get('adp')) else 'N/A',
            'Starters Left': available_above_tier,
            'Drafted (ADPΓëñBest)': adp_aware_drafted,
            'Scarcity %': f"{int(scarcity_ratio * 100)}%",
            'Urgency': urgency_score,
        })
    
    # Sort by urgency (highest first = most critical to address)
    position_priority = pd.DataFrame(position_analysis).sort_values('Urgency', ascending=False)
    
    # Display position priority
    st.write(f"### Position Priority for **{team_to_analyze}**")
    
    # Color coded display with View button
    for idx, row in position_priority.iterrows():
        pos_color = position_colors.get(row['Position'], '#CCCCCC')
        urgency_val = row['Urgency']
        
        if urgency_val > 1.5:
            priority_level = "≡ƒö┤ CRITICAL"
        elif urgency_val > 1.0:
            priority_level = "≡ƒƒá HIGH"
        elif urgency_val > 0.5:
            priority_level = "≡ƒƒí MEDIUM"
        else:
            priority_level = "≡ƒƒó LOW"
        
        col1, col2, col3, col4, col5 = st.columns([0.7, 2, 1.8, 1.2, 1])
        
        with col1:
            st.markdown(f"<div style='background-color:{pos_color}; padding:8px; border-radius:4px; text-align:center; font-weight:bold; color:white;'>{row['Position']}</div>", unsafe_allow_html=True)
        
        with col2:
            st.write(f"**{row['Best Available']}** | {row['PPG']} PPG")
            st.write(f"*Value: {row['Value']:+.1f} | Tier {int(row['Tier'])} base: {row['Baseline']}*")
        
        with col3:
            st.write(f"Slots: {row['Slots']}")
            st.write(f"Starters: {row['Starters Left']} | Scarcity: {row['Scarcity %']}")
        
        with col4:
            st.write(priority_level)
        
        with col5:
            if st.button("≡ƒôè", key=f"view_{row['Position']}_{idx}", help="View players at this position"):
                st.session_state['consider_filter_position'] = row['Position']
                st.session_state['view_position_triggered'] = True
    
    
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
    
