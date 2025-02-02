from decimal import Decimal
from typing import List

from src.parsing.player_mapping import PLAYER_MAPPING
from src.parsing.schemas.session import PokerSession


def get_player_net(sessions: List[PokerSession], player_id: str) -> Decimal:
    """
    Calculate the total net profit/loss for a specific player across all their sessions

    Args:
        sessions: List of PokerSession objects
        player_id: ID of the player to calculate net for

    Returns:
        Decimal representing total net profit/loss in dollars
    """
    player_sessions = [s for s in sessions if s.player_id == player_id]
    return sum((session.net_dollars for session in player_sessions), Decimal("0"))


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
