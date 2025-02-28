from pydantic import BaseModel


class PlayerMappingDetails(BaseModel):
    player_name_lowercase: str
    player_ids: list[str]
    player_nicknames_lowercase: list[str]
