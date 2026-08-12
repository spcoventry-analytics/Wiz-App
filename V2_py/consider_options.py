# consider_options.py
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

def show_consider_options():
    st.title("Consider Options")
    
    position_colors = st.session_state.get('position_colors', {})
    player_data_all = st.session_state.get('player_data_all')
    slot_counts = st.session_state.get('slot_counts', {})
    num_teams = len(st.session_state.get('teams', []))

    available_players = player_data_all[player_data_all["pick_number"] == 0].copy()

    if available_players is None or available_players.empty:
        st.warning("No available players to draft. All picks have been made or data is missing.")
        return

    # === CALCULATE POS VALUE (edge above starter baseline) ===
    # For each position: baseline = average PPG of the top N starters
    # Where N = slot_counts[position] * num_teams
    
    starter_baselines = {}
    position_std_devs = {}
    
    for pos in available_players['position'].unique():
        num_starting_slots = slot_counts.get(pos, 0) * num_teams
        pos_players = available_players[available_players['position'] == pos]
        
        if num_starting_slots > 0:
            starter_avg = pos_players.sort_values('PPG', ascending=False).head(num_starting_slots)['PPG'].mean()
            starter_baselines[pos] = starter_avg
        else:
            # Fallback: use overall position average
            starter_baselines[pos] = pos_players['PPG'].mean()
        
        # Calculate standard deviation of PPG for this position
        position_std_devs[pos] = pos_players['PPG'].std()
    
    available_players['POS_Value'] = available_players.apply(
        lambda row: row['PPG'] - starter_baselines.get(row['position'], 0),
        axis=1
    )
    
    # Normalize by position variance (std dev)
    available_players['POS_Value_Normalized'] = available_players.apply(
        lambda row: (row['PPG'] - starter_baselines.get(row['position'], 0)) / max(position_std_devs.get(row['position'], 1), 0.1),
        axis=1
    )
    
    # === SMART POSITION FILTERING (BEFORE GRAPH) ===
    # Get available positions sorted by best POS Value
    available_positions = available_players.groupby('position')['POS_Value'].max().sort_values(ascending=False)
    position_order = [""] + list(available_positions.index)
    
    st.write("### Filter Players:")
    
    default_position = st.session_state.get('consider_filter_position', '')
    position = st.radio(
        "Position (optional)", 
        position_order, 
        horizontal=True, 
        index=position_order.index(default_position) if default_position in position_order else 0
    )
    
    # Clear the filter after using it once
    if 'consider_filter_position' in st.session_state:
        del st.session_state['consider_filter_position']
    
    team = st.selectbox("NFL Team (optional)", [""] + sorted(list(available_players["team_x"].unique().astype(str))))

    # Apply filters
    filtered_players = available_players.copy()
    if position:
        filtered_players = filtered_players[filtered_players["position"] == position]
    if team:
        filtered_players = filtered_players[filtered_players["team_x"] == team]
    
    # === CREATE TABS: GRAPHS vs TABLE vs STRATEGY ===
    tab_graph, tab_table, tab_strategy = st.tabs(["📊 Gold Mine", "📋 Player Details", "📈 Round Strategy"])
    
    # === TAB 1: GOLD MINE GRAPHS (POSITION-GROUPED) ===
    with tab_graph:
        
        # Get positions sorted by best normalized POS Value
        positions_available = (
            filtered_players.groupby('position')['POS_Value_Normalized']
            .max()
            .sort_values(ascending=False)
            .index
        )

        for pos in positions_available:
            pos_players = filtered_players[filtered_players['position'] == pos].copy()
            pos_players = pos_players.dropna(subset=['PPG', 'floor', 'ceiling', 'points', 'adp'])

            if pos_players.empty:
                continue

            # Top 10 players at this position by normalized value
            pos_players = pos_players.sort_values('POS_Value_Normalized', ascending=False).head(10)
            # Sort by ADP for display
            pos_players = pos_players.sort_values('adp', ascending=True)

            color = position_colors.get(pos, '#1f77b4')

            # Calculate error distances
            error_minus = pos_players['points'] - pos_players['floor']
            error_plus = pos_players['ceiling'] - pos_players['points']

            # Format player text with normalized value badge
            y_labels = [
                f"<b>{name}</b>  <span style='color:gray; font-size:11px;'>({val:+.2f})</span>"
                for name, val in zip(pos_players['name_x'], pos_players['POS_Value_Normalized'])
            ]

            fig = go.Figure()

            # Single trace with horizontal error bars
            fig.add_trace(
                go.Scatter(
                    x=pos_players['points'],
                    y=y_labels,
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
                    customdata=pos_players[['PPG', 'POS_Value', 'POS_Value_Normalized', 'floor', 'ceiling', 'adp']],
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Projected Points: <b>%{x:.1f}</b><br>"
                        "Floor - Ceiling: %{customdata[3]:.0f} - %{customdata[4]:.0f}<br>"
                        "PPG: %{customdata[0]:.2f}<br>"
                        "POS Value: %{customdata[1]:.2f}<br>"
                        "Norm Value: %{customdata[2]:.2f}<br>"
                        "ADP: %{customdata[5]:.1f}"
                        "<extra></extra>"
                    ),
                    showlegend=False,
                )
            )

            # Dynamic plot height
            dynamic_height = max(300, len(pos_players) * 45 + 100)

            fig.update_layout(
                title=dict(
                    text=f"<b>{pos}</b> — Top Value Edges (Normalized Value in parens)",
                    font=dict(size=16)
                ),
                xaxis_title="Projected Points (Floor to Ceiling)",
                yaxis=dict(
                    type='category',
                    autorange=True,
                    tickfont=dict(size=12),
                ),
                height=dynamic_height,
                template='plotly_white',
                margin=dict(l=150, r=40, t=50, b=50),
                hoverlabel=dict(bgcolor="white", font_size=12),
            )

            st.plotly_chart(fig, use_container_width=True)
    
    # === TAB 2: FULL PLAYER DETAILS TABLE ===
    with tab_table:
        keep_columns = ['name_x', 'position', 'team_x', 
                       'points', 'PPG', 'POS_Value', 'POS_Value_Normalized', 'floor', 'ceiling', 
                       'position_rank', "tier", 'adp', "depth",
                       'age', 'college', 'draft_year_x', 'weight', 'espn_id']
        
        table_data = pd.DataFrame(filtered_players)
        existing_columns = [col for col in keep_columns if col in table_data.columns]
        table_data = table_data[existing_columns]
        table_data = table_data.sort_values(by=["position", "POS_Value_Normalized"], ascending=[True, False])
        
        # Display with better formatting
        st.dataframe(
            table_data,
            column_config={
                "points": st.column_config.NumberColumn("Points", format="%.1f"),
                "PPG": st.column_config.NumberColumn("PPG", format="%.2f"),
                "POS_Value": st.column_config.NumberColumn("POS Value", format="%.2f"),
                "POS_Value_Normalized": st.column_config.NumberColumn("Norm Value", format="%.2f"),
                "floor": st.column_config.NumberColumn("Floor", format="%.1f"),
                "ceiling": st.column_config.NumberColumn("Ceiling", format="%.1f"),
                "adp": st.column_config.NumberColumn("ADP", format="%.1f"),
            },
            hide_index=True,
            use_container_width=True
        )
    
    # === TAB 3: ROUND STRATEGY (POINT RANGES BY DRAFT ROUND) ===
    with tab_strategy:
        st.write("**Round Strategy: Build Your Hypothetical Roster**")
        st.write("*For each round, select which position to draft. See the expected player and points.*")
        
        # Initialize hypothetical picks in session state if not present
        if 'hypothetical_picks' not in st.session_state:
            st.session_state['hypothetical_picks'] = {}
        
        # Add positions to available data for this tab
        available_players_strategy = available_players.copy()
        # Drop players without ADP (they can't be assigned to a draft round)
        available_players_strategy = available_players_strategy.dropna(subset=['adp'])
        
        if available_players_strategy.empty:
            st.warning("No players with ADP data available for round strategy.")
            return
        
        available_players_strategy['draft_round'] = np.ceil(available_players_strategy['adp'] / num_teams).astype(int)
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
                    ].sort_values('POS_Value_Normalized', ascending=False)
                    
                    if not round_players.empty:
                        best_player = round_players.iloc[0]
                        st.session_state['hypothetical_picks'][round_num] = {
                            'position': selected_pos,
                            'player_name': best_player['name_x'],
                            'player_id': best_player.get('espn_id', ''),
                            'points': best_player['points'],
                            'ppg': best_player['PPG'],
                            'norm_value': best_player['POS_Value_Normalized']
                        }
                        
                        # Display the selected player
                        st.write(f"📍 **{best_player['name_x']}**")
                        st.caption(f"{best_player['points']:.0f} pts | {best_player['POS_Value_Normalized']:.2f} norm val")
                    else:
                        st.caption("No players available in this round")
                else:
                    # Remove from hypothetical if deselected
                    if round_num in st.session_state['hypothetical_picks']:
                        del st.session_state['hypothetical_picks'][round_num]
        
        # Show hypothetical roster summary
        if st.session_state['hypothetical_picks']:
            st.divider()
            st.write("**Hypothetical Roster Summary:**")
            
            hyp_picks = st.session_state['hypothetical_picks']
            total_points = sum(p['points'] for p in hyp_picks.values())
            avg_norm_val = np.mean([p['norm_value'] for p in hyp_picks.values()])
            
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
            
            # Button to save/confirm this hypothetical roster to Current Plan
            if st.button("📌 Use This Hypothetical Roster on Current Plan"):
                st.session_state['show_hypothetical_roster'] = True
                st.success("Hypothetical roster will display on Current Plan page!")
            
            if st.button("🗑️ Clear All Selections"):
                st.session_state['hypothetical_picks'] = {}
                st.session_state['show_hypothetical_roster'] = False
                st.rerun()
        
        # Reference: Show point range graphs by position
        with st.expander("📊 Reference: Point Ranges by Round (Tap to expand)"):
            st.write("*These graphs show all players at each position and which round they're expected to go in.*")
            
            # Get positions sorted by best normalized POS Value
            positions_available = (
                filtered_players.groupby('position')['POS_Value_Normalized']
                .max()
                .sort_values(ascending=False)
                .index
            )

            for pos in positions_available:
                pos_players = filtered_players[filtered_players['position'] == pos].copy()
                pos_players = pos_players.dropna(subset=['PPG', 'floor', 'ceiling', 'points', 'adp'])

                if pos_players.empty:
                    continue

                # Calculate which round each player is expected to go (ADP / num_teams ≈ round)
                # fillna just in case any NaN slipped through
                pos_players['draft_round'] = np.ceil(pos_players['adp'].fillna(999) / num_teams).astype(int)
                pos_players['draft_round'] = pos_players['draft_round'].clip(lower=1, upper=21)
                
                # Sort by draft round
                pos_players = pos_players.sort_values('draft_round', ascending=True)

                color = position_colors.get(pos, '#1f77b4')

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



