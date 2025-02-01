# headwins-poker

Analytics for Headwins Poker.

After a session, please add logs to the `pokernow_data/ledgers` folder.

If someone uses a new id, please add them to the `src/player_mapping.py` file.

Currently to get net totals for each player, run the script, use `poetry run python main.py`.

## Development

```bash
poetry install  # Install dependencies
poetry run python main.py  # Run the script
```
