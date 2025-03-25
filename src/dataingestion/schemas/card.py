from pydantic import BaseModel

from src.dataingestion.schemas.card_rank import CardRank
from src.dataingestion.schemas.card_suit import CardSuit


class Card(BaseModel):
    rank: CardRank
    suit: CardSuit
