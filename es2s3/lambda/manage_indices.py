import boto3
import requests
from requests_aws4auth import AWS4Auth
import os
import datetime
import json
# env variables
ES_REPO_NAME = os.environ["ES_REPO_NAME"]
ES_INDEX_PREFIX = os.environ["ES_INDEX_PREFIX"]
INDEX_RETENTION = int(os.environ["INDEX_RETENTION"])
SNAPSHOT_RETENTION = int(os.environ["SNAPSHOT_RETENTION"])
IAM_ROLE_ARN = os.environ["IAM_ROLE_ARN"]
HOST = os.environ["HOST"]
REGION = os.environ["REGION"]
NUMBER_OF_SHARDS = 5
NUMBER_OF_REPLICAS = 1

service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, service, session_token=credentials.token)
headers = {"Content-Type": "application/json"}

# assume the index is of the format ES_INDEX_PREFIX + 'YYYY.MM.DD'


def handler(event, context):
    # let's make the snapshot name = "sn_" + index_name

    rundate = datetime.datetime.strptime(event['time'][:10], '%Y-%m-%d')

    # since there is only one thread to handle the snapshot
    # we better delete first, cause it probably takes less time
    # delete the out of date snapshot
    snapshot_to_delete = 'sn_' + ES_INDEX_PREFIX + (rundate -
                                                    datetime.timedelta(days=SNAPSHOT_RETENTION)).strftime('%Y.%m.%d')
    url = HOST + '/'.join(['_snapshot', ES_REPO_NAME, snapshot_to_delete])  #+ '?wait_for_completion=true'
    r = requests.delete(url, auth=awsauth, headers=headers)
    print("The response of deleting snapshot {snapshot_name} is {r_code}".format(snapshot_name=snapshot_to_delete,
                                                                                 r_code=r.status_code
                                                                                 ))
    print("The response of deleting snapshot {snapshot_name} is {r_response}".format(snapshot_name=snapshot_to_delete,
                                                                                     r_response=r.text
                                                                                     ))

    # backup the index
    index_to_snapshot = ES_INDEX_PREFIX + (rundate -
                                           datetime.timedelta(INDEX_RETENTION)).strftime('%Y.%m.%d')
    payload = {
        "indices": index_to_snapshot,
        "ignore_unavailable": True,
        "include_global_state": False
    }
    url = HOST + '/'.join(['_snapshot',
                           ES_REPO_NAME,
                           'sn_' + index_to_snapshot
                           ])
    r = requests.put(url, auth=awsauth, json=payload, headers=headers)
    print("The response code of snapshot index {index_name} is {r_code}".format(index_name=index_to_snapshot,
                                                                                r_code=r.status_code
                                                                                ))
    print("The response of snapshot index {index_name} is {r_response}".format(index_name=index_to_snapshot,
                                                                               r_response=r.text
                                                                               ))
    # delete the index backed up yesterday
    index_to_delete = ES_INDEX_PREFIX + (rundate -
                                         datetime.timedelta(days=INDEX_RETENTION + 1)).strftime('%Y.%m.%d')
    index_to_delete_snapshot = 'sn_' + index_to_delete
    url = HOST + '/'.join(['_snapshot', ES_REPO_NAME, index_to_delete_snapshot])
    r = requests.get(url, auth=awsauth, headers=headers)
    if r.status_code == 200 and json.loads(r.text)['snapshots'][0]['state'] == 'SUCCESS':
        print("Snapshot of index {index} exists, let's delete the index".format(index=index_to_delete))

        url = HOST + index_to_delete
        r = requests.delete(url, auth=awsauth, headers=headers)

        print("The response of deleting index {index_name} is {r_code}".format(index_name=index_to_delete,
                                                                               r_code=r.status_code
                                                                               ))
        print("The response of deleting index {index_name} is {r_response}".format(index_name=index_to_delete,
                                                                                   r_response=r.text
                                                                                   ))
    else:
        print("Snapshot of index {index} doesn't exist, please snapshot the index before deletion".format(index=index_to_delete))

    # create the index for tomorrow
    index_to_create = ES_INDEX_PREFIX + (rundate + datetime.timedelta(days=1)).strftime('%Y.%m.%d')
    payload = {
        "settings": {
            "index": {
                "number_of_shards": NUMBER_OF_SHARDS,
                "number_of_replicas": NUMBER_OF_REPLICAS
            }
        }
    }
    url = HOST + index_to_create
    r = requests.put(url, auth=awsauth, json=payload, headers=headers)
    print("The response of creating index {index_name} is {r_code}".format(index_name=index_to_create,
                                                                           r_code=r.status_code
                                                                           ))
    print("The response of creating index {index_name} is {r_response}".format(index_name=index_to_create,
                                                                               r_response=r.text
                                                                               ))


