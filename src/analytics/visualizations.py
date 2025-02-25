from io import BytesIO
from logging import getLogger

import pandas as pd
import plotly.express as px

from parsing.schemas.session import PokerSession
from src.parsing.player_mapping import (
    PLAYER_ID_TO_LOWERCASE_NAME,
    PLAYER_NICKNAME_TO_LOWERCASE_NAME,
)
from src.parsing.schemas.starting_data_entry import StartingDataEntry

logger = getLogger(__name__)


def get_file_object_of_player_nets_over_time(
    sessions: list[PokerSession], starting_data: list[StartingDataEntry]
) -> BytesIO:
    if not sessions and not starting_data:
        raise ValueError("No sessions or starting data found")
    # Convert sessions to DataFrame with mapped names
    df = pd.DataFrame(
        [
            {
                "player": PLAYER_ID_TO_LOWERCASE_NAME.get(
                    session.player_id,
                    PLAYER_NICKNAME_TO_LOWERCASE_NAME.get(
                        session.player_nickname_lowercase,
                        session.player_nickname_lowercase,
                    ),
                ),
                "date": session.session_start_at.date(),
                "net": session.net_dollars,
            }
            for session in sessions
        ]
    )

    # Add starting data points
    starting_df = pd.DataFrame(
        [
            {
                "player": entry.player_name_lowercase,
                "date": entry.date,
                "net": entry.net_dollars,
            }
            for entry in starting_data
        ]
    )

    # Combine starting data with sessions
    df = pd.concat([starting_df, df])

    # Sort by date and get cumulative sum for each player
    df = df.sort_values("date")
    player_nets = df.groupby(["date", "player"])["net"].sum().reset_index()
    player_nets = player_nets.pivot(index="date", columns="player", values="net")
    player_nets = player_nets.fillna(0).cumsum()

    # Create plot using Plotly
    fig = px.line(
        player_nets,
        markers=True,
        title="Player Net Profits/Losses Over Time",
    )

    # Update legend names to include final values and sort by value
    sorted_traces = sorted(
        fig.data,
        key=lambda trace: player_nets[trace.name].iloc[-1],  # type: ignore
        reverse=True,
    )
    fig.data = sorted_traces

    for trace in fig.data:
        player_name = trace.name  # type: ignore
        final_value = player_nets[player_name].iloc[-1]
        trace.name = f"{player_name} (${final_value:,.2f})"  # type: ignore

    # Customize layout
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Net Profit/Loss ($)",
        xaxis_tickangle=45,
        xaxis_range=[
            player_nets.index[0],
            max(
                player_nets.index[-1],  # Use last date if more than 10 days
                player_nets.index[0] + pd.Timedelta(days=10),  # Ensure at least 10 days shown
            ),
        ],
        legend={"yanchor": "middle", "y": 0.5, "xanchor": "left", "x": 1.02},
        height=600,
        width=1000,
    )

    # Save to buffer
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    buffer.seek(0)
    return buffer
