import json
import boto3
import re
from datetime import datetime, timedelta
import dateutil.tz




def lambda_handler(event, context):

    source = event['invocationSource']
    slots = event['currentIntent']['slots']
    intent = event['currentIntent']['name']

    delresponse = {
            "dialogAction": {
                "type": "Delegate",
                "slots": slots,
            }
        }

    locationresponse = {
            "dialogAction": {
                "type": "ElicitSlot",
                "message": {
                    "contentType": "PlainText",
                    "content": "I am only able to suggest restaurants in New York City (Brooklyn, Queens and Manhattan)."
                },
                "intentName": intent,
                "slots": slots,
                "slotToElicit": "location"
            }
        }

    cuisineresponse = {
            "dialogAction": {
                "type": "ElicitSlot",
                "message": {
                    "contentType": "PlainText",
                    "content": "Currently, I am able to suggest restaurants for Chinese, Japanese, Mexican, Indian, Thai and Korean cuisines.\n Please choose one from the list. "
                },
                "intentName": intent,
                "slots": slots,
                "slotToElicit": "cuisine"
            }
        }
    peopleresponse = {
            "dialogAction": {
                "type": "ElicitSlot",
                "message": {
                    "contentType": "PlainText",
                    "content": "I can find dinning accommodation for up to 20 people. Please re-enter the party size."
                },
                "intentName": intent,
                "slots": slots,
                "slotToElicit": "people"
            }
        }

    dateresponse = {
            "dialogAction": {
                "type": "ElicitSlot",
                "message": {
                    "contentType": "PlainText",
                    "content": "The date you entered is in the past. Please enter a valid date."
                },
                "intentName": intent,
                "slots": slots,
                "slotToElicit": "date"
            }
        }

    timeresponse = {
            "dialogAction": {
                "type": "ElicitSlot",
                "message": {
                    "contentType": "PlainText",
                    "content": "Dinning time must be at least 15 mintutes from now. Please enter a valid time."
                },
                "intentName": intent,
                "slots": slots,
                "slotToElicit": "time"
            }
        }

    numberresponse = {
            "dialogAction": {
                "type": "ElicitSlot",
                "message": {
                    "contentType": "PlainText",
                    "content": "Please enter a valid 10 digits phone number."
                },
                "intentName": intent,
                "slots": slots,
                "slotToElicit": "number"
            }
        }

    successresponse = {
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {
                    "contentType": "PlainText",
                    "content": "You will receive our restaurant suggestions shortly. Have a good day!"
                }
            }
        }

    if source == 'DialogCodeHook':

        if slots['location'] is None:
            return delresponse

        if slots['location'] and not valdate_location(slots['location']):
            return locationresponse


        if slots['cuisine'] is None:
            return delresponse

        if slots['cuisine'] and not validate_cuisine(slots['cuisine']):
            return cuisineresponse


        if slots['people'] is None:
            return delresponse

        if slots['people'] and not validate_party_size(slots['people']):
            return peopleresponse


        if slots['date'] is None:
            return delresponse
            
        if slots['date'] and not validate_date(slots['date']):
            return dateresponse


        if slots['time'] is None:
            return delresponse
        if slots['time'] and not validate_time(slots['date'], slots['time']):
            return timeresponse


        if slots['number'] is None:
            return delresponse

        if slots['number'] and not validate_phone_nubmer(slots['number']):
            return numberresponse


    if source == 'FulfillmentCodeHook':

        sqs = boto3.client('sqs')
        queue_url = sqs.get_queue_url(QueueName='hw1_dining')['QueueUrl']
        sqs.send_message(QueueUrl=queue_url, DelaySeconds=10,
                         MessageBody=(json.dumps(slots)))
        return successresponse

    return delresponse

def validate_cuisine(cuisine):
    # valid cuisines
    cuisines = ["chinese", "indian", "japanese", "mexican", "thai", "korean"]
    
    # returns true if the cusine is present in valid list
    if cuisine.lower() in cuisines:
        return True
    return False

def validate_party_size(size):
    if int(size) < 1 or int(size) > 20:
        return False
    return True

def validate_phone_nubmer(phone_number):
    # set pattern for valid US phone number
    pattern = re.compile(
        "^(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$")
    # if number matches pattern return True 
    if pattern.match(phone_number) is not None:
        return True
    return False

def valdate_location(location):
    # valid locations
    locations = ["nyc", "brooklyn", "new york city",
        "new york", "queens", "manhattan"]
   
    # return true if location is in valid locations, not case sensitive
    if location.lower() not in locations:
        return False
    return True

def validate_date(date):
    input_date = datetime.strptime(date, "%Y-%m-%d")
    
    # a valid date is upto current date
    valid_date = datetime.now()

    # returns true if date is equal to or after valid date 
    if input_date.date() >= valid_date.date():
        return True
    return False


def validate_time(date, time):
    input_date = datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M")
    
    # set eastern time zone
    eastern = dateutil.tz.gettz("US/Eastern")
    
    # valid date is current time for eastern time zone + 15 mins
    valid_date_time = datetime.now(eastern) + timedelta(minutes=15)
    
    # if date in future or date is today's then validate time or if date 
    # equals today's, check time entered is equal to or greater than valid time
    if (input_date.date() > valid_date_time.date()) or (
        input_date.date() == valid_date_time.date()
        and input_date.time() >= valid_date_time.time()
    ):
        return True
    return False
