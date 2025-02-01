from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class PokerSession(BaseModel):
    player_nickname: str
    player_id: str
    session_start_at: datetime
    session_end_at: Optional[datetime] = None
    buy_in_dollars: Decimal
    buy_out_dollars: Optional[Decimal] = None
    stack_dollars: Decimal
    net_dollars: Decimal
