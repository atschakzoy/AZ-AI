# Knowledge Mining — Azure AI Search

A plain-English reference for Azure AI Search. Written so anyone can read it and learn.

---

## What is Azure AI Search

Every company has huge amounts of data locked in documents — PDFs, Word files, emails, images, SharePoint sites. This data is not searchable in any meaningful way. You might have a file share with 50,000 PDFs and no way to find the one you need.

**Azure AI Search is a managed search engine.** You load your documents into it, it indexes them, and then your app can search them instantly — just like Google, but for your own company data.

Beyond basic keyword matching, it supports:
- **Semantic search** — understands what you *mean*, not just the words you typed
- **Vector search** — searches by conceptual similarity using AI embeddings
- **AI enrichment** — automatically extracts entities, key phrases, translates, generates captions from images during indexing

This is the foundation of RAG (Retrieval-Augmented Generation). When you ask an AI assistant "what does our policy say about X?", Search is what finds the relevant chunks before the LLM reads them.

---

## The Core Architecture

```
Data source (Blob, SQL, Cosmos DB, SharePoint...)
    ↓
Indexer — crawls the data source and runs documents through the skillset
    ↓
Skillset — AI operations applied to each document during indexing
    ↓
Index — the searchable store (like a database table optimised for search)
    ↑
Search client — your app queries the index
```

The **index** is the thing your app talks to. Everything else is about getting data *into* the index.

---

## Key Concepts

| Concept | What it is |
|---|---|
| **Index** | The search database. Defines the schema (fields and their types). You query this. |
| **Document** | One record in the index. Could be one PDF file, one product, one knowledge base article. |
| **Field** | A property of a document. E.g. `title`, `content`, `category`, `embedding`. |
| **Indexer** | A crawler. Reads your data source, feeds each document through the skillset, writes results to the index. |
| **Data source** | Where your documents live: Azure Blob Storage, SQL Database, Cosmos DB, etc. |
| **Skillset** | A pipeline of AI operations. Applied to each document while the indexer is running. |

### File vs Document — they are not the same thing

This is one of the most common points of confusion.

**File** — the thing on disk. A PDF, Word doc, CSV. One physical file. Could be 50 pages long.

**Document** — one record in the search index. Has fields, has an `id`, is what gets returned in search results.

They are only the same if you upload a file whole as one index record. In RAG you chunk, so:

```
1 file → many chunks → many documents in the index
```

One 50-page PDF becomes 100 documents in the index, each holding 500 words. They all share the same `source_file` value but each has its own unique `id`, its own `content`, its own `entities`, its own `keyphrases`.

**Why RAG needs chunking:**

An LLM has a context limit — you cannot feed it a 50-page PDF. So you:

1. Split the PDF into chunks
2. Store each chunk as a separate index document
3. When a user asks a question, Search finds the 3–5 most relevant chunks
4. You feed only those chunks to the LLM — not the whole file

**How the `id` and `source_file` fields relate:**

```
policy.pdf  (one file, 50 pages)
    ↓ chunked into 5 pieces

id: "policy.pdf_chunk_1"   source_file: "policy.pdf"   content: "first 500 words..."
id: "policy.pdf_chunk_2"   source_file: "policy.pdf"   content: "next 500 words..."
id: "policy.pdf_chunk_3"   source_file: "policy.pdf"   content: "next 500 words..."
```

The `id` must be unique per chunk — not per file. If you used the filename as the `id`, all chunks from the same file would overwrite each other and only the last one would survive. The `source_file` field is what ties all the chunks back to the original file.

---

## Field Types and Behaviours

When you define an index schema, each field has a type and a set of behaviours:

| Behaviour | What it means | When to use |
|---|---|---|
| `searchable` | Full-text search can match against this field | Text fields you want to search (title, content) |
| `filterable` | Can use in `filter=` expressions | Category, status, date ranges — exact match |
| `sortable` | Can sort results by this field | Dates, prices, scores |
| `facetable` | Can aggregate counts by this field | Category, tag, region — for faceted navigation |
| `retrievable` | Returned in search results | All fields you want back in results |
| `key` | Unique identifier for the document | One field per index must be the key |

A field can have multiple behaviours. Example: `category` might be `filterable`, `facetable`, and `retrievable` — but not `searchable`.

### Field type classes — all four

There are four ways to define a field in the Azure Search SDK:

| Class | Searchable | Use for |
|---|---|---|
| `SimpleField` | No | IDs, categories, dates, numbers, flags — exact match, filter, sort |
| `SearchableField` | Yes | Free text — titles, content, descriptions — full-text search |
| `ComplexField` | — | Nested objects — a field that contains its own sub-fields |
| `SearchField` | Configurable | The raw base class — used when you need full control, e.g. vector fields |

`SimpleField` is exact-match only. Azure stores the value as-is and lets you filter or sort on it, but never breaks it into words for full-text search.

`SearchableField` tells Azure to tokenise the text (break it into words, handle plurals, case etc.) and build an inverted index so queries can match against it.

`ComplexField` is for nested structured objects — for example an address with street, city, and postcode as separate sub-fields inside one field:

```python
ComplexField(name="address", fields=[
    SimpleField(name="street", type=SearchFieldDataType.String),
    SimpleField(name="city", type=SearchFieldDataType.String, filterable=True),
    SimpleField(name="postcode", type=SearchFieldDataType.String),
])
```

`SearchField` is what the other three are built on top of. You use it directly only when you need options the shortcuts don't expose — the most common case being vector search, where you pass in a `VectorSearchProfile`. You will see this in stage 07.

Every index needs exactly one `SimpleField` with `key=True` — this is the unique document ID. All text content you want to search goes in `SearchableField`.

---

### Field names are yours to choose

Field names in the schema are completely up to you. `"id"`, `"content"`, `"entities"` are just names you picked. You could call them `"document_id"`, `"body"`, `"people_found"`. The only rule: the names must match between your schema and the documents you upload. Be consistent.

---

### Behaviours — you set them per field

Each field type has different defaults. You pass behaviours as arguments when you define the field.

**`SimpleField` — behaviours you can set:**

```python
SimpleField(
    name="category",
    type=SearchFieldDataType.String,
    filterable=True,   # off by default
    facetable=True,    # off by default
    sortable=True,     # off by default
    retrievable=True   # True by default
)
```

**`SearchableField` — behaviours you can set:**

```python
SearchableField(
    name="content",
    type=SearchFieldDataType.String,
    filterable=True,    # off by default
    sortable=True,      # off by default
    analyzer_name="en.microsoft"  # optional — language analyser
)
```

`searchable` is always on for `SearchableField` — that is the point of the class. You can optionally add `filterable` and `sortable` on top, but it costs more storage.

**The rule of thumb — only turn on what you actually need.**

Every behaviour you enable costs Azure more storage and processing. A field that is `searchable`, `filterable`, `facetable`, and `sortable` all at once is expensive — Azure has to maintain multiple data structures for it.

| Need | What to use |
|---|---|
| Text you search inside | `SearchableField` |
| Text you filter or group by | `SimpleField` with `filterable=True` / `facetable=True` |
| Unique document ID | `SimpleField` with `key=True` |
| Dates, numbers, status codes | `SimpleField` with `filterable=True` and/or `sortable=True` |

---

### `SearchFieldDataType` — all available types

| Type | Use for |
|---|---|
| `SearchFieldDataType.String` | Any text — IDs, names, content, categories |
| `SearchFieldDataType.Int32` | Whole numbers up to ~2 billion |
| `SearchFieldDataType.Int64` | Larger whole numbers |
| `SearchFieldDataType.Double` | Decimal numbers — prices, scores |
| `SearchFieldDataType.Boolean` | True / False — flags, active status |
| `SearchFieldDataType.DateTimeOffset` | Dates and times — `2024-01-15T00:00:00Z` format |
| `SearchFieldDataType.GeographyPoint` | Latitude/longitude — for location-based search |
| `SearchFieldDataType.ComplexType` | Nested objects — used inside `ComplexField` |
| `Collection(SearchFieldDataType.String)` | A list of strings — e.g. tags, key phrases |
| `Collection(SearchFieldDataType.Single)` | A list of floats — **used for embedding vectors in vector search** |

The one you will hit next is `Collection(SearchFieldDataType.Single)` — an embedding is an array of hundreds or thousands of decimal numbers, and this is the field type that holds it.

---

## Search Types

### Full-text search (keyword)

The classic approach. Splits your query into words, matches against indexed text. Scores results by how many times the terms appear, how rare the terms are (TF-IDF), and field boosts.

```
query: "resource group container"
→ finds documents containing any of: resource, group, container
→ scores higher if all three appear, especially in the title field
```

### Filtered search

Adds an exact-match condition on top of any search. Only returns documents where the filter is true.

```
filter: category eq 'compute'
```

### Faceted search

Returns *counts* per category value alongside your results. Used to build the "filter sidebar" in search UIs.

```
facets: ["category"]
→ returns: {"azure-basics": 3, "compute": 2, "networking": 5}
```

### Vector search

Instead of matching words, you convert your query to a vector (an array of numbers produced by an embedding model) and find documents whose vectors are closest. This finds *semantically similar* documents even if they use completely different words.

```
query: "how do I organise Azure resources?"
→ might find a document about "resource groups" even if the word "organise" never appears
```

Requires embedding vectors to be stored in the index alongside the text. Covered in Stage 07 (Azure OpenAI).

### Hybrid search

Runs full-text search and vector search at the same time, then fuses the rankings. Best of both worlds — catches exact keyword matches AND conceptual similarity.

---

## AI Enrichment — Skillsets

When your indexer crawls documents, you can run AI operations on each one before storing it in the index. The outputs of these operations become new fields in the index.

**Built-in skills:**

| Skill | What it does |
|---|---|
| `EntityRecognitionSkill` | Extracts people, organisations, locations |
| `KeyPhraseExtractionSkill` | Extracts key phrases |
| `SentimentSkill` | Adds a sentiment score |
| `LanguageDetectionSkill` | Detects the document's language |
| `TranslationSkill` | Translates content to another language |
| `OCRSkill` | Extracts text from images embedded in documents |
| `ImageAnalysisSkill` | Generates AI captions and tags for images |
| `AzureOpenAIEmbeddingSkill` | Generates vector embeddings — used for vector search |

**How it fits together:** a PDF gets indexed → OCR runs → text is extracted → EntityRecognitionSkill runs → people and organisations found → all of this stored in the index. Your app can now search by entity name even though the PDF was a scanned image.

---

## The Azure Resource

Azure AI Search is a **dedicated resource** — it is not covered by the multi-service (Foundry Tools) account.

- **Terraform resource:** `azurerm_search_service`
### SKUs — which one to pick

| SKU | Indexes | Storage | Replicas | Use for |
|---|---|---|---|---|
| `free` | 1 | 50MB | 1 | Learning only — no SLA, shared infrastructure, cannot scale |
| `basic` | 15 | 2GB per partition | up to 3 | Small production apps, low traffic |
| `standard` (S1) | 50 | 25GB per partition | up to 12 | Most production workloads — the default choice |
| `standard` (S2) | 200 | 100GB per partition | up to 12 | High volume — large document stores |
| `standard` (S3) | 200 | 200GB per partition | up to 12 | Very high volume |
| `storage_optimized` (L1/L2) | 10 | 1–2TB per partition | up to 12 | Massive data, cost-optimised for storage over speed |

**For AI-102 and learning:** `free` tier is enough.
**For a real production RAG app:** start with `standard` (S1) — it supports replicas (for availability) and partitions (for scale), and is the tier most Azure documentation assumes.

The free tier has no SLA — Azure makes no uptime guarantee. Basic and above have a 99.9% SLA.

### SDKs — how many are there

There is **one SDK package per language**, all wrapping the same underlying REST API:

| Language | Package |
|---|---|
| Python | `azure-search-documents` |
| .NET / C# | `Azure.Search.Documents` |
| JavaScript / TypeScript | `@azure/search-documents` |
| Java | `azure-search-documents` |

You only need one — whichever language you are using. In this project that is Python: `azure-search-documents`.

Underneath all of them is the **REST API** — if you ever need a feature the SDK doesn't expose yet, you can call the REST API directly with `requests` or `HttpRequest`, the same pattern you used in Content Safety.

### How the endpoint is built in Terraform

Unlike Cognitive Services resources where the endpoint is a direct attribute, `azurerm_search_service` does not expose the endpoint as an output. You build it yourself using string interpolation:

```hcl
output "endpoint" {
  value = "https://${azurerm_search_service.search.name}.search.windows.net"
}
```

The endpoint is always `https://<resource-name>.search.windows.net` — the resource name becomes the subdomain automatically. This is why `custom_subdomain_name` is not needed for Search (unlike Document Intelligence).

---

## Where Azure AI Search Is Mostly Used

| Industry / use case | How |
|---|---|
| **RAG pipelines** | Index documents → retrieve relevant chunks → pass to LLM to answer questions. This is the most common real-world use today. |
| **Enterprise intranet search** | Replace the broken company SharePoint search with a proper relevance-ranked engine |
| **E-commerce product search** | Search product catalogue by name, description, category, price range — with faceted navigation |
| **Legal / compliance** | Search thousands of contracts for specific clauses, parties, or dates |
| **Knowledge bases** | Support portals — "find me docs about this error message" |
| **Healthcare** | Search patient notes, research papers, clinical trials |
| **HR / recruitment** | Search CVs for skills, experience level, location |

---

## Azure AI Search vs SQL vs Vector Databases

A common question — where does Azure AI Search fit compared to other data stores?

```
SQL database     → exact match, structured rows, no AI, no relevance ranking
Azure AI Search  → relevance ranking, full-text search, AI enrichment, optional vector search
Vector database  → pure semantic similarity, embeddings only, no keyword matching
```

Azure AI Search sits in the middle. It can do:
- Keyword search like SQL
- Vector/semantic search like a dedicated vector database (Pinecone, Weaviate, Qdrant)
- AI enrichment during indexing (entities, key phrases, embeddings)

**You do not need a separate vector database** if you're using Azure AI Search. Vector search is built in — you define a vector field in your index, store embeddings there, and search by similarity. All inside the same service.

This is why Azure AI Search is the standard choice for RAG pipelines on Azure — keyword search + vector search + AI enrichment in one place, no extra infrastructure needed.

---

## Real-World Usage — How It Actually Works

### The index schema reflects your data

In a real app you design the schema around your data, not around a tutorial. First ask:
- What do I need to **search** on? → `searchable`
- What do I need to **filter** on? → `filterable`
- What do I need to **count/group** on? → `facetable`
- What do I need to **get back** in results? → `retrievable`

Example — a support knowledge base:

```python
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="title", type=SearchFieldDataType.String),
    SearchableField(name="body", type=SearchFieldDataType.String),
    SimpleField(name="product", type=SearchFieldDataType.String, filterable=True, facetable=True),
    SimpleField(name="last_updated", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
]
```

Every project gets a different schema designed for its data.

### Where real data comes from — two approaches

| Approach | How | When to use |
|---|---|---|
| **SDK upload** (`upload_documents`) | You fetch data yourself (from a DB, API, files) and push it | Custom pipelines, scheduled batch jobs, RAG ingestion |
| **Indexer + Data source** | You point Azure at Blob Storage, SQL, or Cosmos DB — Azure crawls it automatically on a schedule | Large document stores where you don't want to write a crawler |

### Field names are yours to choose

Field names in the schema are completely up to you — `"id"`, `"content"`, `"entities"` are just names you picked. You could call them `"document_id"`, `"body"`, `"people_found"`. The only rule: the names must match between your schema and the documents you upload. Be consistent.

---

### Can you use Document Intelligence instead of the indexer?

No — they do different jobs. You use both together, not one instead of the other.

- **Document Intelligence** — extracts content from a file. Reads a PDF or image and gives you back structured text, tables, key-value pairs. It has no concept of search or storing anything.
- **Azure AI Search indexer** — moves content into the search index. Crawls a data source, runs skills, writes into the index. It does not extract complex document structure.

```
Document Intelligence
    → extracts clean text and tables from complex PDFs
        ↓
Your code chunks the text
        ↓
Azure AI Search indexer (or SDK upload)
    → stores chunks in the index, runs skillset, makes it searchable
```

**When the indexer alone is enough:** plain text, simple Word docs, CSVs — the indexer's built-in document cracking handles these.

**When you need Document Intelligence first:**
- Scanned PDFs (images — the indexer can't read them without OCR)
- PDFs with tables you want to preserve as structured data
- Forms where you need specific fields extracted (invoice number, total, etc.)

---

### The stage 06 scripts are for small data — here is what production looks like

What you built in stage 06 is the learning version — enough to understand how all the pieces work. The concepts are exactly right; the scale is small.

| Thing | Stage 06 | Production |
|---|---|---|
| Schema | Designed manually per project | Flat chunk schema, works for any file |
| Data volume | A few files | Thousands to millions of chunks |
| Indexer trigger | Run manually | Scheduled or event-triggered |
| Document cracking | Indexer handles simple files | Document Intelligence for complex PDFs |
| Chunking | Not done — full document per record | Split into 500–1000 word chunks |
| Vector field | Not included | Always included for hybrid search |
| Skillset | Entity + key phrase | Entity + key phrase + OCR + embedding |

---

### The universal schema — works for 50,000 mixed files

You do not need to know every document's internal structure. You chunk every file into pieces of text, and every chunk becomes one document in the index with the same fixed schema:

```python
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SimpleField(name="source_file", type=SearchFieldDataType.String, filterable=True),
    SimpleField(name="page_number", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SearchableField(name="entities", type=SearchFieldDataType.String),
    SearchableField(name="keyphrases", type=SearchFieldDataType.String),
    # later: Collection(SearchFieldDataType.Single) for the embedding vector
]
```

The schema never changes no matter how many files you have. Every chunk from every file — PDF, Excel, CSV, Word — goes into the same fields.

**You only need a custom schema when your data is structured** — like a product catalogue where every item has a price, SKU, and category and you need to filter by price. For unstructured documents, the flat chunk schema handles everything.

---

### RAG pipeline pattern — how Search fits in

This is the most common real-world use of Azure AI Search today:

```
PDF / Word files
    ↓
Document Intelligence (prebuilt-layout) — extract text, preserve table structure
    ↓
Chunk the text — split into paragraphs or fixed-size chunks
    ↓
Upload each chunk as one document to Search
    ↓
User asks a question → Search finds the relevant chunks → LLM reads them and answers
```

Each chunk in the index gets fields like:
- `id` — unique chunk ID
- `content` — the chunk text
- `source_file` — which PDF it came from
- `page_number` — where in the document it was
- `content_vector` — the embedding (for vector search, Stage 07)

The index schema is always designed first — look at your data and decide what you need to search, filter, and retrieve. Same thinking as designing a database table.

---

## AI-102 Exam — Key Points

- Azure AI Search requires a **dedicated resource** — not covered by the multi-service account.
- Know the difference: **index** (the schema + data), **indexer** (the crawler), **skillset** (AI pipeline), **data source** (where data comes from).
- Field behaviours: `searchable`, `filterable`, `facetable`, `sortable`, `retrievable`, `key` — know what each one means.
- **Vector search** requires embedding vectors stored in the index — generated by an embedding model (Azure OpenAI).
- **Hybrid search** = keyword + vector at the same time.
- **`@search.score`** — higher means more relevant. In full-text search this is a TF-IDF-based score. In vector search it is a cosine similarity score.
- **AI enrichment** happens at indexing time, not query time — the skills run on the indexer pass, and the results are stored in the index.
- `AzureOpenAIEmbeddingSkill` generates vectors during indexing — this is how you automate vector field population.
- Free tier: 1 index, 50MB — enough for learning.
