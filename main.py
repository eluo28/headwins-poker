import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import List

from src.analytics.analytics_helpers import get_all_player_nets
from src.parsing.schemas.session import PokerSession
from src.parsing.session_loading_helpers import load_sessions, load_starting_data

if __name__ == "__main__":
    all_sessions: List[PokerSession] = []
    # Read all CSV files from the ledgers folder
    ledgers_dir = "pokernow_data/ledgers"
    for filename in os.listdir(ledgers_dir):
        if filename.endswith(".csv"):
            filepath = os.path.join(ledgers_dir, filename)
            sessions = load_sessions(Path(filepath))
            all_sessions.extend(sessions)

    player_nets = get_all_player_nets(all_sessions)
    starting_data = load_starting_data("pokernow_data/starting_data.csv")

    for player in starting_data:
        if player not in player_nets:
            player_nets[player] = Decimal("0")

    for player in player_nets:
        if player in starting_data:
            player_nets[player] += starting_data[player]

    for player, net in player_nets.items():
        direction = "DOWN" if net < 0 else "UP"
        print(f"{player}: ${abs(net):,.2f} {direction}")
        sys.stdout.flush()
