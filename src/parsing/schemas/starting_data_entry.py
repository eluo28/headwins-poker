from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class StartingDataEntry(BaseModel):
    player_name_lowercase: str
    net_dollars: Decimal
    date: date
