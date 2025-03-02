from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PlayerSessionLog(BaseModel):
    player_nickname_lowercase: str
    player_id: str
    session_start_at: datetime
    session_end_at: datetime  # assumes that the end time is the latest end time in the file if no end time is provided
    buy_in_dollars: Decimal
    buy_out_dollars: Decimal | None = None
    stack_dollars: Decimal
    net_dollars: Decimal
