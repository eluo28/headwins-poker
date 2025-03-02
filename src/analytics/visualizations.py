from io import BytesIO
from logging import getLogger

import pandas as pd
import plotly.express as px

from src.dataingestion.ledger_session_helpers import (
    consolidate_sessions_with_player_mapping_details,
    load_all_ledger_sessions,
)
from src.dataingestion.registered_player_helpers import load_registered_players
from src.dataingestion.schemas.consolidated_session import ConsolidatedPlayerSession
from src.dataingestion.schemas.player_session_log import PlayerSessionLog
from src.dataingestion.schemas.registered_player import RegisteredPlayer
from src.discordbot.services.s3_service import S3Service

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


def get_file_object_of_player_played_time_totals(
    consolidated_sessions: list[ConsolidatedPlayerSession],
    registered_players: list[RegisteredPlayer],
) -> BytesIO:
    """
    Creates a bar chart showing total time played for each player.

    Args:
        consolidated_sessions: List of consolidated player sessions
        registered_players: List of registered players

    Returns:
        BytesIO object containing the rendered plot image
    """

    # Calculate total hours played per player
    player_times = {}
    for session in consolidated_sessions:
        player = session.player_nickname_lowercase
        if player not in player_times:
            player_times[player] = 0
        # Convert milliseconds to hours
        player_times[player] += session.time_played_ms / (1000 * 60 * 60)

    # If no sessions, use registered player names with 0 hours
    if not player_times:
        player_times = {player.player_name_lowercase: 0 for player in registered_players}

    # Convert to DataFrame and sort by total time
    df = pd.DataFrame([{"player": player, "hours": hours} for player, hours in player_times.items()]).sort_values(
        "hours", ascending=True
    )

    # Create bar chart
    fig = px.bar(
        df,
        x="player",
        y="hours",
        title="Total Hours Played by Player",
        labels={"hours": "Hours Played", "player": "Player"},
    )

    # Add hour values as text on bars
    fig.update_traces(text=[f"{hours:.1f}h" for hours in df["hours"]], textposition="outside")

    # Update layout
    fig.update_layout(
        showlegend=False,  # Remove legend since it's redundant for a bar chart
        xaxis_title="Player",
        yaxis_title="Hours Played",
        height=600,
        width=1000,
    )

    # Save to BytesIO
    img_bytes = BytesIO()
    fig.write_image(img_bytes, format="png")
    img_bytes.seek(0)

    return img_bytes


def get_file_object_of_player_nets_over_time(
    consolidated_sessions: list[ConsolidatedPlayerSession],
    registered_players: list[RegisteredPlayer],
) -> BytesIO:
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


def get_file_object_of_player_profit_per_hour(
    consolidated_sessions: list[ConsolidatedPlayerSession],
    registered_players: list[RegisteredPlayer],
) -> BytesIO:
    """
    Creates a bar chart showing profit per hour for each player.

    Args:
        consolidated_sessions: List of consolidated player sessions
        registered_players: List of registered players

    Returns:
        BytesIO object containing the rendered plot image
    """
    # Calculate profit per hour for each player
    player_stats = {}
    for session in consolidated_sessions:
        player = session.player_nickname_lowercase
        if player not in player_stats:
            player_stats[player] = {"total_profit": 0, "total_hours": 0}

        # Add profit and hours
        player_stats[player]["total_profit"] += float(session.net_dollars)
        player_stats[player]["total_hours"] += session.time_played_ms / (1000 * 60 * 60)  # Convert ms to hours

    # If we have stats, calculate hourly rate and create DataFrame
    if player_stats:
        df = pd.DataFrame(
            [
                {
                    "player": player,
                    "profit_per_hour": stats["total_profit"] / stats["total_hours"] if stats["total_hours"] > 0 else 0,
                }
                for player, stats in player_stats.items()
            ]
        ).sort_values("profit_per_hour", ascending=True)
    else:
        # If no stats, use registered players with 0 profit/hour
        df = pd.DataFrame(
            [{"player": player.player_name_lowercase, "profit_per_hour": 0} for player in registered_players]
        )

    # Create bar chart
    fig = px.bar(
        df,
        x="player",
        y="profit_per_hour",
        title="Profit per Hour by Player",
        labels={"profit_per_hour": "Profit per Hour ($)", "player": "Player"},
    )

    # Add profit per hour values to player names
    fig.update_traces(text=[f"${x:,.2f}/hr" for x in df["profit_per_hour"]], textposition="outside")

    # Update layout
    fig.update_layout(
        xaxis_title="Player",
        yaxis_title="Profit per Hour ($)",
        height=600,
        width=1000,
    )

    # Save to BytesIO
    img_bytes = BytesIO()
    fig.write_image(img_bytes, format="png")
    img_bytes.seek(0)

    return img_bytes


def get_file_object_of_buy_in_analysis(
    consolidated_sessions: list[ConsolidatedPlayerSession],
) -> BytesIO:
    """
    Creates a scatter plot showing the relationship between buy-in amounts and final results.
    Also includes a trend line and correlation analysis.

    Args:
        consolidated_sessions: List of consolidated player sessions

    Returns:
        BytesIO object containing the rendered plot image
    """
    # Extract buy-in and net result data, calculating averages per player
    player_stats = {}
    for session in consolidated_sessions:
        player = session.player_nickname_lowercase
        if player not in player_stats:
            player_stats[player] = {"total_buy_in": 0, "total_net": 0, "session_count": 0, "dates": []}

        player_stats[player]["total_buy_in"] += float(session.buy_in_dollars)
        player_stats[player]["total_net"] += float(session.net_dollars)
        player_stats[player]["session_count"] += 1
        player_stats[player]["dates"].append(session.date)

    # Calculate averages and create data points
    data = []
    for player, stats in player_stats.items():
        avg_buy_in = stats["total_buy_in"] / stats["session_count"]
        avg_net = stats["total_net"] / stats["session_count"]
        roi = stats["total_net"] / stats["total_buy_in"] if stats["total_buy_in"] != 0 else 0
        data.append(
            {
                "player": player,
                "avg_buy_in": avg_buy_in,
                "avg_net_profit": avg_net,
                "roi": roi,
                "session_count": stats["session_count"],
                "date_range": f"{min(stats['dates'])} to {max(stats['dates'])}",
            }
        )

    # If no valid data, return an empty plot with a message
    if not data:
        fig = px.scatter(
            title="Buy-In Analysis (No Data Available)",
        )
        fig.add_annotation(text="No buy-in data available.", showarrow=False, font={"size": 14})
        buffer = BytesIO()
        fig.write_image(buffer, format="png")
        buffer.seek(0)
        return buffer

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Create scatter plot
    fig = px.scatter(
        df,
        x="avg_buy_in",
        y="avg_net_profit",
        color="player",
        hover_data=["session_count", "roi", "date_range"],
        title="Buy-In Analysis: Average Buy-In vs Average Net Result by Player",
        labels={
            "avg_buy_in": "Average Buy-In Amount ($)",
            "avg_net_profit": "Average Net Result ($)",
            "player": "Player",
            "roi": "ROI",
            "session_count": "Number of Sessions",
        },
        trendline="ols",  # Add trend line using Ordinary Least Squares
    )

    # Calculate correlation
    correlation = df["avg_buy_in"].corr(df["avg_net_profit"])

    # Add correlation annotation
    fig.add_annotation(
        x=1.15,  # Position outside the graph on the right
        y=-0.15,  # Position below the graph
        xref="paper",
        yref="paper",
        text=f"Correlation: {correlation:.2f}",
        showarrow=False,
        font={"size": 12},
        bgcolor="rgba(255, 255, 255, 0.7)",
        bordercolor="black",
        borderwidth=1,
        borderpad=4,
    )
    # Add horizontal line at y=0 (break-even point)
    fig.add_hline(
        y=0, line_dash="dash", line_color="gray", annotation_text="Break Even", annotation_position="bottom right"
    )

    # Add text labels for each player
    for _, row in df.iterrows():
        fig.add_annotation(
            x=row["avg_buy_in"],
            y=row["avg_net_profit"],
            text=f"{row['player']}\n({row['session_count']} {'session' if row['session_count'] == 1 else 'sessions'})",
            showarrow=True,
            arrowhead=0,
            arrowsize=0.3,
            arrowwidth=1,
            arrowcolor="rgba(0,0,0,0.5)",
            ax=15,  # Offset in pixels
            ay=-15,  # Offset in pixels
            font={"size": 10},
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.5)",
            borderwidth=1,
            borderpad=2,
        )

    # Customize layout
    fig.update_layout(
        legend={"title": "Player"},
        height=600,
        width=1000,
    )

    # Add quadrant labels
    fig.add_annotation(
        x=df["avg_buy_in"].max() * 0.75,
        y=df["avg_net_profit"].max() * 0.75,
        text="High Buy-In, High Profit",
        showarrow=False,
        font={"size": 10},
    )

    fig.add_annotation(
        x=df["avg_buy_in"].min() * 1.25,
        y=df["avg_net_profit"].max() * 0.75,
        text="Low Buy-In, High Profit",
        showarrow=False,
        font={"size": 10},
    )

    fig.add_annotation(
        x=df["avg_buy_in"].max() * 0.75,
        y=df["avg_net_profit"].min() * 0.75,
        text="High Buy-In, High Loss",
        showarrow=False,
        font={"size": 10},
    )

    fig.add_annotation(
        x=df["avg_buy_in"].min() * 1.25,
        y=df["avg_net_profit"].min() * 0.75,
        text="Low Buy-In, High Loss",
        showarrow=False,
        font={"size": 10},
    )

    # Save to buffer
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    buffer.seek(0)
    return buffer
