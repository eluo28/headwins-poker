PLAYER_MAPPING = {
    "Edwin": {
        "played_ids": ["9M0NBGM9an"],
    },
    "Larry": {"played_ids": ["vTnkzfSe3x"]},
    "Josh": {"played_ids": ["fmjgGR4d_8"]},
    "Allen": {
        "played_ids": ["O4o2WcWz3Z"],
    },
    "Jeff": {"played_ids": ["FMYFFNvVDL"]},
    "Mond": {"played_ids": ["VnzuRuUJp5"]},
    "Gob": {"played_ids": ["-HnKEXRxVA"]},
    "Nick": {"played_ids": ["23ejw2m6D-"]},
    "Dan": {"played_ids": ["ArJnWs8BqK"]},
}

PLAYER_ID_TO_NAME = {
    player_id: name
    for name, data in PLAYER_MAPPING.items()
    for player_id in data["played_ids"]
}
