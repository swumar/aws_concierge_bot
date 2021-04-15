import requests
import json
import boto3
import datetime
from decimal import Decimal
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from boto3.dynamodb.conditions import Attr

ENDPOINT = "https://api.yelp.com/v3/businesses/search"
API_KEY = "INSERT API KEY HERE"

def get_restaurants(cuisine):
    restaurant_list = []
    iterations = 20
    
    for i in range(iterations):
        parameter = {
            "term": cuisine + " restaurants",
            "location": "New York City",
            "limit": 50,
            "offset": 50 * i,
            'sort_by': 'best_match'
        }
                
        response = requests.get(
            url = ENDPOINT,
            data = "",
            headers = {"Authorization": "Bearer "+ API_KEY},
            params = parameter,
        )
        raw_data = json.loads(response.text)
        data = raw_data["businesses"]
        restaurant_list = restaurant_list + data


    return restaurant_list

def load_data(restaurant_data, cuisine):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("yelp-restaurants")
    count = 0
    for restaurant in restaurant_data:
        in_table= table.get_item(Key={'restaurantID':restaurant['id']})
        if 'Item' in in_table:
            continue

        try: 
            entry = {
                "insertedAtTimestamp": str(datetime.datetime.now()),
                "restaurantID": restaurant["id"],
                "alias": restaurant["alias"],
                "name": restaurant["name"],
                "rating": Decimal(restaurant["rating"]),
                "numOfReviews": int(restaurant["review_count"]),
                "address": restaurant["location"]["display_address"],
                "latitude": str(restaurant["coordinates"]["latitude"]),
                "longitude": str(restaurant["coordinates"]["longitude"]),
                "zip_code": restaurant["location"]["zip_code"],
                "cuisine": cuisine,
                "city": restaurant["location"]["city"]
            }

            table.put_item(
                Item= entry
            )
            count +=1

        except Exception as e:
            print("ERROR: ", e)
            print("For Table Entry: \n ", entry)
            exit(1)
        
        
    return count

def create_elastic_search_index():
    credentials = boto3.Session().get_credentials()
    region = "us-east-1"
    service = "es"
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        service,
        session_token=credentials.token,
    )
    host = "Enter elastic search host link"

    es = Elasticsearch(
        hosts=[{"host": host, "port": 443}],
        http_auth = awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )

    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("yelp-restaurants")
    count = 0
 
    result = table.scan()
    print(len(result['Items']))

    while(True):

        for restaurant in result['Items']:
            es.index(
                index="restaurants",
                doc_type="Restaurant",
                id=restaurant["restaurantID"],
                body={"restaurantID": restaurant["restaurantID"], "cuisine": restaurant['cuisine']},
            )
            count+=1
        if 'LastEvaluatedKey' not in result:
            break
        result = table.scan(ExclusiveStartKey=result['LastEvaluatedKey'])
        print(len(result['Items']))

    
    return count


if __name__ == '__main__':
    cuisine_types = ['indian', 'japanese', 'chinese', 'thai', 'korean', 'mexican']
    for cuisine in cuisine_types:
        yelp_data = get_restaurants(cuisine)
        print(len(yelp_data))
        entries = load_data(yelp_data, cuisine)
        print("Entries added to table for ", cuisine, ":",entries)
    
    
    count = create_elastic_search_index()
    print("Success", count)

    
        
