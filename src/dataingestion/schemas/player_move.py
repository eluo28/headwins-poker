import datetime
from decimal import Decimal

from pydantic import BaseModel

from src.dataingestion.schemas.card import Card
from src.dataingestion.schemas.player_action import PlayerAction


class PlayerMove(BaseModel):
    player_id: str
    player_nickname: str
    action: PlayerAction
    amount: Decimal | None = None  # For bets, calls, raises
    cards: list[Card] | None = None  # For shows
    timestamp: datetime.datetime
    order: int
    original_log_line: str  # Store the original log entry for reference
