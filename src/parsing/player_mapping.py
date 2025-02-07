PLAYER_MAPPING = {
    "Edwin": {
        "played_ids": ["9M0NBGM9an"],
    },
    "Larry": {"played_ids": ["vTnkzfSe3x, f2FO7_98Oo"]},
    "Josh": {"played_ids": ["Z_WOxDxS2G"]},
    "Allen": {
        "played_ids": ["O4o2WcWz3Z"],
    },
    "Jeff": {"played_ids": ["FMYFFNvVDL"]},
    "Mond": {"played_ids": ["VnzuRuUJp5"]},
    "Gob": {"played_ids": ["-HnKEXRxVA"]},
    "Nick": {"played_ids": ["23ejw2m6D-"]},
    "Dan": {"played_ids": ["ArJnWs8BqK"]},
    "Addison": {"played_ids": ["YRv7Vh3JH0"]},
}

PLAYER_ID_TO_NAME = {
    player_id.strip(): name
    for name, data in PLAYER_MAPPING.items()
    for played_id in data["played_ids"]
    for player_id in played_id.split(",")
}
