from datetime import datetime
from itertools import product
import logging
import secrets
from urllib import request
import uuid
import json
from jsonschema import validate
import requests
import azure.functions as func
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential



def main(req: func.HttpRequest) -> func.HttpResponse:
    credentials = DefaultAzureCredential()
    client = SecretClient(vault_url=os.environ['VAULT_URL'], credential=credentials)
    HOST = client.get_secret(name = 'HOST')
    MASTER_KEY = client.get_secret(name = 'MASTER-KEY')
    DATABASE_ID = client.get_secret(name = 'DATABASE')
    CONTAINER_ID = client.get_secret(name = 'CONTAINER')
    client = cosmos_client.CosmosClient(HOST.value, {'masterKey': MASTER_KEY.value} )
    try:
        
        db = client.create_database_if_not_exists(id=DATABASE_ID.value)
        
        container = db.create_container_if_not_exists(id=CONTAINER_ID.value, partition_key=PartitionKey(path='/id', kind='Hash'))
    except exceptions.CosmosHttpResponseError as e:
        print('\nrun_sample has caught an error. {0}'.format(e.message))        
        

    id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
    
    schema = {
                "type": "object",
                "properties": {
                "userId": {"type": "string"},
                "productId": {"type": "string"},
                "locationName": {"type": "string"},
                "rating": {"type": "number", "minimum": 0, "maximum": 5},
                "userNotes": {"type": "string"}
                },
            }
    try:
        req_body = req.get_json()
        validate(instance = req_body, schema = schema)
        req_body['id'] = id
        req_body['timestamp'] = timestamp
    except ValueError as err:
        return func.HttpResponse(f"Invalid request body: {err}", status_code = 404)
    # except jsonschema.ValidationError as err:
        # return func.HttpResponse(f"Request Body is not as per schema: {err}", status_code = 404)

    
    userId = req_body['userId']
    print(userId)
    checkUser = requests.get('https://serverlessohapi.azurewebsites.net/api/GetUser?userId='+userId)
    if checkUser.status_code == 400:
        return func.HttpResponse(f"User not found", status_code = 404)
    
    productId = req_body['productId']
    print(productId)
    checkProduct = requests.get('https://serverlessohapi.azurewebsites.net/api/GetProduct?productId='+productId)
    if checkProduct.status_code == 400:
        return func.HttpResponse(f"Product not found", status_code = 404)
    
    container.create_item(body=req_body)
    return func.HttpResponse(f"{req_body}", status_code = 200)

    
