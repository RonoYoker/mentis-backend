import boto3
from django.conf import settings


class S3Helper:
    def __init__(self, **kwargs):
        self.client = self.get_s3_connection()

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