from enum import StrEnum


class BoardAction(StrEnum):
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SECOND_FLOP = "second flop"
    SECOND_TURN = "second turn"
    SECOND_RIVER = "second river"
