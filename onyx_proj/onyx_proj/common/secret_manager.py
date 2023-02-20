import logging

import boto3
from botocore.exceptions import ClientError
import json

logger = logging.getLogger("app")


def fetch_secrets_from_secret_manager(secret_name, region_name):
    # Create a Secrets Manager client
    print(f"fetch_secrets_from_secret_manager :: secret_name: {secret_name}, region_name: {region_name}")
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            # For a list of exceptions thrown, see
            # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
            logger.error(f"Error while loading secrets data. Error: {str(e)}.")
            raise e

        # Decrypts secret using the associated KMS key.
        bank_config = json.loads(get_secret_value_response['SecretString'])
        print(f"fetch_secrets_from_secret_manager :: bank_config: {bank_config}")
        return bank_config
    except Exception as e:
        print(f"fetch_secrets_from_secret_manager :: Exception: {e}")