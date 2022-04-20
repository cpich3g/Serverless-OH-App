import logging
import azure.cosmos.cosmos_client as cosmos_client
import json
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
    
    userId = req.params.get('userId')
    
    ratings = list(container.query_items(query="SELECT * FROM r WHERE r.userId = @Id", parameters=[{"name":"@Id", "value":userId}],enable_cross_partition_query=True))
    
    if ratings:
        return func.HttpResponse(json.dumps(ratings, indent=True))
    else:
        return func.HttpResponse(
            "User Cannot be found or User does not have any ratings",
            status_code=404
        )

def query_items(container, userId):
    items = list(container.query_items(query="SELECT * FROM r WHERE r.userId = @Id", parameters=[{"name":"@Id", "value":userId}],enable_cross_partition_query=True))
