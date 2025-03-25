from typing import Dict, List, Set, Mapping, Collection, Sequence

from src.dataingestion.schemas.poker_log import PokerLog
from src.dataingestion.schemas.poker_hand import PokerHand
from src.dataingestion.schemas.player_move import PlayerMove
from src.dataingestion.schemas.player_action import PlayerAction


def _calculate_vpip_stats(hands: Sequence[PokerHand], player_mapping: Mapping[str, Collection[str]]) -> tuple[dict[str, float], dict[str, int], dict[str, int]]:
    """
    Helper function to calculate VPIP statistics for a set of hands.
    
    Args:
        hands: List of poker hands to analyze
        player_mapping: Dictionary mapping player nicknames to their IDs
        
    Returns:
        Tuple of (vpip percentages, total hands, vpip hands) dictionaries
    """
    # Track hands played and vpip hands for each player
    total_hands: Dict[str, int] = {}  # player_id -> total hands played
    vpip_hands: Dict[str, int] = {}   # player_id -> hands where player put money in voluntarily
    
    for hand in hands:
        # Get all players in the hand
        player_ids_in_hand = set(hand.player_registered_nicknames_to_id.values())
        
        # Update total hands for each player
        for player_id in player_ids_in_hand:
            total_hands[player_id] = total_hands.get(player_id, 0) + 1
            
        # Track if each player has VPIPed this hand
        has_vpiped = set()
        
        # Look at preflop actions
        for action in hand.actions_in_chronological_order:
            # Stop when we hit the flop
            if not hasattr(action, 'player_nickname'):
                break
                
            # Skip blind posts since they're not voluntary
            if action.action == PlayerAction.POST:
                continue
                
            # Any bet/call/raise preflop counts as VPIP
            if isinstance(action, PlayerMove) and action.action in [PlayerAction.BET, PlayerAction.CALL, PlayerAction.RAISE]:
                has_vpiped.add(action.player_id)
                
        # Update VPIP counts
        for player_id in has_vpiped:
            vpip_hands[player_id] = vpip_hands.get(player_id, 0) + 1

    # Sum up stats for each registered nickname
    nickname_total_hands = {}
    nickname_vpip_hands = {}
    for nickname, player_ids in player_mapping.items():
        nickname_total_hands[nickname] = sum(total_hands.get(pid, 0) for pid in player_ids)
        nickname_vpip_hands[nickname] = sum(vpip_hands.get(pid, 0) for pid in player_ids)
    
    # Calculate percentages by nickname
    vpip_percentages = {}
    for nickname in nickname_total_hands:
        if nickname_total_hands[nickname] > 0:
            vpip_pct = (nickname_vpip_hands[nickname] / nickname_total_hands[nickname]) * 100
            vpip_percentages[nickname] = round(vpip_pct, 1)
            
    return vpip_percentages, nickname_total_hands, nickname_vpip_hands


def calculate_vpip_by_player_across_all_logs(logs: List[PokerLog]) -> dict[str, float]:
    """
    Calculate VPIP (Voluntarily Put Money In Pot) percentage for each player across all logs.
    
    Args:
        logs: List of poker log objects to analyze
        
    Returns:
        Dictionary mapping player nicknames to their VPIP percentage
    """
    # Build combined mapping of nicknames to player IDs across all logs
    all_registered_player_to_ids: Dict[str, Set[str]] = {}
    for log in logs:
        for nickname, player_ids in log.registered_player_to_ids.items():
            if nickname not in all_registered_player_to_ids:
                all_registered_player_to_ids[nickname] = set()
            all_registered_player_to_ids[nickname].update(player_ids)
    
    # Combine all hands from all logs
    all_hands = [hand for log in logs for hand in log.hands]
    
    # Calculate VPIP stats using the helper function
    vpip_percentages, _, _ = _calculate_vpip_stats(all_hands, all_registered_player_to_ids)
    return vpip_percentages


def calculate_vpip_by_player(log: PokerLog) -> dict[str, float]:
    """
    Calculate VPIP (Voluntarily Put Money In Pot) percentage for each player.
    VPIP is the percentage of hands where a player voluntarily puts money in the pot preflop.
    
    Args:
        log: Poker log object to analyze
        
    Returns:
        Dictionary mapping player nicknames to their VPIP percentage
    """
    # Calculate VPIP stats using the helper function
    vpip_percentages, _, _ = _calculate_vpip_stats(log.hands, log.registered_player_to_ids)
    return vpip_percentages
