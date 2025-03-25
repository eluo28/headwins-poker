from enum import StrEnum, auto


class BoardState(StrEnum):
    PREFLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()