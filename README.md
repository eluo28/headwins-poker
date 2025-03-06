# headwins-poker

Analytics for Poker Now data.

## Commands

### 📋 Registered Players

To consolidate your players' information (if the same player plays under different nicknames), or if you want to add initial details to a player's record, upload a JSON file named `registered_players.json` with your players' information using `/upload_registered_players`.

**Format Example:**
```json
{
    "PlayerName": {
        "played_ids": ["player_id_1", "player_id_2"],
        "played_nicknames": ["nickname1", "nickname2"],
        "initial_details": {
            "initial_net_amount": 100.50,
            "initial_date": "YYYY-MM-DD"
        }
    },
    "AnotherPlayer": {
        "played_ids": ["another_id"],
        "played_nicknames": ["another_nickname"],
        "initial_details": {
            "initial_net_amount": -50.25,
            "initial_date": "YYYY-MM-DD"
        }
    }
}
```

- `played_ids`: IDs from PokerNow that identify this player
- `played_nicknames`: Nicknames used by this player
- `initial_details`: Starting balance and date (optional)

### 📊 Ledger and Log Files

After each pokernow session, upload the CSV files using `/upload_ledger_and_log_csv`.

**Steps:**
1. At the end of your PokerNow game, download both the **Ledger CSV** and **Hand Log CSV**
2. Use the `/upload_ledger_and_log_csv` command and attach both files
3. The bot will process and store these files for analysis

These files contain all the information about your poker session, including player balances, hands played, and game actions.

### 📈 Analysis Commands

Once you've uploaded your data, use these commands to analyze your games:

- `/graph_all_player_nets` - View all players' net profits over time
- `/graph_played_time_totals` - See how much time each player has spent playing
- `/graph_profit_per_hour` - Analyze each player's profit per hour played
- `/graph_buy_in_analysis` - Analyze the relationship between buy-in amounts and final results

### 🗂️ File Management

You can manage your uploaded files with these commands. Note that only admins (users with a role named `headwins_admin`) can delete files:

- `/list_ledger_files` - View uploaded ledger files
- `/list_log_files` - View uploaded log files
- `/list_registered_players` - View uploaded registered players files
- `/get_registered_players` - Fetch your current registered players file
- `/delete_ledger_file` - Delete a specific ledger file by name (admin only)
- `/delete_log_file` - Delete a specific log file by name (admin only)
- `/delete_registered_players` - Delete the registered players file (admin only)

## Development

```bash
poetry install  # Install dependencies
poetry run python -m src.discordbot.run_bot  # Run the bot
```

## CLI

```bash
./hcli fixall  # Format and fix linting errors
```

