import csv
import re
from decimal import Decimal, InvalidOperation
from io import StringIO
from logging import getLogger
from typing import cast

from src.dataingestion.schemas.poker_log import PokerLog
from src.dataingestion.schemas.registered_player import RegisteredPlayer
from src.discordbot.services.s3_service import S3Service
from src.dataingestion.schemas.board_action import BoardAction
from src.dataingestion.schemas.board_move import BoardMove
from src.dataingestion.schemas.card import Card
from src.dataingestion.schemas.card_rank import CardRank
from src.dataingestion.schemas.card_suit import CardSuit
from src.dataingestion.schemas.poker_hand import PokerHand
from src.dataingestion.schemas.player_action import PlayerAction
from src.dataingestion.schemas.player_move import PlayerMove
from src.dataingestion.common_utils import parse_utc_datetime

logger = getLogger(__name__)

VALID_RANKS: set[str] = {rank.value for rank in CardRank}


def parse_cards(card_text: str) -> list[Card]:
    """Parse a string of cards into Card objects."""
    cards = []
    # Match patterns like "A♠" or "10♥"
    card_pattern = r'(\d{1,2}|[JQKA])([♠♥♦♣])'
    matches = re.finditer(card_pattern, card_text)
    
    for match in matches:
        rank, suit_symbol = match.groups()
        # Validate rank is one of the allowed values
        if rank not in VALID_RANKS:
            raise ValueError(f"Invalid card rank found: {rank}")
        suit = CardSuit(suit_symbol)
        cards.append(Card(rank=cast(CardRank, rank), suit=suit))
    
    return cards


def parse_player_info(text: str) -> tuple[str, str]:
    """Parse player nickname and ID from text like 'edwin @ 9M0NBGM9an' or '"edwin @ 9M0NBGM9an"'."""
    # Remove any surrounding quotes
    text = text.strip('"')
    # Split on @ and strip whitespace
    parts = text.split('@')
    if len(parts) != 2:
        raise ValueError(f"Could not parse player info from: {text}")
    nickname = parts[0].strip()
    player_id = parts[1].strip()
    return nickname, player_id

def get_registered_player_nickname_from_session_nickname_or_id(session_nickname: str, session_id: str, registered_players: list[RegisteredPlayer]) -> str:
    """Get the registered player nickname from the session nickname."""
    for player in registered_players:
        if session_nickname.lower() in player.player_nicknames_lowercase:
            return player.player_name_lowercase
        if session_id in player.player_ids:
            return player.player_name_lowercase
    return session_nickname

def parse_amount(text: str) -> Decimal:
    """Parse amount from text, handling various formats."""
    # Check for blind posts and similar actions with 'of' before the amount
    if "of " in text:
        match = re.search(r'of (\d+\.?\d*)', text)
        if match:
            return Decimal(match.group(1))
    
    # Check for 'raises to' pattern
    if "raises to " in text:
        match = re.search(r'raises to (\d+\.?\d*)', text)
        if match:
            return Decimal(match.group(1))
    
    # Check for 'collected' pattern
    if "collected " in text:
        match = re.search(r'collected (\d+\.?\d*)', text)
        if match:
            return Decimal(match.group(1))
    
    # Check for 'calls' pattern
    if "calls " in text:
        match = re.search(r'calls (\d+\.?\d*)', text)
        if match:
            return Decimal(match.group(1))
            
    # Check for 'bets' pattern
    if "bets " in text:
        match = re.search(r'bets (\d+\.?\d*)', text)
        if match:
            return Decimal(match.group(1))
    
    # Check for general monetary amount (for other cases)
    # Look for amount at the end of the action
    match = re.search(r'[a-z] (\d+\.?\d*)"?,?$', text.lower())
    if not match:
        raise ValueError(f"Could not parse amount from: {text}")
    
    return Decimal(match.group(1))


def parse_starting_stacks(stack_text: str) -> dict[str, Decimal]:
    """Parse the starting stacks from a stack entry line.
    Example format: 'Player stacks: #1 "Nicky @ 23ejw2m6D-" (27.25) | #3 "glenny @ O4o2WcWz3Z" (17.40)'
    """
    if not stack_text.startswith("Player stacks:"):
        logger.warning(f"Stack entry does not start with 'Player stacks:': {stack_text}")
        return {}
    
    stack_text = stack_text[len("Player stacks: "):]
    player_entries = stack_text.split(" | ")
    stacks = {}
    
    for entry in player_entries:
        match = re.match(r'#\d+ "([^"]+) @ ([^"]+)" \((\d+\.?\d*)\)', entry.strip())
        if match:
            _, player_id, amount = match.groups()
            try:
                stacks[player_id] = Decimal(amount)
            except (ValueError, InvalidOperation):
                raise ValueError(f"Could not parse stack amount from entry: {entry}")
        else:
            raise ValueError(f"Could not parse stack entry: {entry}")
    
    return stacks


def parse_hand_id(text: str) -> str:
    """Parse hand ID from the starting hand text."""
    pattern = r'\(id: ([^)]+)\)'
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"Could not parse hand ID from: {text}")
    return match.group(1)

def parse_poker_hand(entries: list[dict[str, str]], registered_players: list[RegisteredPlayer]) -> PokerHand:
    """Parse a list of log entries into a PokerHand object."""
    # Find the start and end of the hand
    start_idx = None
    end_idx = None
    hand_id = None
    
    for i, entry in enumerate(entries):
        text = entry["entry"]
        if text.startswith("-- starting hand #"):
            start_idx = i
            # Extract hand ID from format: -- starting hand #179 (id: bzhgiiupyhku)
            match = re.search(r'#\d+ \(id: ([^)]+)\)', text)
            if match:
                hand_id = match.group(1)
        elif text.startswith("-- ending hand #"):
            end_idx = i
            break

    if start_idx is None or hand_id is None:
        raise ValueError("Could not find start of hand or hand ID")

    if end_idx is None:
        raise ValueError(f"Could not find end of hand {hand_id} - hand appears incomplete")
    
    # Find the stack entry (should be right after the start of the hand)
    stack_entry = None
    for i in range(start_idx, min(start_idx + 5, len(entries))):
        if entries[i]["entry"].startswith("Player stacks:"):
            stack_entry = entries[i]["entry"]
            break
    
    if not stack_entry:
        raise ValueError("No starting stacks found in hand entries")
    
    starting_stacks = parse_starting_stacks(stack_entry)
    if not starting_stacks:
        raise ValueError("Could not parse any starting stacks")
    
    # Process the hand entries
    hand_entries = entries[start_idx:end_idx]
    
    # Initialize tracking variables
    actions_in_chronological_order: list[PlayerMove | BoardMove] = []
    community_cards = []
    net_amounts_collected_by_player_id = {}
    player_registered_nicknames_to_id = {}
    # Process each entry
    for entry in hand_entries:
        text = entry["entry"]
        timestamp = parse_utc_datetime(entry["at"])
        order = int(entry["order"])
            
        # Parse community cards
        if "Flop:" in text or "Flop (second run):" in text:
            community_cards = parse_cards(text)  # Reset and set flop cards
            actions_in_chronological_order.append(BoardMove(
                action=BoardAction.FLOP if "second run" not in text else BoardAction.SECOND_FLOP,
                cards=community_cards,
                timestamp=timestamp,
                order=order,
                original_log_line=text
            ))
        elif "Turn:" in text or "Turn (second run):" in text:
            community_cards = parse_cards(text)
            actions_in_chronological_order.append(BoardMove(
                action=BoardAction.TURN if "second run" not in text else BoardAction.SECOND_TURN,
                cards=[community_cards[-1]],  # Just the turn card
                timestamp=timestamp,
                order=order,
                original_log_line=text
            ))
        elif "River:" in text or "River (second run):" in text:
            community_cards = parse_cards(text)
            actions_in_chronological_order.append(BoardMove(
                action=BoardAction.RIVER if "second run" not in text else BoardAction.SECOND_RIVER,
                cards=[community_cards[-1]],  # Just the river card
                timestamp=timestamp,
                order=order,
                original_log_line=text
            ))
            continue
        
        # Parse player actions
        for action in PlayerAction:
            if action.value in text:
                # Extract player info - now handles text with or without quotes
                if '"' in text:
                    parts = text.split('"')
                    if len(parts) < 2:
                        raise ValueError(f"Unexpected format in player text: {text}")
                    player_text = parts[1]
                else:
                    player_text = text
                
                nickname, player_id = parse_player_info(player_text)
                player_registered_nickname = get_registered_player_nickname_from_session_nickname_or_id(nickname, player_id, registered_players)
                player_registered_nicknames_to_id[player_registered_nickname] = player_id


                # Create player move
                move = PlayerMove(
                    player_id=player_id,
                    player_nickname=nickname,
                    action=action,
                    timestamp=timestamp,
                    order=order,
                    original_log_line=text
                )
                
                # Add amount for betting actions
                if action in [PlayerAction.BET, PlayerAction.CALL, PlayerAction.RAISE, PlayerAction.POST]:
                    move.amount = parse_amount(text)
                
                # Add shown cards
                elif action == PlayerAction.SHOW:
                    move.cards = parse_cards(text)
                
                # Track collected amounts
                elif action == PlayerAction.COLLECT:
                    amount = parse_amount(text)
                    net_amounts_collected_by_player_id[player_id] = amount
                
                actions_in_chronological_order.append(move)
                break
    
    # Calculate pot size (sum of all bets minus returned uncalled bets)
    pot_size = Decimal('0')
    for move in actions_in_chronological_order:
        if isinstance(move, PlayerMove) and move.amount and move.action in [PlayerAction.BET, PlayerAction.CALL, PlayerAction.RAISE]:
            pot_size += move.amount
        elif isinstance(move, PlayerMove) and move.action == PlayerAction.UNCALLED_BET_RETURN and move.amount:
            pot_size -= move.amount
    
    if not actions_in_chronological_order:
        raise ValueError("No actions found in hand")
    
    # Create and return the PokerHand object
    return PokerHand(
        hand_id=hand_id,
        start_time=parse_utc_datetime(hand_entries[0]["at"]),
        end_time=parse_utc_datetime(hand_entries[-1]["at"]),
        starting_stacks=starting_stacks,
        pot_size=pot_size,
        community_cards=community_cards,
        actions_in_chronological_order=actions_in_chronological_order,
        net_amounts_collected_by_player_id=net_amounts_collected_by_player_id,
        player_registered_nicknames_to_id=player_registered_nicknames_to_id
    )


def is_admin_log(entry: str) -> bool:
    """Check if the log entry is an administrative message that should be ignored."""
    admin_patterns = [
        "requested a seat",
        "approved the player",
        "stand up with the stack",
        "sit back with the stack",
        "joined the game",
        "quits the game",
        "stand up to leave",
        "sit back at the table"
    ]
    return any(pattern in entry for pattern in admin_patterns)


def parse_poker_log(log_file: StringIO, registered_players: list[RegisteredPlayer]) -> PokerLog:
    """
    Parse a poker log file into a list of PokerHand objects.
    
    Args:
        log_file: StringIO object containing the poker log CSV data
        
    Returns:
        List of PokerHand objects
    """
    hands = []
    current_hand_entries = []
    
    # Read CSV in reverse order since the log is in reverse chronological order
    rows = list(csv.DictReader(log_file))[::-1]
    
    for row in rows:
        # Skip administrative logs
        if is_admin_log(row["entry"]):
            continue
            
        if "starting hand" in row["entry"]:
            # Start collecting entries for a new hand
            current_hand_entries = [row]
        elif current_hand_entries:
            # Add entry to current hand
            current_hand_entries.append(row)
            if "ending hand" in row["entry"]:
                # Parse completed hand
                hand = parse_poker_hand(current_hand_entries, registered_players)
                hands.append(hand)
                current_hand_entries = []

    date = parse_utc_datetime(rows[0]["at"]).date()
    registered_player_to_ids = build_nickname_to_player_ids_mapping(hands)
    
    return PokerLog(hands=hands, date=date, registered_player_to_ids=registered_player_to_ids)


def build_nickname_to_player_ids_mapping(hands: list[PokerHand]) -> dict[str, list[str]]:
    """
    Build a mapping of registered nicknames to all player IDs used by that player across all hands.
    
    Args:
        hands: List of poker hands to analyze
        
    Returns:
        Dictionary mapping registered nicknames to lists of player IDs
    """
    nickname_to_ids = {}
    for hand in hands:
        for nickname, player_id in hand.player_registered_nicknames_to_id.items():
            if nickname not in nickname_to_ids:
                nickname_to_ids[nickname] = []
            if player_id not in nickname_to_ids[nickname]:
                nickname_to_ids[nickname].append(player_id)
    return nickname_to_ids
        

async def get_poker_log_file_contents(
    guild_id: str,
    s3_service: S3Service,
) -> list[tuple[StringIO, str]]:
    """
    Gets contents of poker log CSV files from S3 for a guild.

    Args:
        guild_id: Discord guild ID to get files for

    Returns:
        List of csv file contents for each poker log CSV file
    """
    csv_files_content_and_names: list[tuple[StringIO, str]] = []
    try:
        file_names, _ = await s3_service.list_files(guild_id, "logs") 
        for file_name in file_names:
            if file_name.endswith(".csv"):
                # Get the object from S3
                success, file_content = await s3_service.get_file(guild_id, file_name, "logs")
                if not success:
                    raise Exception(file_content)
                # Create a StringIO object
                csv_file = StringIO(file_content)
                csv_files_content_and_names.append((csv_file, file_name))
    except Exception as e:
        logger.error(f"Error accessing S3: {e}")
        raise

    return csv_files_content_and_names


async def load_all_poker_logs(guild_id: str, s3_service: S3Service, registered_players: list[RegisteredPlayer]) -> list[PokerLog]:
    """
    Loads and combines all poker hands from CSV files in S3.

    Args:
        guild_id: Discord guild ID to load hands for

    Returns:
        list of all poker hands combined
    """
    all_logs: list[PokerLog] = []
    csv_files_with_names = await get_poker_log_file_contents(guild_id, s3_service)

    for csv_file, file_name in csv_files_with_names:
        try:
            log = parse_poker_log(csv_file, registered_players)
            all_logs.append(log)
        except Exception as e:
            logger.error(f"Error parsing poker log {file_name}: {e}")

    return all_logs

