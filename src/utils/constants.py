import os


def get_s3_region() -> str | None:
    '''Get the S3 region from environment variables.'''
    return os.getenv('S3_REGION')


def get_s3_endpoint() -> str | None:
    '''Get the S3 endpoint from environment variables.'''
    return os.getenv('S3_ENDPOINT')


DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
