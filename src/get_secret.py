import json

from boto3 import Session
from botocore.exceptions import ClientError


def get_secret(secret_name: str) -> str:
    region_name = "us-east-1"

    session = Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret_string = get_secret_value_response["SecretString"]
        # Parse the JSON string and get the token value
        secret_dict = json.loads(secret_string)
        return secret_dict["DISCORD_TOKEN"]
    except ClientError as e:
        raise e
