import json
import re
from logging import getLogger

import discord

logger = getLogger(__name__)


async def validate_registered_players_file(file: discord.Attachment) -> str | None:
    """Validate the registered players JSON file format."""
    if not file.filename.endswith(".json"):
        return "Please upload a JSON file"

    if file.filename != "registered_players.json":
        return "File must be named 'registered_players.json'"

    content = await file.read()
    text = content.decode("utf-8")

    try:
        data = json.loads(text)

        # Validate overall structure is a dict
        if not isinstance(data, dict):
            return "File must contain a JSON object"

        # Validate each player entry
        for player_name, player_data in data.items():
            # Check required fields exist
            if not isinstance(player_data, dict):
                return f"Invalid data format for player {player_name}"

            if "played_ids" not in player_data or not isinstance(player_data["played_ids"], list):
                return f"Missing or invalid played_ids for player {player_name}"

            if "played_nicknames" not in player_data or not isinstance(player_data["played_nicknames"], list):
                return f"Missing or invalid played_nicknames for player {player_name}"

            # Validate initial_details if present
            if "initial_details" in player_data:
                initial_details = player_data["initial_details"]
                if not isinstance(initial_details, dict):
                    return f"Invalid initial_details format for player {player_name}"

                if "initial_net_amount" not in initial_details:
                    return f"Missing initial_net_amount in initial_details for player {player_name}"

                if "initial_date" not in initial_details:
                    return f"Missing initial_date in initial_details for player {player_name}"

                try:
                    float(initial_details["initial_net_amount"])
                except (ValueError, TypeError):
                    return f"Invalid initial_net_amount for player {player_name}"

                if not re.match(r"^\d{4}-\d{2}-\d{2}$", initial_details["initial_date"]):
                    return f"Invalid initial_date format for player {player_name}. Expected YYYY-MM-DD"

    except json.JSONDecodeError:
        return "Invalid JSON format"
    except Exception as e:
        logger.error(f"Error validating registered players file: {e}")
        return "Error validating file format"

    return None


async def validate_ledger_file(ledger_file: discord.Attachment) -> str | None:
    if not ledger_file.filename.endswith(".csv") or not ledger_file.filename.startswith("ledger"):
        return "Please upload a ledger CSV file starting with 'ledger'"

    ledger_content = await ledger_file.read()
    ledger_text = ledger_content.decode("utf-8")
    first_line = ledger_text.split("\n")[0].strip()
    expected_headers = "player_nickname,player_id,session_start_at,session_end_at,buy_in,buy_out,stack,net"

    if first_line != expected_headers:
        return (
            "Ledger CSV file must have the following headers: "
            "player_nickname,player_id,session_start_at,session_end_at,buy_in,buy_out,stack,net"
        )

    return None


async def validate_log_file(log_file: discord.Attachment) -> str | None:
    if not log_file.filename.endswith(".csv") or not log_file.filename.startswith("poker_now_log"):
        return "Please upload a log CSV file starting with 'poker_now_log'"

    log_content = await log_file.read()
    log_text = log_content.decode("utf-8")
    log_first_line = log_text.split("\n")[0].strip()
    expected_log_headers = "entry,at,order"

    if log_first_line != expected_log_headers:
        return "Log CSV file must have the following headers: entry,at,order"

    return None


async def validate_ledger_and_log_files(ledger_file: discord.Attachment, log_file: discord.Attachment) -> str | None:
    ledger_validation = await validate_ledger_file(ledger_file)
    if ledger_validation:
        return ledger_validation

    log_validation = await validate_log_file(log_file)
    if log_validation:
        return log_validation

    return None
