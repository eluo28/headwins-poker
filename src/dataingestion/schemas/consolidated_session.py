from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ConsolidatedPlayerSession(BaseModel):
    player_nickname_lowercase: str
    net_dollars: Decimal
    date: date
