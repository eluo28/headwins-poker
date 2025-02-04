from decimal import Decimal
from typing import List

from src.parsing.player_mapping import PLAYER_MAPPING
from src.parsing.schemas.session import PokerSession


def get_all_player_nets(sessions: List[PokerSession]) -> dict[str, Decimal]:
    player_nets: dict[str, Decimal] = {}  # Player name -> net

    # Initialize nets for all players
    for player_name in PLAYER_MAPPING:
        player_nets[player_name] = Decimal("0")

    for session in sessions:
        # Find which player this session belongs to by checking IDs
        for player_name, player_data in PLAYER_MAPPING.items():
            if session.player_id in player_data["played_ids"]:
                player_nets[player_name] += session.net_dollars
                break

    return player_nets
