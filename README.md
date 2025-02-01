# headwins-poker

Analytics for Headwins Poker.

After a session, please add logs to the `pokernow_data/ledgers` folder.

If someone uses a new id, please add them to the `src/player_mapping.py` file.

Currently to get net totals for each player, run the script, use `poetry run python main.py`.

To run the bot, first use `npm install` to install dependencies.
Next, use `node deploy.js` to deploy the commands to the server.
Finally, use `node index.js` to run the bot.
Additionally, will need .env file with DISCORD_TOKEN, CLIENT_ID, and GUILD_ID.

## Development

```bash
poetry install  # Install dependencies
poetry run python main.py  # Run the script
```
