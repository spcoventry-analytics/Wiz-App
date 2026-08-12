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
    your_team_default = st.session_state.get('your_team', draft_order[0] if draft_order else None)
    
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
    
    # Get picks made by this team
    team_picks = player_data_all[(player_data_all['pick_number'] > 0) & (player_data_all['owner'] == team_to_analyze)]
    
    # Count filled slots by position
    filled_by_position = {}
    for pos in slot_counts.keys():
        if pos not in ["IR", ""]:
            filled_by_position[pos] = len(team_picks[team_picks['position'] == pos])
    
    # FLEX capacity: can be filled by RB, WR, or TE
    flex_slots_available = slot_counts.get("FLEX", 0)
    flex_positions = ["RB", "WR", "TE"]
    
    # Recalculate RB/WR/TE capacity accounting for FLEX
    adjusted_capacity = {}
    adjusted_capacity["RB"] = slot_counts.get("RB", 0) + flex_slots_available
    adjusted_capacity["WR"] = slot_counts.get("WR", 0) + flex_slots_available
    adjusted_capacity["TE"] = slot_counts.get("TE", 0) + flex_slots_available
    
    # Keep other positions as-is (LB, DL, DB, etc.)
    for pos in slot_counts.keys():
        if pos not in ["IR", "", "RB", "WR", "TE", "FLEX"]:
            adjusted_capacity[pos] = slot_counts.get(pos, 0)
    
    # Available players (not yet drafted)
    available_players = player_data_all[player_data_all["pick_number"] == 0]
    
    if available_players.empty:
        st.warning("No available players remaining!")
        return
    
    # Calculate position urgency
    num_teams = len(draft_order)
    position_analysis = []
    
    for pos in adjusted_capacity.keys():
        total_slots = adjusted_capacity.get(pos, 0)
        filled_slots = filled_by_position.get(pos, 0)
        empty_slots = total_slots - filled_slots
        
        # Determine which tier we're currently drafting from
        # This is based on how many slots we've already filled at this position
        current_tier = filled_slots
        
        # Get available players at this position
        pos_players = available_players[available_players['position'] == pos].sort_values('points', ascending=False)
        
        # Get tier baseline for current tier
        tier_baseline = 0
        if pos in tier_baselines and current_tier in tier_baselines[pos]:
            tier_baseline = tier_baselines[pos][current_tier]
        
        # Count available players ABOVE this tier's baseline (startable quality for THIS slot)
        available_above_tier = len(pos_players[pos_players['PPG'] >= tier_baseline]) if tier_baseline > 0 else len(pos_players)
        
        # Best available at this position
        best_available = pos_players.iloc[0] if len(pos_players) > 0 else None
        
        # Scarcity calculation - ADJUSTED FOR ADP
        # For tier-based analysis: scarcity = how many players at this position (in this tier) have been drafted
        # Each tier has num_teams players, so max scarcity is num_teams
        num_teams = len(draft_order)
        drafted_at_pos = len(player_data_all[
            (player_data_all['position'] == pos) & 
            (player_data_all['pick_number'] > 0)
        ])
        
        # ADP-aware scarcity: only count drafted players with ADP <= best_available's ADP
        # This filters out "wasted" high-ADP picks and shows real scarcity
        adp_aware_drafted = drafted_at_pos  # default
        if best_available is not None and pd.notna(best_available.get('adp')):
            best_available_adp = best_available['adp']
            adp_aware_drafted = len(player_data_all[
                (player_data_all['position'] == pos) & 
                (player_data_all['pick_number'] > 0) &
                (player_data_all['adp'] <= best_available_adp)
            ])
            scarcity_ratio = adp_aware_drafted / num_teams if num_teams > 0 else 0
        else:
            # No ADP data, fall back to basic scarcity
            scarcity_ratio = drafted_at_pos / num_teams if num_teams > 0 else 0
        
        # Urgency combines: (1) empty slots need to fill, (2) scarcity of available STARTABLE players
        # If no starters left for this tier, it's CRITICAL
        urgency_score = (empty_slots / total_slots if total_slots > 0 else 0) + (scarcity_ratio * 0.5)
        if available_above_tier <= empty_slots:
            # Not enough starters left to fill all slots!
            urgency_score += 1.0
        
        # Only show if team has slots to fill at this position or it's scarce
        if empty_slots > 0 or scarcity_ratio > 0.3:
            position_analysis.append({
                'Position': pos,
                'Slots': f"{filled_slots}/{total_slots}",
                'Empty': empty_slots,
                'Tier': current_tier + 1,  # Display 1-indexed
                'Baseline (This Tier)': round(tier_baseline, 1),
                'Best Available': best_available['name_x'] if best_available is not None else 'NONE',
                'PPG': round(best_available['points'], 1) if best_available is not None else 0,
                'ADP': round(best_available['adp'], 0) if best_available is not None and pd.notna(best_available.get('adp')) else 'N/A',
                'Starters Left (Tier)': available_above_tier,
                'Drafted (ADP ≤ Best)': adp_aware_drafted,
                'Scarcity': f"{int(scarcity_ratio * 100)}%",
                'Urgency': urgency_score,
            })
    
    # Sort by urgency (highest first = most critical to address)
    position_priority = pd.DataFrame(position_analysis).sort_values('Urgency', ascending=False)
    
    # Display position priority
    st.write(f"### Position Priority for **{team_to_analyze}**")
    st.write("**Tier** = which slot you're filling (1st RB = Tier 1, 2nd RB = Tier 2, etc.)")
    st.write("**Baseline (This Tier)** = avg PPG of that tier from draft pool snapshot at start")
    st.write("**Starters Left (Tier)** = available players ABOVE this tier's baseline")
    st.write("**ADP-aware scarcity** = only counts drafted players with ADP ≤ best available")
    st.write("**🔴 CRITICAL**: Not enough starters left to fill remaining slots OR multiple empty slots + high scarcity")
    st.write("**🟠 HIGH**: Multiple empty slots OR real scarcity of top players")
    st.write("**🟡 MEDIUM**: One empty slot + moderate scarcity")
    st.write("**🟢 LOW**: Slots filled OR plenty of starters left for this tier")
    st.write("")
    
    # Color coded display
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
        
        col1, col2, col3, col4, col5 = st.columns([0.8, 1.5, 2, 1.5, 1.2])
        
        with col1:
            st.markdown(f"<div style='background-color:{pos_color}; padding:8px; border-radius:4px; text-align:center; font-weight:bold;'>{row['Position']}</div>", unsafe_allow_html=True)
        
        with col2:
            st.write(f"**{row['Best Available']}**")
            st.write(f"{row['PPG']} PPG | ADP: {row['ADP']}")
            st.write(f"*Tier {row.get('Tier', '?')} baseline: {row.get('Baseline (This Tier)', '?')} PPG*")
        
        with col3:
            st.write(f"Slots: {row['Slots']}")
            drafted_col = row.get('Drafted (ADP ≤ Best)', row.get('Drafted (Top N)', '?'))
            st.write(f"Starters: {row.get('Starters Left (Tier)', '?')} | Drafted: {drafted_col}")
        
        with col4:
            st.write(f"{priority_level}")
            st.write(f"Scarcity: {row['Scarcity']}")
        
        with col5:
            if st.button("📊 View", key=f"view_{row['Position']}_{team_to_analyze}"):
                st.session_state['consider_filter_position'] = row['Position']
                st.info(f"✅ Go to **Consider Options** to view {row['Position']} players")
    
    # Show team's current roster
    st.divider()
    st.write(f"### {team_to_analyze}'s Current Roster:")
    if not team_picks.empty:
        roster_display = team_picks[['name_x', 'position', 'points', 'pick_number']].copy()
        roster_display.columns = ['Player', 'Pos', 'Proj PPG', 'Pick #']
        roster_display = roster_display.sort_values('Pick #')
        st.dataframe(roster_display, use_container_width=True, hide_index=True)
    else:
        st.write(f"No picks made yet.")

    
    
    
    