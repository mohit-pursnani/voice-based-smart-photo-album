import json
import boto3
import requests
import inflect
inflect = inflect.engine()

def push_to_lex(query):
    lex = boto3.client('lex-runtime')
    response = lex.post_text(
        botName='******',                 
        botAlias='prod',
        userId="root",           
        inputText=query
    )
    print("lex-response", response)
    labels = []
    if 'slots' not in response:
        print("No photo collection for query {}".format(query))
    else:
        print ("slot: ",response['slots'])
        slot_val = response['slots']
        for key,value in slot_val.items():
            if value!=None:
                labels.append(value)
    return labels


def search_elastic_search(label):
    region = 'us-east-1' 
    service = 'es'
    url = 'https://*******-*****.us-east-1.es.amazonaws.com/photos/_search?q='
    
    resp = []
    url2 = url+label
    resp.append(requests.get(url2, auth=('****', '******')).json())
            
    print ("RESPONSE" , resp)

    return resp
    

def put_in_s3(searchRespone):
    output = []
    print("searchRespone: ",searchRespone)
    for r in searchRespone:
        if 'hits' in r:
             for val in r['hits']['hits']:
                key = val['_source']['objectKey']
                if key not in output:
                    output.append("https://******.****.us-***.amazonaws.com/"+key)
    print("output: ",output)
    
    return output


def lambda_handler(event, context):
    q = event['queryStringParameters']['q']
    print(q)
    img_paths = []
    outputArray= []
    labels = push_to_lex(q)
    print("labels", labels)
    if len(labels) != 0:
        for label in labels:
            if (label is not None) and label != '':
                if inflect.singular_noun(label) == False:
                    response = search_elastic_search(label)
                    print("response: ",response)
                    outputArray = put_in_s3(response)
                    # If singular put only one value
                    if len(outputArray) != 0:
                        img_paths.append(outputArray[0])
                    print (label, "is singular")
                else:
                    response = search_elastic_search(inflect.singular_noun(label, count=None))
                    print("response: ",response)
                    img_paths += put_in_s3(response)
                    print (label, "is plural")
    img_paths = list(set(img_paths))
    print("img_paths: ",img_paths)
    if not img_paths:
        return{
            'statusCode':404,
            'headers': {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"*","Access-Control-Allow-Headers": "*"},
            'body': json.dumps('No Results found')
        }
    else:  
        print(img_paths)
        return{
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"*","Access-Control-Allow-Headers": "*"},
            'body': json.dumps(img_paths)
        }