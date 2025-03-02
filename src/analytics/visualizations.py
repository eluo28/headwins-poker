from io import BytesIO
from logging import getLogger

import pandas as pd
import plotly.express as px

from dataingestion.ledger_session_helpers import (
    consolidate_sessions_with_player_mapping_details,
    load_all_ledger_sessions,
)
from dataingestion.registered_player_helpers import load_registered_players
from dataingestion.schemas.consolidated_session import ConsolidatedPlayerSession
from dataingestion.schemas.player_session_log import PlayerSessionLog
from discordbot.services.s3_service import S3Service
from src.dataingestion.schemas.registered_player import RegisteredPlayer

logger = getLogger(__name__)


async def load_sessions_and_registered_players(
    guild_id: str, s3_service: S3Service
) -> tuple[list[PlayerSessionLog], list[RegisteredPlayer]]:
    sessions = await load_all_ledger_sessions(guild_id, s3_service)
    logger.info(f"Loaded {len(sessions)} player ledger sessions")

    registered_players = await load_registered_players(guild_id, s3_service)
    logger.info(f"Loaded {len(registered_players)} registered players")

    return sessions, registered_players


async def fetch_consolidated_sessions_and_registered_players(
    guild_id: str, s3_service: S3Service
) -> tuple[list[ConsolidatedPlayerSession], list[RegisteredPlayer]]:
    sessions, registered_players = await load_sessions_and_registered_players(guild_id, s3_service)
    consolidated_sessions = consolidate_sessions_with_player_mapping_details(sessions, registered_players)
    return consolidated_sessions, registered_players


def get_file_object_of_player_nets_over_time(
    consolidated_sessions: list[ConsolidatedPlayerSession],
    registered_players: list[RegisteredPlayer],
) -> BytesIO:
    if not consolidated_sessions:
        raise ValueError("No sessions found")

    # Convert sessions to DataFrame with mapped names
    df = pd.DataFrame(
        [
            {
                "player": session.player_nickname_lowercase,
                "date": session.date,
                "net": session.net_dollars,
            }
            for session in consolidated_sessions
        ]
    )

    # Add starting data points
    starting_df = pd.DataFrame(
        [
            {
                "player": entry.player_name_lowercase,
                "date": entry.initial_details.initial_date,
                "net": entry.initial_details.initial_net_amount,
            }
            for entry in registered_players
            if entry.initial_details is not None
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
