from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class StartingDataEntry(BaseModel):
    player_name: str
    net_dollars: Decimal
    date: date
