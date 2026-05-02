import sys
import os
import logging
import boto3

# initialize logger
logger = logging.getLogger()
logger.setLevel("INFO")

# initialize S3 client once outside handler (faster for repeated invocations)
s3_client = boto3.client("s3", region_name="ap-southeast-2")

# make sure Lambda can find fetch_fred.py in /var/task
sys.path.append("/var/task")

from fetch_fred import main

def handler(event, context):
    """
    Main Lambda handler — triggered daily by EventBridge
    Pulls US Treasury yield curve data from FRED and uploads to S3
    """
    try:
        # get bucket name from environment variable
        # we'll set this in the Lambda console later
        bucket_name = os.environ.get("BUCKET_NAME", "yield-curve-pipeline")
        
        logger.info("Lambda triggered — starting yield curve pull")
        
        main()
        
        logger.info(f"Successfully pulled yield curve data and uploaded to {bucket_name}")
        
        return {
            "statusCode": 200,
            "body": "yield curve pull complete"
        }
        
    except Exception as e:
        logger.error(f"Error pulling yield curve data: {str(e)}")
        raise