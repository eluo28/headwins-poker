from io import BytesIO
from typing import List

import matplotlib.pyplot as plt
import pandas as pd

from src.parsing.schemas.session import PokerSession
from src.parsing.schemas.starting_data_entry import StartingDataEntry


def get_file_object_of_player_nets_over_time(
    sessions: List[PokerSession], starting_data: List[StartingDataEntry]
) -> BytesIO:
    # Convert sessions to DataFrame
    df = pd.DataFrame(
        [
            {
                "player": session.player_nickname,
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
                "player": entry.player_name,
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

    # Create plot
    plt.figure(figsize=(12, 8))
    for player in player_nets.columns:
        plt.plot(player_nets.index, player_nets[player], label=player, marker="o")

    min_date = min(entry.date for entry in starting_data)
    plt.xlim(left=min_date)

    plt.title("Player Net Profits/Losses Over Time")
    plt.xlabel("Date")
    plt.ylabel("Net Profit/Loss ($)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True)

    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    plt.close()

    # Reset buffer position to start
    buffer.seek(0)
    return buffer
