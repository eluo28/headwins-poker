from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PokerSession(BaseModel):
    player_nickname: str
    player_id: str
    session_start_at: datetime | None = None
    session_end_at: datetime | None = None
    buy_in_dollars: Decimal
    buy_out_dollars: Decimal | None = None
    stack_dollars: Decimal
    net_dollars: Decimal
