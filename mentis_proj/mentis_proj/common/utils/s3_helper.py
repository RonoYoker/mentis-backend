import boto3
import logging

logger = logging.getLogger("app")


class S3Helper:
    def __init__(self):
        self.client = None
        self.get_s3_client()

    def get_s3_client(self):
        if self.client is None:
            self.client = boto3.resource('s3', region_name="ap-south-1")

    def upload_file_for_url_redirect(self, short_uuid, long_url, bucket_name):
        """
        Method to upload short url redirect object to AWS short URL bucket
        """
        method_name = "upload_file_for_url_redirect"
        bucket = self.client.Bucket(bucket_name)
        try:
            bucket.put_object(Bucket=bucket_name,
                              Key=short_uuid,
                              WebsiteRedirectLocation=long_url
                              )
        except Exception as ex:
            logger.error(f"method_name :: {method_name}, Error while uploading short url mapping to S3, ex {ex}")
            raise ex
