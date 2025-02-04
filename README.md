# headwins-poker

Analytics for Headwins Poker.

After a session, please add logs to the `pokernowdata/ledgers` folder.

If someone uses a new id, please add them to the `src/parsing/player_mapping.py` file.

## Development

```bash
poetry install  # Install dependencies
poetry run python -m src.discordbot.run_bot  # Run the bot
```

## CLI

```bash
./hcli fixall  # Format and fix linting errors
```

