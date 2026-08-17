# position_status_bar.py
"""
Position Priority Status Bar - Persistent across all pages
Shows urgency gauges, best available players, and scarcity metrics
Can be collapsed/expanded to save screen real estate
"""

import streamlit as st
import pandas as pd
from datetime import datetime


def show_position_status_bar():
    """
    Display collapsible position priority status bar at top of page.
    Shows all 7 positions with urgency gauges, best available players, and draft status.
    
    Reads from session_state:
    - player_data_all
    - slot_counts
    - draft_order
    - my_team
    - tier_baselines
    - position_colors
    
    Returns early if data not loaded yet (safe to call during config phase)
    """
    
    player_data_all = st.session_state.get('player_data_all')
    slot_counts = st.session_state.get('slot_counts', {})
    draft_order = st.session_state.get('draft_order', [])
    my_team = st.session_state.get('my_team')
    tier_baselines = st.session_state.get('tier_baselines', {})
    position_colors = st.session_state.get('position_colors', {})
    
    # Guard: only show if all required data is loaded
    if player_data_all is None or player_data_all.empty:
        return
    
    if not slot_counts or not draft_order or not my_team:
        return
    
    if not tier_baselines or not position_colors:
        return
    
    num_teams = len(draft_order) if draft_order else 1
    
    # Create collapsible status bar
    with st.expander("📊 **Position Priority Status** — Click to expand urgency details", expanded=False):
        st.write("")  # Spacing
        
        # Get my team's picks
        my_team_picks = player_data_all[player_data_all['owner'] == my_team].copy() if my_team else pd.DataFrame()
        
        # Calculate priority for each position
        position_status = []
        
        for pos in ['QB', 'RB', 'WR', 'TE', 'LB', 'DL', 'DB']:
            total_slots = slot_counts.get(pos, 0)
            if total_slots == 0:
                continue
            
            # Count filled slots for my team
            filled_slots = len(my_team_picks[my_team_picks['position'] == pos])
            empty_slots = total_slots - filled_slots
            
            # Get available players at this position
            available_players = player_data_all[
                (player_data_all['position'] == pos) & 
                (player_data_all['pick_number'] == 0)
            ].sort_values('PPG', ascending=False)
            
            best_available = available_players.iloc[0] if len(available_players) > 0 else None
            
            # Calculate tier baseline and elasticity
            tier_baseline = 0
            if pos in tier_baselines and filled_slots in tier_baselines[pos]:
                tier_baseline = tier_baselines[pos][filled_slots]
            
            # Elasticity: PPG cost if we wait one round
            elasticity = 0
            if best_available is not None and len(available_players) > num_teams:
                next_round_available = available_players.iloc[num_teams]
                elasticity = best_available['PPG'] - next_round_available['PPG']
            
            # Urgency score (0-2.0 scale for gauge)
            urgency_score = 0
            if empty_slots > 0:
                if elasticity > 1.0:
                    urgency_score = 1.5 + (elasticity / 5.0)  # High elasticity = more urgent
                elif elasticity > 0.5:
                    urgency_score = 1.0
                else:
                    urgency_score = 0.5
            
            # Scarcity: ADP-aware drafted count
            adp_aware_drafted = 0
            if best_available is not None and pd.notna(best_available.get('adp')):
                best_available_adp = best_available['adp']
                adp_aware_drafted = len(player_data_all[
                    (player_data_all['position'] == pos) & 
                    (player_data_all['pick_number'] > 0) &
                    (player_data_all['adp'] <= best_available_adp)
                ])
            
            scarcity_ratio = (adp_aware_drafted / num_teams * 100) if num_teams > 0 else 0
            
            position_status.append({
                'Position': pos,
                'Best Available': best_available['name_x'] if best_available is not None else 'NONE',
                'PPG': round(best_available['PPG'], 1) if best_available is not None else 0,
                'Urgency': urgency_score,
                'Slots': f"{filled_slots}/{total_slots}",
                'Empty': empty_slots,
                'Starters': len(available_players[available_players['PPG'] >= tier_baseline]) if tier_baseline > 0 else len(available_players),
                'Scarcity %': int(scarcity_ratio),
                'Elasticity': round(elasticity, 1),
                'Color': position_colors.get(pos, '#CCCCCC'),
            })
        
        # Display as gauge-like cards in columns
        if position_status:
            # Header row with position labels
            cols = st.columns(7)
            for idx, status in enumerate(position_status):
                with cols[idx]:
                    pos = status['Position']
                    color = status['Color']
                    
                    # Position header with color
                    st.markdown(
                        f"<div style='background-color:{color}; padding:8px; border-radius:4px; text-align:center; "
                        f"font-weight:bold; color:white; margin-bottom:8px;'>{pos}</div>",
                        unsafe_allow_html=True
                    )
                    
                    # Best available player
                    st.caption(f"**{status['Best Available']}**")
                    st.caption(f"{status['PPG']} PPG")
                    
                    # Urgency gauge (simple text representation)
                    urgency_val = status['Urgency']
                    if urgency_val > 1.5:
                        gauge = "🔴🔴🔴 CRITICAL"
                    elif urgency_val > 1.0:
                        gauge = "🟠🟠 HIGH"
                    elif urgency_val > 0.5:
                        gauge = "🟡 MEDIUM"
                    else:
                        gauge = "🟢 LOW"
                    
                    st.caption(gauge)
                    
                    # Slot status
                    st.caption(f"**Slots:** {status['Slots']}")
                    st.caption(f"**Starters:** {status['Starters']}")
                    st.caption(f"**Scarcity:** {status['Scarcity %']}%")
                    
                    # Elasticity warning
                    if status['Elasticity'] > 1.0:
                        st.caption(f"⚡ Elasticity: {status['Elasticity']}")
        
        st.divider()
        
        # Draft status summary
        st.write("**Draft Status Summary:**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            picks_made = len(my_team_picks)
            st.metric("Your Picks", picks_made)
        
        with col2:
            # Count how many critical positions
            critical_positions = sum(1 for s in position_status if s['Urgency'] > 1.5)
            st.metric("🔴 Critical", critical_positions)
        
        with col3:
            # Draft picks made overall
            total_picks = len(player_data_all[player_data_all['pick_number'] > 0])
            st.metric("Total Picks", total_picks)
        
        with col4:
            # Picks left
            total_possible_picks = len(draft_order) * 21
            picks_left = total_possible_picks - total_picks
            st.metric("Picks Left", picks_left)
