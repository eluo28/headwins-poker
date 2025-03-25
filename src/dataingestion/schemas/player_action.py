from enum import StrEnum


class PlayerAction(StrEnum):
    FOLD = "folds"
    CHECK = "checks"
    CALL = "calls"
    BET = "bets"
    RAISE = "raises"
    SHOW = "shows"
    COLLECT = "collected"
    UNCALLED_BET_RETURN = "uncalled bet returned"
    POST = "posts" 