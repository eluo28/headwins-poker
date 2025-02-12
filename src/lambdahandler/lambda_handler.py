import json
import os
from typing import Any

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from src.lambdahandler.command_handler import command_handler

PUBLIC_KEY = os.environ["PUBLIC_KEY"]


def lambda_handler(event: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    try:
        body = json.loads(event["body"])

        signature = event["headers"]["x-signature-ed25519"]
        timestamp = event["headers"]["x-signature-timestamp"]

        verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
        message = timestamp + event["body"]

        try:
            verify_key.verify(message.encode(), signature=bytes.fromhex(signature))
        except BadSignatureError:
            return {"statusCode": 401, "body": json.dumps("invalid request signature")}

        # handle the interaction

        t = body["type"]

        if t == 1:
            return {"statusCode": 200, "body": json.dumps({"type": 1})}
        elif t == 2:
            return command_handler(body)
        else:
            return {"statusCode": 400, "body": json.dumps("unhandled request type")}
    except:
        raise
