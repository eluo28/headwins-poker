import json
from logging import getLogger

import boto3
from botocore.exceptions import ClientError

logger = getLogger(__name__)


class SecretsManagerService:
    def __init__(self) -> None:
        region_name = "us-east-1"
        session = boto3.Session()
        self.client = session.client(service_name="secretsmanager", region_name=region_name)

    def get_secret(self, secret_name: str) -> str:
        try:
            get_secret_value_response = self.client.get_secret_value(SecretId=secret_name)
            secret_string = get_secret_value_response["SecretString"]
            # Parse the JSON string and get the token value
            secret_dict = json.loads(secret_string)
            return secret_dict["DISCORD_TOKEN"]
        except ClientError as e:
            raise e
