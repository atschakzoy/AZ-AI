import os
import time
from dotenv import load_dotenv
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    SearchIndexer,
    SearchIndexerDataSourceConnection,
    SearchIndexerDataContainer,
    SearchIndexerSkillset,
    EntityRecognitionSkillV3,
    KeyPhraseExtractionSkill,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    FieldMapping,
)
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

endpoint = os.environ["SEARCH_ENDPOINT"]
key = os.environ["SEARCH_KEY"]
container_name = os.environ["STORAGE_CONTAINER_NAME"]
connection_string = os.environ["STORAGE_CONNECTION_STRING"]

INDEX_NAME = "enriched-documents"
DATA_SOURCE_NAME = "blob-datasource"
SKILLSET_NAME = "my-skillset"
INDEXER_NAME = "my-indexer"

index_client = SearchIndexClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

indexer_client = SearchIndexerClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

search_client = SearchClient(
    endpoint=endpoint,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(key)
)

# --- SETUP: run once to create everything ---
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SearchableField(name="entities", type=SearchFieldDataType.String),
    SearchableField(name="keyphrases", type=SearchFieldDataType.String),
]
index_client.create_or_update_index(SearchIndex(name=INDEX_NAME, fields=fields))
print("Index ready")

data_source = SearchIndexerDataSourceConnection(
    name=DATA_SOURCE_NAME,
    type="azureblob",
    connection_string=connection_string,
    container=SearchIndexerDataContainer(name=container_name)
)
indexer_client.create_or_update_data_source_connection(data_source)
print("Data source ready")

skillset = SearchIndexerSkillset(
    name=SKILLSET_NAME,
    skills=[
        EntityRecognitionSkillV3(
            inputs=[InputFieldMappingEntry(name="text", source="/document/content")],
            outputs=[OutputFieldMappingEntry(name="namedEntities", target_name="entities")]
        ),
        KeyPhraseExtractionSkill(
            inputs=[InputFieldMappingEntry(name="text", source="/document/content")],
            outputs=[OutputFieldMappingEntry(name="keyPhrases", target_name="keyphrases")]
        ),
    ]
)
indexer_client.create_or_update_skillset(skillset)
print("Skillset ready")

try:
    indexer_client.delete_indexer(INDEXER_NAME)
except Exception:
    pass

indexer = SearchIndexer(
    name=INDEXER_NAME,
    data_source_name=DATA_SOURCE_NAME,
    skillset_name=SKILLSET_NAME,
    target_index_name=INDEX_NAME,
    output_field_mappings=[
        FieldMapping(source_field_name="/document/entities", target_field_name="entities"),
        FieldMapping(source_field_name="/document/keyphrases", target_field_name="keyphrases"),
    ]
)
indexer_client.create_or_update_indexer(indexer)
print("Indexer ready")

# --- WAIT: poll until indexer finishes ---
print("Waiting for indexer to finish...")
for _ in range(12):
    time.sleep(10)
    status = indexer_client.get_indexer_status(INDEXER_NAME)
    last_run = status.last_result
    if last_run and last_run.status in ("success", "transientFailure", "persistentFailure"):
        print(f"Indexer finished: {last_run.status}, docs: {last_run.item_count}, failed: {last_run.failed_item_count}")
        break
    print("Still indexing...")

# --- QUERY: search the enriched results ---
results = search_client.search(
    search_text="*",
    select=["keyphrases", "entities"]
)

for result in results:
    print("Key phrases:", result["keyphrases"])
    print("Entities:", result["entities"])
