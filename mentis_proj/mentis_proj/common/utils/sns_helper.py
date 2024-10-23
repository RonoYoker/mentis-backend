import logging
import json
import boto3
import settings

logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)


class SnsHelper:
    def __init__(self, **kwargs):
        self.client = self.sns_client()

    def sns_client(self):
        return boto3.client('sns', region_name='ap-south-1')

    def publish_data_to_topic(self, topic, data):
        try:
            self.client.publish(
                TopicArn=self.get_sns_arn(topic),
                Message=json.dumps(data),
                MessageStructure='json')
        except Exception as e:
            logger.error(f"Error while pushing in SNS ex::{str(e)} data::{data} topic_arn::{self.get_sns_arn(topic)}")
            return False
        return True

    def get_sns_arn(self, sns_queue):
        return f"arn:aws:sns:{settings.AWS_REGION}:{settings.AWS_ACCOUNTID}:{sns_queue}"
