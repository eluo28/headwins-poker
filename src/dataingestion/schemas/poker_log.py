from datetime import date

from pydantic import BaseModel

from src.dataingestion.schemas.poker_hand import PokerHand


class PokerLog(BaseModel):
    hands: list[PokerHand]
    date: date
    registered_player_to_ids: dict[str, list[str]]
