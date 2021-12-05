import boto3
import requests
from requests_aws4auth import AWS4Auth
import os

# env variables
ES_REPO_NAME = os.environ["ES_REPO_NAME"]
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
IAM_ROLE_ARN = os.environ["IAM_ROLE_ARN"]
HOST = os.environ["HOST"]
REGION = os.environ["REGION"]

service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, service, session_token=credentials.token)


def handler(event, context):
    path = '_snapshot/' + ES_REPO_NAME
    url = HOST + path
    payload = {
        "type": "s3",
        "settings": {
            "bucket": S3_BUCKET_NAME,
            "region": REGION,
            "role_arn": IAM_ROLE_ARN
        }
    }

    headers = {"Content-Type": "application/json"}
    r = requests.put(url, auth=awsauth, json=payload, headers=headers)

    print("The response code for register repo {repo_name} is {r_code}".format(repo_name=ES_REPO_NAME,
                                                                               r_code=r.status_code)
          )
    print("The response for register repo {repo_name} is {r_response}".format(repo_name=ES_REPO_NAME,
                                                                              r_response=r.text)
          )