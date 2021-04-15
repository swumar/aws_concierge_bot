import json
import boto3
import random
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


def elastic_search(cuisine):
    credentials = boto3.Session().get_credentials()
    region = "us-east-1"
    service = "es"
    host = "search-restaurants-yad4az4e32h73o7e5ijgzai3rm.us-east-1.es.amazonaws.com"

    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                       region, service, session_token=credentials.token)
    es = Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    query_body = {
        "size": 3,
        "from": random.randrange(500),
        "query": {
            "match": {
                "cuisine": cuisine
            }
        }
    }
    result = es.search(body=query_body, index='restaurants')
    return result


def lambda_handler(event, context_message):
    sqs = boto3.client('sqs')
    queue_url = sqs.get_queue_url(QueueName='hw1_dining')['QueueUrl']
    res = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)

    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("yelp-restaurants")

    if 'Messages' in res.keys():
        for message in res['Messages']:
            details = json.loads(message['Body'])
            cuisine = details['cuisine']
            people = details['people']
            number = details['number']
            if len(number) > 10:
                number=re.sub('[^0-9]+', '', number)
                if len(number) == 10 or (len(number) == 11 and number[0] == "1"):
                    number = number[1:]
            formatted_number = "+1"+number  
            location = details['location'] 
            date = details['date']   
            time = details['time']
            elasticdata = elastic_search(cuisine)

            restaurant_info = []
            res = json.dumps(elasticdata)
            for i in elasticdata["hits"]["hits"]:
                print(i["_id"])
                result = table.get_item(
                    Key={
                        "restaurantID": i["_id"],
                    }
                )
                restaurant_info.append(result)
           
            text_message = (
                "Hi! Listed below are the "
                + str(cuisine).title()
                + " restaurant suggestions for "
                + str(people)
                + " people on "
                + str(date)
                +" at "
                + str(time)
                + " near "
                + str(location).title() 
                + ":"
                + "\n"
            )

            for i in range(0, 3):
                response = restaurant_info[i]
                msg = (
                    str(i + 1)
                    + ")"
                    + str(response["Item"]["name"])
                    + " located at "
                    + ', '.join(response["Item"]["address"])
                    + "\n"
                )
                text_message = text_message + msg

            text_message = text_message + "Hope you like our suggestions!"
            # print(text_message)

            try:
                client = boto3.client('sns', 'us-east-1')
                client.set_sms_attributes(
                    attributes={
                        'DefaultSMSType': 'Transactional'
                    }
                )
                response = client.publish(
                    Message=text_message, MessageStructure='string', PhoneNumber=formatted_number)

            except Exception as e:
                print("Sending message failed. Error:")
                print(e)

            receipt_handle = message['ReceiptHandle']
            sqs.delete_message(QueueUrl=queue_url,
                               ReceiptHandle=receipt_handle)
            return {
                'statusCode': 200,
                'body': json.dumps('Message Sent to SNSQueue')
            }

    else:
        return {
            "statusCode": 500,
            "body": json.dumps("Error fetching data from sqs."),
        }

