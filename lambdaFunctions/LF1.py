import json
import boto3
import urllib.parse
import requests
import base64
import botocore.response as br

def rekognition_function(bucket_name, file_name):
    print("bucket_name: ",bucket_name)
    print("file_name: ",file_name)
    try:
        client = boto3.client('rekognition')
        response = client.detect_labels(
            Image={
                'S3Object':{
                    'Bucket':bucket_name, 
                    'Name': file_name
                }
            }, 
            MaxLabels=10 
        )
    except:
        print("Invalid image format")
    
    label_names = []

    label_names = list(map(lambda x:x['Name'], response['Labels']))
    label_names = [x.lower() for x in label_names]
    print("label names are: ", label_names)
    return label_names


def store_json_elastic_search(json_object):
    region = 'us-east-1' 
    service = 'es'
    credentials = boto3.Session().get_credentials()
    
    host = 'https://**************.us-east-1.es.amazonaws.com/'
    index = 'photos'
    url = host + index + '/doc'
    headers = {"Content-Type": "application/json"}
    
    resp = requests.post(url,auth=('******', '******'), data = json.dumps(json_object),headers = headers)
    print("response: ",resp.text)

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    record = event['Records'][0]
    
    print("event : ", event)
    s3Object = record['s3']
    bucket = s3Object['bucket']['name']
    file_name = s3Object['object']['key']
    key = s3Object['object']['key']
    response = s3.head_object(Bucket=bucket, Key=key)
    print("head_object : " , response)
    if response["Metadata"]:
        customlabels = response["Metadata"]["customlabels"]
        print("customlabels : ", customlabels)
        customlabels = customlabels.split(',')
        customlabels = list(map(lambda x: x.lower(), customlabels))
    time_stamp = record['eventTime']
    print("Timestamp is :",time_stamp)
    label_names = []
    label_names = rekognition_function(bucket, file_name)
    if response["Metadata"]:
        for cl in customlabels:
            print(cl)
            cl = cl.lower().strip()
            if cl not in label_names:
                label_names.append(cl)
    print("label_names: ",label_names)
    json_object = {
        'objectKey': s3Object['object']['key'],
        'bucket': bucket,
        'createdTimestamp': time_stamp,
        'labels': label_names
    }
    store_json_elastic_search(json_object)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
