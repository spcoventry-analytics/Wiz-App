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
    
    # === CREATE TABS: GRAPHS vs TABLE ===
    tab_graph, tab_table = st.tabs(["📊 Gold Mine", "📋 Player Details"])
    
    # === TAB 1: GOLD MINE GRAPHS ===
    with tab_graph:
        # Get positions sorted by best normalized POS Value
        positions_available = filtered_players.groupby('position')['POS_Value_Normalized'].max().sort_values(ascending=False).index
        
        for pos in positions_available:
            pos_players = filtered_players[filtered_players['position'] == pos].copy()
            pos_players = pos_players.dropna(subset=['PPG', 'floor', 'ceiling', 'points'])
            
            if pos_players.empty:
                continue
            
            # Top 10 players at this position
            pos_players = pos_players.sort_values('POS_Value_Normalized', ascending=False).head(10)
            pos_players = pos_players.sort_values('points', ascending=True)
            
            color = position_colors.get(pos, '#999999')
            
            # Create figure for this position
            fig = go.Figure()
            
            # Add a line and dot for each player
            for idx, (_, player) in enumerate(pos_players.iterrows()):
                player_name = player['name_x']
                pos_value = player['POS_Value']
                pos_value_norm = player['POS_Value_Normalized']
                
                floor_points = player['floor']
                ceiling_points = player['ceiling']
                gun_to_head = player['points']
                
                # Horizontal line from floor to ceiling
                fig.add_trace(go.Scatter(
                    x=[floor_points, ceiling_points],
                    y=[idx, idx],
                    mode='lines',
                    line=dict(color=color, width=3),
                    hoverinfo='skip',
                    showlegend=False
                ))
                
                # Dot at gun-to-head estimate
                fig.add_trace(go.Scatter(
                    x=[gun_to_head],
                    y=[idx],
                    mode='markers',
                    marker=dict(
                        size=14,
                        color=color,
                        line=dict(color='white', width=2)
                    ),
                    hovertemplate=f"<b>{player_name}</b><br>Points: {gun_to_head:.1f}<br>PPG: {player['PPG']:.2f}<br>POS Value: {pos_value:.2f}<br>Norm Value: {pos_value_norm:.2f}<br>Range: {floor_points:.0f}-{ceiling_points:.0f}<extra></extra>",
                    showlegend=False
                ))
                
                # Label: name above dot, normalized POS Value below
                fig.add_annotation(
                    x=gun_to_head,
                    y=idx + 0.35,
                    text=player_name,
                    showarrow=False,
                    font=dict(size=9),
                    xanchor='center'
                )
                fig.add_annotation(
                    x=gun_to_head,
                    y=idx - 0.35,
                    text=f"({pos_value_norm:.2f})",
                    showarrow=False,
                    font=dict(size=8, color='gray'),
                    xanchor='center'
                )
            
            fig.update_layout(
                title=f"{pos} - Top Value Edges (Normalized)",
                xaxis_title="Projected Points (Season)",
                yaxis_title="Players",
                hovermode='closest',
                height=500,
                template='plotly_white',
                yaxis=dict(showticklabels=False),
                margin=dict(l=50, r=50, t=60, b=50)
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



