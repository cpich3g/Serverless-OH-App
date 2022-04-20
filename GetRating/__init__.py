import logging
import json
from textwrap import indent
import azure.cosmos.cosmos_client as cosmos_client
import azure.functions as func
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
    database = client.get_database_client(DATABASE_ID.value)
    container = database.get_container_client(CONTAINER_ID.value)
    
    req_body = req.get_json()
    ratingId = req_body['ratingId']
    
    if not ratingId:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('ratingId')
    
    rating = list(container.query_items(query="SELECT * FROM ratings r WHERE r.id = @id", parameters=[{"name":"@id", "value":ratingId}],enable_cross_partition_query=True))
    
    
    if rating:
        return func.HttpResponse(json.dumps(rating[0], indent=True))
    else:
        return func.HttpResponse(
            "Rating ID seems to be wrong",
            status_code=404
        )

    