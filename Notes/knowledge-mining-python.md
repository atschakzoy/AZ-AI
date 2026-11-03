# Knowledge Mining — Python Patterns

Quick reference for writing Python scripts that call Azure AI Search.

---

## Install

```bash
pip install azure-search-documents
```

---

## Three Clients

Azure AI Search splits its functionality across three completely separate clients. They talk to the same Search service but do different things.

### `SearchIndexClient` — the index schema client

Think of this as the **database admin**. It manages index schemas only.

- Imported from: `azure.search.documents.indexes`
- Talks to: the Search service itself (not a specific index)
- You use it: once, at setup time, to create your index schema
- Methods: `create_or_update_index()`, `delete_index()`, `list_indexes()`

### `SearchIndexerClient` — the indexer admin client

Think of this as the **pipeline admin**. It manages everything that runs server-side during indexing.

- Imported from: `azure.search.documents.indexes`
- Talks to: the Search service itself
- You use it: when setting up the automated indexing pipeline
- Methods: `create_or_update_data_source_connection()`, `create_or_update_skillset()`, `create_or_update_indexer()`, `run_indexer()`

### `SearchClient` — the data client

Think of this as the **app client**. It works with documents inside a specific index — uploading, deleting, and searching.

- Imported from: `azure.search.documents`
- Talks to: **one specific index** (you pass `index_name` when creating it)
- You use it: every time you upload or search documents
- Methods: `upload_documents()`, `search()`, `delete_documents()`

### The key difference

```
SearchIndexClient   → index schemas only (CREATE TABLE equivalent)
SearchIndexerClient → data sources, skillsets, indexers (the automation pipeline)
SearchClient        → documents inside one index (INSERT / SELECT equivalent)
```

```
SearchIndexClient → manages indexes (schema)
SearchClient      → manages documents (data inside one index)
```

The analogy in SQL:
- `SearchIndexClient` = running `CREATE TABLE` or `ALTER TABLE`
- `SearchClient` = running `INSERT`, `SELECT`, `DELETE` on rows in that table

### The correct split between the three clients

```
SearchIndexClient      → index schema only
SearchIndexerClient    → data source, skillset, indexer
SearchClient           → search and upload
```

`SearchIndexerClient` is the one that creates all three pipeline objects:

| Object | Method |
|---|---|
| Data source | `create_or_update_data_source_connection()` |
| Skillset | `create_or_update_skillset()` |
| Indexer | `create_or_update_indexer()`, `run_indexer()`, `get_indexer_status()` |

`SearchIndexClient` manages the index schema only — nothing else.

`SearchClient` is only for querying and uploading documents — it has no admin capabilities.

---

## Imports

```python
# For creating/managing indexes
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType
)

# For uploading and searching documents
from azure.search.documents import SearchClient

# Auth
from azure.core.credentials import AzureKeyCredential
```

---

## Client Setup

```python
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential

load_dotenv()

endpoint = os.environ["SEARCH_ENDPOINT"]
key = os.environ["SEARCH_KEY"]

# Client for managing indexes
index_client = SearchIndexClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

# Client for uploading and searching documents
search_client = SearchClient(
    endpoint=endpoint,
    index_name="documents",      # the name of the index you created
    credential=AzureKeyCredential(key)
)
```

---

## Create an Index

An index is like a database table — you define the schema (what fields exist and what you can do with them) before putting data in it.

```python
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchFieldDataType
)

fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="title", type=SearchFieldDataType.String),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
]

index = SearchIndex(name="documents", fields=fields)
index_client.create_or_update_index(index)
print("Index created")
```

- `key=True` — every index must have exactly one key field. This is the unique ID per document.
- `SearchableField` — full-text search works on these fields.
- `SimpleField` — exact match only. Use for IDs, categories, dates.
- `filterable=True` — lets you use this field in a `filter=` expression.
- `facetable=True` — lets you get counts per value (e.g. "3 documents in 'azure-basics'").
- `create_or_update_index` — creates if new, updates if it already exists.

---

## Upload Documents

Documents are just Python dictionaries. The keys must match the field names in your index schema.

```python
documents = [
    {
        "id": "1",
        "title": "Azure Resource Groups",
        "content": "A resource group is a container that holds related resources.",
        "category": "azure-basics"
    },
    {
        "id": "2",
        "title": "Azure App Service",
        "content": "Azure App Service is a fully managed platform for web apps and APIs.",
        "category": "compute"
    }
]

result = search_client.upload_documents(documents)
print(f"Uploaded {len(result)} documents")
```

- `upload_documents` sends the list to the index. If a document with that `id` already exists, it overwrites it.
- `result` is a list of `IndexingResult` objects — one per document — with `.succeeded` and `.key`.
- The dictionaries above are hardcoded for learning only. In production, the data always comes from somewhere real — see the patterns below.

---

## Where data actually comes from — production patterns

There are three ways to get data into an Azure AI Search index in production. Which one you use depends on where your data lives.

---

### Pattern 1 — Indexer + data source (Azure crawls automatically)

Use this when your files already live in an Azure service. You create a data source connection pointing at where the data is, and the indexer crawls it on a schedule without you writing any fetch logic.

Supported data sources out of the box:

| Data source | Type string | When to use |
|---|---|---|
| Azure Blob Storage | `"azureblob"` | PDFs, Word docs, images, CSVs stored in a container |
| Azure SQL Database | `"azuresql"` | Structured rows in a SQL table |
| Azure Cosmos DB | `"cosmosdb"` | JSON documents in a Cosmos container |
| Azure Table Storage | `"azuretable"` | Key-value table data |
| SharePoint Online | `"sharepoint"` | Documents in SharePoint sites |

```python
data_source = SearchIndexerDataSourceConnection(
    name=DATA_SOURCE_NAME,
    type="azureblob",           # change this to match your source
    connection_string=connection_string,
    container=SearchIndexerDataContainer(name=container_name)
)
indexer_client.create_or_update_data_source_connection(data_source)
```

The indexer crawls the data source automatically and runs your skillset on each document.

---

### Pattern 2 — Manual upload with real data (you control the pipeline)

Use this when your data comes from an API, a database Azure Search does not support natively, or you generate it programmatically. Instead of hardcoded dictionaries, you fetch real data and build the documents dynamically:

```python
# Example: read files from a folder, chunk them, upload each chunk
import os

documents = []
chunk_number = 0

for filename in os.listdir("my_documents"):
    with open(f"my_documents/{filename}", "r") as f:
        text = f.read()

    # split the text into chunks of roughly 500 words
    words = text.split()
    chunks = [words[i:i+500] for i in range(0, len(words), 500)]

    for chunk in chunks:
        chunk_number += 1
        documents.append({
            "id": f"{filename}_chunk_{chunk_number}",
            "source_file": filename,
            "content": " ".join(chunk)
        })

search_client.upload_documents(documents)
```

The shape is the same as the hardcoded example — a list of dictionaries — but the data comes from real files.

---

### Pattern 3 — RAG pipeline (the most common production pattern)

Use this when your data is complex documents (PDFs with tables, scanned files) and you need Document Intelligence to extract the content before indexing.

```
Files in Blob Storage or on disk
    ↓
Document Intelligence extracts text and tables from each file
    ↓
Your Python script chunks the extracted text
    ↓
upload_documents() pushes each chunk as one index document
    ↓
Azure AI Search index — ready to query
```

This combines manual upload with Document Intelligence. The indexer is not used here — you do the work yourself so you have full control over chunking and structure. This is what you will build in Stage 07 and 08 when you add embeddings and an LLM on top.

---

## Full-Text Search

```python
results = search_client.search(
    search_text="resource group",
    select=["id", "title", "content"],
    top=5
)

for result in results:
    print(result["title"])
    print(result["content"])
    print(result["@search.score"])
```

- `search_text` — the query. Azure splits it into words and scores documents by match.
- `select` — which fields to return. Like `SELECT` in SQL. Omit to return all fields.
- `top` — maximum number of results.
- `result["@search.score"]` — the relevance score. Higher = more relevant.

---

## Filtered Search

```python
results = search_client.search(
    search_text="app",
    filter="category eq 'compute'",
    select=["title", "content"]
)

for result in results:
    print(result["title"])
```

- `filter` uses OData syntax. `eq` means equals.
- The field must have `filterable=True` in the schema.
- You can combine: `filter="category eq 'compute' and id ne '1'"`.

---

## Faceted Search (counts per category)

```python
results = search_client.search(
    search_text="*",         # * means match everything
    facets=["category"],
    select=["title"]
)

# Print the facet counts
facets = results.get_facets()
for facet in facets["category"]:
    print(f"{facet['value']}: {facet['count']}")
```

- `search_text="*"` — match all documents (no filter on text).
- `facets=["category"]` — return counts per unique value in the `category` field.
- `results.get_facets()` — returns a dictionary. Key is the field name, value is a list of `{value, count}` objects.
- The field must have `facetable=True` in the schema.

---

## The Indexer Pipeline — Full Code Walkthrough

This section explains every part of `indexer.py` line by line, including Python concepts that appear for the first time.

---

### `import time`

`time` is a built-in Python module (comes with Python, no install needed). We use it for `time.sleep()` — pausing the script for a number of seconds.

```python
import time
time.sleep(10)   # pause the script for 10 seconds
```

Why we need it: the indexer runs asynchronously inside Azure. We need to wait for it to finish before we query the results.

---

### `try` / `except` — handling errors gracefully

This is the first time you've seen `try`/`except`. It means: "try to run this code — if it fails with an error, don't crash, just do this instead."

```python
try:
    indexer_client.delete_indexer("my-indexer")
except Exception:
    pass
```

- `try:` — attempt to delete the indexer
- `except Exception:` — if it fails (e.g. the indexer doesn't exist yet), catch the error
- `pass` — do nothing, just continue

Without `try`/`except`, if the indexer doesn't exist, `delete_indexer` raises an error and the whole script crashes. With it, the error is caught silently and the script continues.

You'll use this pattern whenever you call something that might fail for a "normal" reason — like deleting something that might not exist yet.

---

### Polling loop — waiting for the indexer

```python
for _ in range(12):
    time.sleep(10)
    status = indexer_client.get_indexer_status("my-indexer")
    last_run = status.last_result
    if last_run and last_run.status in ("success", "transientFailure", "persistentFailure"):
        print(f"Indexer finished: {last_run.status}")
        break
    print("Still indexing...")
```

Breaking this down:

- `for _ in range(12):` — loop 12 times. `_` is used as the variable name when you don't care about the loop counter — it's just a Python convention for "I'm not using this value".
- `time.sleep(10)` — wait 10 seconds on each loop iteration. 12 × 10 = 120 seconds maximum wait.
- `indexer_client.get_indexer_status("my-indexer")` — ask Azure: what is the indexer doing right now?
- `status.last_result` — the result of the most recent indexer run. Can be `None` if the indexer has never run.
- `if last_run and ...` — check two things: `last_run` is not None, AND the status is one of the finished states.
- `break` — exit the loop immediately when done. Without `break`, the loop would keep running all 12 times even after the indexer finishes.

This pattern is called **polling** — you keep checking a status until it reaches a finished state, instead of sleeping for a fixed time.

---

### `output_field_mappings` — why they are needed

When the skillset runs, it writes its results into the **document tree** — a temporary structure that exists during indexing:

```
/document/content       ← raw text from the blob
/document/entities      ← output of EntityRecognitionSkillV3
/document/keyphrases    ← output of KeyPhraseExtractionSkill
```

The indexer does NOT automatically move these into your index fields. You have to tell it explicitly with `output_field_mappings`:

```python
output_field_mappings=[
    FieldMapping(source_field_name="/document/entities", target_field_name="entities"),
    FieldMapping(source_field_name="/document/keyphrases", target_field_name="keyphrases"),
]
```

- `source_field_name` — where the value is in the document tree (skillset output)
- `target_field_name` — the field name in your index where it should be stored

Without these mappings, the skillset runs but the results are lost — they never make it into the index.

---

### Why we delete and recreate the indexer each run

Azure AI Search tracks which blobs the indexer has already processed (using timestamps). If you just update an existing indexer, it remembers it already processed your blobs and skips them — resulting in `docs: 0`.

Deleting and recreating the indexer resets this tracking state, forcing it to process all blobs again from scratch.

---

## Skillsets — Structure and How They Work

A skillset is a list of AI operations that run on each document during indexing. You define it once, attach it to an indexer, and Azure runs it automatically on every document it crawls.

### The overall structure

```python
skillset = SearchIndexerSkillset(
    name="my-skillset",        # you name the whole skillset
    skills=[                   # list of individual skills
        Skill1(...),
        Skill2(...),
    ]
)
```

The `name` is how the indexer knows which skillset to use — you reference it by name when creating the indexer.

### Every skill has inputs and outputs

Every single skill follows the same pattern:

```python
SomeSkill(
    inputs=[InputFieldMappingEntry(name="text", source="/document/content")],
    outputs=[OutputFieldMappingEntry(name="keyPhrases", target_name="keyphrases")]
)
```

**inputs** — where the skill reads from:
- `name` — what the skill expects to receive (defined by the skill — you can't change this)
- `source` — where to get the value. `/document/content` means the raw text of the document.

**outputs** — where the skill writes its result:
- `name` — what the skill produces (defined by the skill — you can't change this)
- `target_name` — the name you give it for the next step to use. This becomes available as `/document/keyphrases` for other skills or for field mapping into the index.

### The document tree — how data flows

Think of the document as a tree that grows as each skill adds to it:

```
/document                          ← the blob file
/document/content                  ← raw text (Azure extracts this automatically)
/document/entities                 ← added by EntityRecognitionSkillV3
/document/keyphrases               ← added by KeyPhraseExtractionSkill
```

Each skill reads from the tree and writes back to it. Skills run in sequence — a later skill can read the output of an earlier skill.

### Field mapping — from the document tree into the index

The indexer maps from the document tree into your index fields. If your `target_name` matches an index field name exactly, Azure maps it automatically. Otherwise you define explicit field mappings.

### Built-in skills vs custom skills

| Type | What it is | Examples |
|---|---|---|
| Built-in | Pre-built skills provided by Azure | `EntityRecognitionSkillV3`, `KeyPhraseExtractionSkill`, `OCRSkill`, `AzureOpenAIEmbeddingSkill` |
| Custom | An Azure Function you write that calls any API | Call Content Safety, call Translator, call your own model |

Custom skills are how you plug in Content Safety, a Translator call, or any other service into the indexing pipeline. The function receives a document chunk, does something to it, and returns the enriched result — exactly like a built-in skill.

### A real production skillset would look like this

```
skillset
  └── OCRSkill                      → extract text from scanned images
  └── EntityRecognitionSkillV3      → extract people, orgs, locations
  └── KeyPhraseExtractionSkill      → extract key phrases
  └── custom skill (Azure Function) → call Content Safety to flag harmful content
  └── custom skill (Azure Function) → call Translator to translate to English
  └── AzureOpenAIEmbeddingSkill     → generate vector embeddings for vector search
```

All of this runs automatically on every document the indexer finds — including new documents added later.

---

## Delete an Index

```python
index_client.delete_index("documents")
print("Index deleted")
```

Call this at the end of your script if you want to clean up. The index and all its documents are removed.

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `ResourceNotFoundError` | Index does not exist when searching | Create the index first before calling `search_client.search()` |
| `HttpResponseError 400` on filter | Field not `filterable=True` in schema | Add `filterable=True` to the field definition and recreate the index |
| `HttpResponseError 400` on facet | Field not `facetable=True` in schema | Add `facetable=True` to the field definition and recreate the index |
| `KeyError: 'id'` on upload result | Checking result wrong | Use `result[0].succeeded` and `result[0].key` not dict access |
| No results returned | Index just created — documents not yet indexed | Wait a second and retry — indexing is near-instant but not synchronous |
| `AuthenticationFailed` | Wrong key | Check `.env` — must use the admin key, not the query key (query key is read-only) |
