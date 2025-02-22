PLAYER_MAPPING = {
    "Edwin": {
        "played_ids": ["9M0NBGM9an"],
        "played_nicknames": ["edwin"],
    },
    "Larry": {
        "played_ids": ["vTnkzfSe3x, f2FO7_98Oo"],
        "played_nicknames": ["larry"],
    },
    "Josh": {"played_ids": ["Z_WOxDxS2G"], "played_nicknames": ["joshy"]},
    "Allen": {
        "played_ids": ["O4o2WcWz3Z"],
        "played_nicknames": ["glenny"],
    },
    "Jeff": {"played_ids": ["FMYFFNvVDL"], "played_nicknames": []},
    "Mond": {"played_ids": ["VnzuRuUJp5"], "played_nicknames": []},
    "Gob": {"played_ids": ["-HnKEXRxVA"], "played_nicknames": []},
    "Nick": {"played_ids": ["23ejw2m6D-"], "played_nicknames": []},
    "Dan": {"played_ids": ["ArJnWs8BqK"], "played_nicknames": ["the senate"]},
    "Addison": {"played_ids": ["YRv7Vh3JH0"], "played_nicknames": []},
    "Chris": {"played_ids": [], "played_nicknames": ["kris", "CF"]},
    "Eli": {"played_ids": [], "played_nicknames": ["Egan", "egan konopinsk"]},
}

PLAYER_ID_TO_LOWERCASE_NAME = {
    player_id.strip(): name.lower()
    for name, data in PLAYER_MAPPING.items()
    for played_id in data["played_ids"]
    for player_id in played_id.split(",")
}
PLAYER_NICKNAME_TO_LOWERCASE_NAME = {
    nickname.lower().strip(): name.lower()
    for name, data in PLAYER_MAPPING.items()
    for played_nickname in data["played_nicknames"]
    for nickname in played_nickname.split(",")
}
