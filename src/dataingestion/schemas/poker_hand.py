from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field

from src.dataingestion.schemas.board_move import BoardMove
from src.dataingestion.schemas.card import Card
from src.dataingestion.schemas.player_move import PlayerMove


class PokerHand(BaseModel):
    hand_id: str
    start_time: datetime
    end_time: datetime
    starting_stacks: dict[str, Decimal] 
    pot_size: Decimal
    community_cards: list[Card] = Field(default_factory=list)
    actions_in_chronological_order: list[PlayerMove | BoardMove]
    net_amounts_collected_by_player_id: dict[str, Decimal]
    player_registered_nicknames_to_id: dict[str, str]