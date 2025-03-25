import datetime

from pydantic import BaseModel

from src.dataingestion.schemas.board_action import BoardAction
from src.dataingestion.schemas.card import Card


class BoardMove(BaseModel):
    action: BoardAction
    cards: list[Card]
    timestamp: datetime.datetime
    order: int
    original_log_line: str  # Store the original log entry for reference
