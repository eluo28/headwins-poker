from io import BytesIO
from logging import getLogger
from typing import List
import pandas as pd

import plotly.express as px

from src.analytics.log_analytics import calculate_vpip_by_player_across_all_logs, calculate_vpip_by_player
from src.dataingestion.schemas.poker_log import PokerLog
logger = getLogger(__name__)


def get_file_object_of_total_vpip(logs: list[PokerLog]) -> BytesIO:
    """
    Creates a bar graph showing VPIP percentage for each player across all sessions.
    
    Args:
        logs: List of poker logs to analyze
        
    Returns:
        BytesIO buffer containing the graph image
    """
    
    # Get VPIP percentages
    vpip_by_player = calculate_vpip_by_player_across_all_logs(logs)
    
    # Sort by VPIP percentage ascending
    sorted_players = sorted(vpip_by_player.items(), key=lambda x: x[1], reverse=False)
    players = [p[0] for p in sorted_players]
    vpip_values = [p[1] for p in sorted_players]

    # Create bar chart
    fig = px.bar(
        x=players,
        y=vpip_values,
        text=[f"{v}%" for v in vpip_values],
    )

    # Update layout
    fig.update_layout(
        title="VPIP % by Player Across All Logs",
        xaxis_title="Player",
        yaxis_title="VPIP %",
        yaxis_range=[0, 100],
        showlegend=False,
        template="plotly_white"
    )

    # Save to buffer
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    buffer.seek(0)
    return buffer


def get_file_object_of_vpip_over_time(logs: List[PokerLog]) -> BytesIO:
    """
    Creates a scatter plot showing VPIP percentage for each player over time.
    Each player is represented by a different color/marker in the legend.
    
    Args:
        logs: List of poker logs to analyze
        
    Returns:
        BytesIO buffer containing the graph image
    """
    # Create a list to store data for each log
    data = []
    
    # Sort logs by date
    sorted_logs = sorted(logs, key=lambda x: x.date)
    
    # Calculate VPIP for each log and create data points
    for log in sorted_logs:
        vpip_by_player = calculate_vpip_by_player(log)
        
        for player, vpip in vpip_by_player.items():
            data.append({
                'date': log.date,
                'player': player,
                'vpip': vpip
            })
    
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(data)
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x='date',
        y='vpip',
        color='player',
        labels={
            'date': 'Date',
            'vpip': 'VPIP %',
            'player': 'Player'
        },
        title='VPIP % by Player Over Time'
    )
    
    # Update layout
    fig.update_layout(
        yaxis_range=[0, 100],
        template="plotly_white",
        xaxis_tickformat='%Y-%m-%d'
    )
    
    # Add hover data
    fig.update_traces(
        hovertemplate="<br>".join([
            "Date: %{x}",
            "VPIP: %{y}%",
            "<extra></extra>"
        ])
    )
    
    # Save to buffer
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    buffer.seek(0)
    return buffer
