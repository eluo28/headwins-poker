import json
from typing import Any


def command_handler(body: dict[str, Any]) -> dict[str, Any]:
    command = body["data"]["name"]

    if command == "bleb":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "type": 4,
                    "data": {
                        "content": "Hello, World.",
                    },
                }
            ),
        }
    else:
        return {"statusCode": 400, "body": json.dumps("unhandled command")}
