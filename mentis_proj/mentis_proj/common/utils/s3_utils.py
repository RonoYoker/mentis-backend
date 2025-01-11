import boto3
from django.conf import settings
import logging
logging.getLogger('boto3').setLevel(logging.DEBUG)
logging.getLogger('botocore').setLevel(logging.DEBUG)
logging.getLogger('s3transfer').setLevel(logging.DEBUG)
logging.getLogger('urllib3').setLevel(logging.DEBUG)

class S3Helper:
    def __init__(self, **kwargs):
        self.client = self.get_s3_connection()
        self.s3_client = boto3.client("s3")

    def get_s3_connection(self):
        return boto3.resource('s3', "ap-south-1")


    def get_file_from_s3_bucket(self, bucket_name: str, key: str, remote_path: str = None):
        """
        downloads file from s3 bucket using bucket name and file name
        """
        if remote_path:
            final_key = remote_path + key
        else:
            final_key = key
        bucket = self.client.Bucket(bucket_name)
        bucket.download_file(final_key, '/tmp/' + key)

    def check_file_existence(self,bucket_name, object_key):
        try:
            self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
            return True
        except Exception as e:
            return False

    def upload_file_to_s3_bucket(self, bucket_name: str, key: str):
        """
        downloads file from s3 bucket using bucket name and file name
        """
        bucket = self.client.Bucket(bucket_name)
        bucket.upload_file('/tmp/' + key, key)

    def generate_s3_url(self, key, bucket_name):
        return "https://%s.s3.%s.amazonaws.com/%s" % (bucket_name, "ap-south-1", key)

    def list_all_files_with_time_from_s3_bucket(self, bucket_name: str, prefix=""):
        """
        returns all files in bucket
        """
        files_list = []
        bucket = self.client.Bucket(bucket_name)
        for file in bucket.objects.filter(Prefix=prefix):
            files_list.append([file.key, file.last_modified])

        return files_list

    def generate_presigned_url_for_s3_object(self, key, bucket_name, expiry_time=10800):
        """
        generates presigned url for object which expires after given time
        """
        return self.client.meta.client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': key},
                                                              ExpiresIn=expiry_time)

    def get_s3_url(self, bucket, key, region_name="ap-south-1"):
        url = f"https://s3-{region_name}.amazonaws.com/{bucket}/{key}"
        return url

    def upload_object_from_string(self, bucket, key, data, params={}):
        try:
            if self.s3_client is None:
                print(f"unable to make S3 connection, BUCKET : {bucket}, KEY: {key}")
            result = self.s3_client.put_object(Bucket=bucket, Key=key, Body=data,
                                            ContentType=params.get('Content-Type', 'text/plain'),
                                            ACL=params.get('ACL', 'private'))
            res = result.get('ResponseMetadata')

            if res.get('HTTPStatusCode') == 200:
                logging.info('File Uploaded Successfully')
                return {"success":True,"url":self.get_s3_url(bucket,key)}
            else:
                logging.info('File Not Uploaded')
                return {"success": False}
        except Exception as uploadExp:
            logging.error(f"log_key: upload_object_from_string, err: {uploadExp}")
            return {"success": False}
