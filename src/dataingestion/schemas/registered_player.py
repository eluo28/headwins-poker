from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class InitialDetails(BaseModel):
    initial_net_amount: Decimal 
    initial_date: date 


class RegisteredPlayer(BaseModel):
    player_name_lowercase: str
    player_ids: list[str]
    player_nicknames_lowercase: list[str]
    initial_details: InitialDetails | None
