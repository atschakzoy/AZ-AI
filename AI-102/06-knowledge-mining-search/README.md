# Stage 06 — Knowledge Mining & Azure AI Search

## What is this and why does it matter?

Most enterprise data lives in unstructured documents — PDFs, Word files, emails, images, SharePoint. Azure AI Search lets you index all of it, enrich it with AI (extract entities, translate, generate embeddings), and make it searchable with both keyword and semantic/vector search.

This is the foundation for RAG (Retrieval-Augmented Generation) — the technique used in Stage 08 to make LLMs answer questions from your own documents.

---

## What you will learn

- What Azure AI Search is and how it works
- Creating an index, indexer, and data source
- AI enrichment — applying AI skills during indexing
- Full-text search and filters
- Semantic search (ranking by meaning, not just keyword match)
- Vector search (searching by embedding similarity)
- Calling Azure AI Search from Python

---

## Part 1 — How Azure AI Search Works

```
Data source (Blob, SQL, Cosmos DB)
    ↓
Indexer — reads documents and feeds them through the skillset
    ↓
Skillset — AI enrichment (extract entities, translate, generate descriptions)
    ↓
Index — the searchable store (like a database table optimised for search)
    ↑
Search client — your app queries the index
```

**Key concepts:**

| Concept | What it is |
|---------|-----------|
| **Index** | The search database — defines fields and their types |
| **Document** | One record in the index (e.g. one PDF file) |
| **Field** | A property of a document (title, content, entities, embedding) |
| **Indexer** | A crawler that reads data from a source and populates the index |
| **Data source** | Where your documents live (Azure Blob, SQL, Cosmos DB, etc.) |
| **Skillset** | A pipeline of AI operations applied during indexing |

---

## Part 2 — Creating an Index with the Python SDK

```bash
pip install azure-search-documents azure-identity
```

```python
import os
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchField, SearchableField,
    SearchFieldDataType, VectorSearch, HnswAlgorithmConfiguration,
    VectorSearchProfile
)
from azure.identity import DefaultAzureCredential

index_client = SearchIndexClient(
    endpoint=os.environ["SEARCH_ENDPOINT"],
    credential=DefaultAzureCredential()
)

# Define index schema
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="title", type=SearchFieldDataType.String),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
    SearchField(
        name="content_vector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile_name="myHnsw"
    )
]

# Vector search configuration
vector_search = VectorSearch(
    algorithms=[HnswAlgorithmConfiguration(name="myHnsw")],
    profiles=[VectorSearchProfile(name="myHnsw", algorithm_configuration_name="myHnsw")]
)

index = SearchIndex(name="documents", fields=fields, vector_search=vector_search)
index_client.create_or_update_index(index)
print("Index created")
```

---

## Part 3 — Uploading Documents

```python
from azure.search.documents import SearchClient

search_client = SearchClient(
    endpoint=os.environ["SEARCH_ENDPOINT"],
    index_name="documents",
    credential=DefaultAzureCredential()
)

documents = [
    {
        "id": "1",
        "title": "Azure Resource Groups",
        "content": "A resource group is a container that holds related resources for an Azure solution.",
        "category": "azure-basics"
    },
    {
        "id": "2",
        "title": "Azure App Service",
        "content": "Azure App Service is a fully managed platform for building web apps and APIs.",
        "category": "compute"
    }
]

result = search_client.upload_documents(documents)
print(f"Uploaded {len(result)} documents")
```

---

## Part 4 — Searching

**Full-text search:**

```python
results = search_client.search(
    search_text="resource group container",
    select=["id", "title", "content"],
    top=5
)

for result in results:
    print(f"Score: {result['@search.score']:.2f} | {result['title']}")
    print(f"  {result['content'][:100]}...")
```

**Filtered search:**

```python
results = search_client.search(
    search_text="app",
    filter="category eq 'compute'",
    select=["title", "content"]
)
```

**Faceted search (get counts per category):**

```python
results = search_client.search(
    search_text="*",
    facets=["category"],
    select=["title"]
)
for facet in results.get_facets()["category"]:
    print(f"{facet['value']}: {facet['count']}")
```

---

## Part 5 — Vector Search (Semantic Similarity)

Vector search finds documents that are *conceptually similar* to a query, even if they use different words. This requires generating embeddings — numerical representations of text.

```python
from openai import AzureOpenAI

# Generate embedding for the query
openai_client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-02-01"
)

def get_embedding(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

from azure.search.documents.models import VectorizedQuery

query_vector = get_embedding("how do I organise Azure resources?")

results = search_client.search(
    search_text=None,
    vector_queries=[
        VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=3,
            fields="content_vector"
        )
    ]
)

for result in results:
    print(f"Score: {result['@search.score']:.4f} | {result['title']}")
```

**Hybrid search (keyword + vector together):**

```python
results = search_client.search(
    search_text="organise resources",  # keyword component
    vector_queries=[
        VectorizedQuery(vector=query_vector, k_nearest_neighbors=3, fields="content_vector")
    ]
)
```

---

## Part 6 — AI Enrichment with Skillsets

During indexing, you can apply AI skills to enrich your documents. The enriched fields are stored in the index.

**Common built-in skills:**

| Skill | What it does |
|-------|-------------|
| `EntityRecognitionSkill` | Extracts people, organisations, locations |
| `KeyPhraseExtractionSkill` | Extracts key phrases |
| `SentimentSkill` | Adds sentiment score |
| `LanguageDetectionSkill` | Detects the document's language |
| `TranslationSkill` | Translates content |
| `OCRSkill` | Extracts text from images in documents |
| `ImageAnalysisSkill` | Adds AI-generated captions and tags to images |
| `AzureOpenAIEmbeddingSkill` | Generates vector embeddings during indexing |

---

## AI-102 Exam Checklist — Knowledge Mining

- [ ] What is the difference between an index, an indexer, and a skillset?
- [ ] What is a data source in Azure AI Search?
- [ ] What fields are `filterable`, `facetable`, and `searchable`? What is the difference?
- [ ] What is vector search and why is it better than keyword search for semantic queries?
- [ ] What is an embedding and how do you generate one?
- [ ] What is hybrid search?
- [ ] What does `AzureOpenAIEmbeddingSkill` do during indexing?
- [ ] What is the `@search.score` and what does a higher score mean?

---

## Exercises

1. Create a search index with text and vector fields. Upload 10 documents on different Azure topics.
2. Perform a keyword search and print the top 5 results with their scores.
3. Generate embeddings for your documents using Azure OpenAI and store them in the vector field.
4. Perform a vector search: ask "what is serverless computing?" and return the top 3 most similar documents.
5. Combine keyword and vector search (hybrid). Compare the results to each individual method.
