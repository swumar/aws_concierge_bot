import json
import boto3

def lambda_handler(event, context):

    client = boto3.client('lex-runtime')
    msg = event['messages'][0]['unstructured']['text']
    res = client.post_text(botName='dining_bot', botAlias='dining_bot', userId='root', inputText=msg)
    response = {
        "messages" : [{
            "type": "unstructured",
            "unstructured": {
                "text": res['message']
            }
        }]
    }
    
    return response