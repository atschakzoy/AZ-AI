import os
from dotenv import load_dotenv
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
)

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

endpoint = os.environ["SEARCH_ENDPOINT"]
key = os.environ["SEARCH_KEY"]

index_client = SearchIndexClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

search_client = SearchClient(
    endpoint=endpoint,
    index_name="documents",
    credential=AzureKeyCredential(key)
)

fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="title", type=SearchFieldDataType.String),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True)             
]

index = SearchIndex(name="documents",fields=fields)
index_client.create_or_update_index(index)
print("Index created")

documents = [
    {"id": "1", "title": "Azure Resource Groups", "content": "A resource group is a container that holds related resources for an Azure solution.", "category": "azure-basics"},
    {"id": "2", "title": "Azure App Service", "content": "Azure App Service is a fully managed platform for building web apps and APIs.", "category": "compute"},
    {"id": "3", "title": "Azure Blob Storage", "content": "Blob Storage stores unstructured data like images, videos, and documents in the cloud.", "category": "storage"},
    {"id": "4", "title": "Azure Functions", "content": "Azure Functions is a serverless compute service that runs code in response to events.", "category": "compute"},
    {"id": "5", "title": "Azure Key Vault", "content": "Key Vault stores and manages secrets, keys, and certificates securely.", "category": "security"},
]

result = search_client.upload_documents(documents)
print(f"Uploaded {len(result)} documents")

print("--- Full-text search ---")
results = search_client.search(
    search_text="resource group",
    select=["id", "title", "content"],
    top=5
)

for result in results:
    print(result["title"])
    print(result["@search.score"])


print("--- Filtered search ---")
results = search_client.search(
    search_text="*",
    filter="category eq 'compute'",
    select=["title", "category"]
)

for result in results:
    print(result["title"], result["category"])


print("--- Faceted search ---")
results = search_client.search(
    search_text="*",
    facets=["category"],
    select=["title"]
)

for facet in results.get_facets()["category"]:
    print(facet["value"], facet["count"])
