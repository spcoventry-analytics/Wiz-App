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
    
    st.write("### Filter Players (Optional):")
    
    col_filt1, col_filt2 = st.columns(2)
    
    with col_filt1:
        default_position = st.session_state.get('consider_filter_position', '')
        position = st.selectbox(
            "Position (optional)", 
            position_order, 
            index=position_order.index(default_position) if default_position in position_order else 0
        )
        
        # Clear the filter after using it once
        if 'consider_filter_position' in st.session_state:
            del st.session_state['consider_filter_position']
    
    with col_filt2:
        team = st.selectbox("NFL Team (optional)", [""] + sorted(list(available_players["team_x"].unique().astype(str))))

    # Apply filters
    filtered_players = available_players.copy()
    if position:
        filtered_players = filtered_players[filtered_players["position"] == position]
    if team:
        filtered_players = filtered_players[filtered_players["team_x"] == team]
    
    # === CREATE TABS: GRAPHS vs TABLE ===
    tab_graph, tab_table = st.tabs(["📊 Gold Mine", "📋 Player Details"])
    
    # === TAB 1: GOLD MINE GRAPHS (POSITION-GROUPED) ===
    with tab_graph:
        
        # === CALCULATE ROUND REFERENCE LINES ===
        # Rank offensive players by ADP to show round boundaries
        offensive_positions = ['QB', 'RB', 'WR', 'TE']
        offensive_players = available_players[available_players['position'].isin(offensive_positions)].copy()
        offensive_players = offensive_players.dropna(subset=['adp', 'points']).copy()
        
        if not offensive_players.empty:
            # Sort by ADP (lowest = earliest pick) and add overall rank
            offensive_players = offensive_players.sort_values('adp', ascending=True).reset_index(drop=True)
            offensive_players['overall_rank'] = range(1, len(offensive_players) + 1)
            offensive_players['draft_round'] = (np.ceil(offensive_players['overall_rank'] / num_teams)).fillna(1).astype(int)
            
            # Calculate average points at each round boundary
            round_lines = {}
            for round_num in range(1, 22):
                round_players = offensive_players[offensive_players['draft_round'] == round_num]
                if not round_players.empty:
                    avg_points = round_players['points'].mean()
                    round_lines[round_num] = avg_points
        else:
            round_lines = {}
        
        # Calculate max round globally (for consistent coloring across positions)
        global_max_round = max(offensive_players['draft_round'].unique()) if not offensive_players.empty else 1
        
        # Color scale for rounds (cycle through a gradient)
        import colorsys
        def get_round_color(round_num, opacity=0.12):
            """Generate a color based on round number with consistent global scale"""
            hue = (round_num - 1) / max(global_max_round, 1)  # 0 to 1
            saturation = 0.5
            value = 0.85
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
            return f"rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {opacity})"
        
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
            
            # Add draft round for each player
            # First try to merge with offensive_players (which has draft_round calculated)
            if not offensive_players.empty and 'espn_id' in pos_players.columns and 'espn_id' in offensive_players.columns:
                pos_players = pos_players.merge(
                    offensive_players[['espn_id', 'draft_round']],
                    on='espn_id',
                    how='left',
                    suffixes=('', '_off')
                )
            
            # If merge didn't work or column missing, calculate draft_round from ADP
            if 'draft_round' not in pos_players.columns:
                pos_players['draft_round'] = (np.ceil(pos_players['adp'] / num_teams)).fillna(1).astype(int)
            else:
                # Fill any NaN values with calculated round
                pos_players['draft_round'] = pos_players['draft_round'].fillna(
                    (np.ceil(pos_players['adp'] / num_teams)).fillna(1).astype(int)
                )

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
            
            # Add horizontal lines between rounds (simplified)
            current_round = None
            
            for idx, (_, row) in enumerate(pos_players.iterrows()):
                player_round = int(row['draft_round'])
                
                if current_round is not None and player_round != current_round:
                    # Round changed - add a simple horizontal divider line
                    y_line = idx - 0.5
                    fig.add_hline(
                        y=y_line,
                        line_dash="solid",
                        line_color="rgba(150, 150, 150, 0.5)",
                        line_width=2,
                        layer="below"
                    )
                
                current_round = player_round

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
                    autorange='reversed',  # Best players at top
                    tickfont=dict(size=12),
                ),
                height=dynamic_height,
                template='plotly_white',
                margin=dict(l=150, r=40, t=50, b=50),
                hoverlabel=dict(bgcolor="white", font_size=12),
            )

            # Create layout with graph and control button
            col_graph, col_control = st.columns([4, 1])
            
            with col_graph:
                st.plotly_chart(fig, use_container_width=True)
            
            with col_control:
                st.write("")  # Spacing
                st.write("")
                st.write("**Target Round:**")
                target_round = st.selectbox(
                    f"Select round for {pos}",
                    ["—", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
                    key=f"gold_mine_round_{pos}",
                    label_visibility="collapsed"
                )
                
                if target_round != "—":
                    if st.button(f"📌 Target {pos} R{target_round}", use_container_width=True, key=f"btn_target_{pos}"):
                        st.session_state[f"round_{target_round}_pos"] = pos
                        st.success(f"Round {target_round} set to {pos}! Go to Strategy tab to see the player.")
                        st.rerun()
    
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