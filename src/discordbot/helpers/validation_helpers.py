import re
from logging import getLogger

import discord

logger = getLogger(__name__)

STARTING_DATA_COLUMNS = 3


async def validate_starting_data_file(file: discord.Attachment) -> str | None:
    """Validate the starting data CSV file format."""
    if not file.filename.endswith(".csv"):
        return "Please upload a CSV file"

    content = await file.read()
    text = content.decode("utf-8")
    lines = text.strip().split("\n")

    # Check each line format
    for i, line in enumerate(lines):
        parts = line.strip().split(",")
        if len(parts) != STARTING_DATA_COLUMNS:
            return f"Line {i + 1} should have exactly {STARTING_DATA_COLUMNS} columns: player_name,net_amount,date"

        try:
            # Validate net amount is a number
            float(parts[1])
        except ValueError:
            return f"Invalid net amount on line {i + 1}: {parts[1]}"

        try:
            # Validate date format (YYYY-MM-DD)
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", parts[2].strip()):
                raise ValueError
        except ValueError:
            return f"Invalid date format on line {i + 1}. Expected YYYY-MM-DD"

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


async def validate_csv_files(ledger_file: discord.Attachment, log_file: discord.Attachment) -> str | None:
    ledger_validation = await validate_ledger_file(ledger_file)
    if ledger_validation:
        return ledger_validation

    log_validation = await validate_log_file(log_file)
    if log_validation:
        return log_validation

    return None
