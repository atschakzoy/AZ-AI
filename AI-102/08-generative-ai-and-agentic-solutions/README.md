# Stage 08 — Generative AI Solutions & Agentic Solutions

## What is this and why does it matter?

This final stage covers two things: RAG (building a grounded AI that answers from your documents) and Agentic Solutions (building agents that plan and take multi-step actions). Together these map to ~20% of the AI-102 exam.

---

## What you will learn

- What RAG is and building a complete RAG pipeline
- Using Azure AI Search as the retrieval layer
- Optimising RAG with prompt engineering
- What fine-tuning is and when to use it
- Microsoft Foundry Agent Service — creating and running agents
- Multi-agent orchestration patterns
- Deploying AI apps to Azure Container Apps

---

## Part 1 — RAG (Retrieval-Augmented Generation)

**The problem:** LLMs only know their training data. They hallucinate when asked about your private documents.

**The solution — RAG:**

```
User question
    ↓
Search your documents (Azure AI Search) → retrieve top 3 relevant chunks
    ↓
Build a prompt: "Answer using ONLY these documents: [chunks]"
    ↓
LLM generates a grounded answer
    ↓
Return answer + source citations
```

**Complete RAG pipeline:**

```python
import os
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)

openai_client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_ad_token_provider=token_provider,
    api_version="2024-12-01-preview"
)

search_client = SearchClient(
    endpoint=os.environ["SEARCH_ENDPOINT"],
    index_name="documents",
    credential=DefaultAzureCredential()
)

def get_embedding(text: str) -> list[float]:
    return openai_client.embeddings.create(
        model="text-embedding-ada-002", input=text
    ).data[0].embedding

def retrieve(question: str, top_k: int = 3) -> list[dict]:
    # Hybrid search — combines keyword matching AND vector similarity in one call
    # Keyword search catches exact terms ("Azure OpenAI", product codes, names)
    # Vector search catches meaning ("how do I deploy?" matches "deployment guide")
    # Hybrid is almost always better than either alone
    results = search_client.search(
        search_text=question,             # keyword component
        vector_queries=[VectorizedQuery(
            vector=get_embedding(question),
            k_nearest_neighbors=top_k,
            fields="content_vector"       # vector component — field that stores the embedding
        )],
        select=["id", "title", "content"],
        top=top_k,
        query_type="semantic",            # re-rank results by meaning after retrieval
        semantic_configuration_name="default"  # must be configured on the index
    )
    return [{"id": r["id"], "title": r["title"], "content": r["content"]} for r in results]

# Why three ranking layers?
#   1. Keyword search  — BM25 algorithm, fast, catches exact matches
#   2. Vector search   — cosine similarity, catches meaning even with different words
#   3. Semantic rerank — a separate language model re-reads the top results and reorders
#                        them by true relevance to the question. Most expensive but most accurate.

def answer(question: str) -> dict:
    chunks = retrieve(question)
    context = "\n\n".join(
        f"[Source {i+1}: {c['title']}]\n{c['content']}"
        for i, c in enumerate(chunks)
    )
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Answer using ONLY the provided sources. "
                           "If the answer is not there, say so. Always cite the source number."
            },
            {"role": "user", "content": f"Sources:\n{context}\n\nQuestion: {question}"}
        ],
        temperature=0.1
    )
    return {
        "answer": response.choices[0].message.content,
        "sources": [{"title": c["title"]} for c in chunks]
    }
```

---

## Part 2 — Optimising RAG

**Prompt engineering for RAG:**
- Set `temperature=0.1` — factual answers need consistency, not creativity
- Explicitly tell the model to cite sources — `[Source 1]`, `[Source 2]`
- Tell the model to say "I don't know" if the answer is not in the sources (prevents hallucination)
- Ground the model hard: "Answer using ONLY the provided sources. Do not use your general knowledge."

**Improving retrieval:**
- Use **hybrid search** (keyword + vector + semantic reranking) — the Part 1 retrieve function does all three
- Increase `top_k` if answers are incomplete — retrieve more chunks
- Chunk documents well — too small = missing context, too large = diluted relevance. 300–500 tokens per chunk is a common starting point.
- Overlap chunks by ~50 tokens — so a sentence that falls on a boundary appears in both chunks

**Evaluating RAG quality:**

| Metric | What it measures | How to check it |
|--------|----------------|----------------|
| **Groundedness** | Is the answer supported by the retrieved chunks? | Content Safety Groundedness Detection (Stage 02) |
| **Relevance** | Did retrieval return the right documents? | Manual review — does the source actually contain the answer? |
| **Faithfulness** | Did the model stick to the sources or add extra knowledge? | Compare answer against chunks — any facts not in the chunks? |
| **Answer quality** | Is the answer accurate and complete? | Human evaluation or LLM-as-judge |

**RAG evaluation in code — using LLM-as-judge:**

```python
def evaluate_groundedness(answer: str, chunks: list[dict]) -> dict:
    # Use GPT-4o itself to check whether the answer is grounded in the sources
    # This pattern is called "LLM-as-judge" — use the model to evaluate model output
    context = "\n\n".join(f"[Source {i+1}]: {c['content']}" for i, c in enumerate(chunks))

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are a grounding evaluator.
Given an answer and the source documents it was generated from, determine:
1. Is every claim in the answer supported by the sources? (grounded: true/false)
2. Which specific claims are NOT supported, if any?
Respond in JSON: {"grounded": true/false, "unsupported_claims": ["...list..."]}"""
            },
            {
                "role": "user",
                "content": f"Sources:\n{context}\n\nAnswer to evaluate:\n{answer}"
            }
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    import json
    return json.loads(response.choices[0].message.content)

# Usage
result = answer("What are the Azure OpenAI pricing tiers?")
evaluation = evaluate_groundedness(result["answer"], result["sources"])

if not evaluation["grounded"]:
    print("WARNING — answer contains unsupported claims:")
    for claim in evaluation["unsupported_claims"]:
        print(f"  - {claim}")
```

---

## Part 2b — When to Use a Smaller Model

GPT-4o is the best model but also the most expensive. In a real production app, not every task needs GPT-4o.

**Model selection guide:**

| Task | Right model |
|---|---|
| Complex reasoning, nuanced answers | GPT-4o |
| Simple extraction, classification | GPT-4o mini (cheaper, faster) |
| Embedding generation | `text-embedding-3-small` |
| Grounding / evaluation (internal) | GPT-4o mini |
| Voice / real-time (latency critical) | GPT-4o mini or GPT-4o Realtime |

**GPT-4o mini** — a smaller, much cheaper version of GPT-4o. Use it for:
- Tasks in the hot path of an API (every request → every millisecond matters)
- Internal evaluation calls (you are calling the model to check another model's output)
- Simple classification or routing tasks

**Rule of thumb:** Design with GPT-4o, then ask "does this specific step actually need a frontier model?" For anything that is not the main answer generation, switch to mini.

---

## Part 3 — Fine-Tuning

Fine-tuning trains the model further on your own data to change its default behaviour.

**When to fine-tune:**
- You need a very specific tone or format that prompt engineering alone cannot achieve
- You have thousands of examples of the exact input/output you want
- You need to reduce prompt length (fine-tuning teaches the model so you don't need long examples)

**When NOT to fine-tune:**
- You need up-to-date information → use RAG instead
- You just want the model to follow instructions → use a system message
- You don't have enough examples (need hundreds to thousands)

**Fine-tuning in Azure OpenAI:**
```python
# Training data format (JSONL)
# {"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}

# Submit fine-tuning job via portal or SDK
# The result is a new deployment you call by its custom model name
```

---

## Part 4 — Microsoft Foundry Agent Service

The Foundry Agent Service lets you build agents that plan and take multi-step actions using tools.

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    CodeInterpreterTool,
    FileSearchTool,
    FunctionTool
)
from azure.identity import DefaultAzureCredential
import json

client = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential()
)

# Define a custom function tool
def get_weather(location: str) -> str:
    return json.dumps({"location": location, "temperature": "22°C", "condition": "Sunny"})

functions = FunctionTool(functions=[get_weather])

# Create the agent
agent = client.agents.create_agent(
    model="gpt-4o",
    name="assistant",
    instructions="You are a helpful assistant. Use tools when you need information.",
    tools=functions.definitions + CodeInterpreterTool().definitions
)

# Create a thread and run
thread = client.agents.create_thread()
client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content="What is the weather in London and what is 15% of 2450?"
)

run = client.agents.create_and_process_run(
    thread_id=thread.id,
    agent_id=agent.id
)

messages = client.agents.list_messages(thread_id=thread.id)
for msg in reversed(messages.data):
    if msg.role == "assistant":
        print(msg.content[0].text.value)
```

---

## Part 5 — Multi-Agent Orchestration

A single agent can only do so much. Complex tasks benefit from multiple specialised agents working together.

**Common pattern — Sequential (pipeline):**
```
User request → Planner agent → Research agent → Writer agent → Review agent → Final output
```

**Common pattern — Parallel:**
```
User request → Orchestrator
                ├── Agent A (handles subtask 1)
                ├── Agent B (handles subtask 2)
                └── Agent C (handles subtask 3)
               → Combine results → Final output
```

**In Foundry — connecting agents:**

```python
# Agent A — researcher
researcher = client.agents.create_agent(
    model="gpt-4o",
    name="researcher",
    instructions="You research topics using file search.",
    tools=FileSearchTool(file_ids=[uploaded_file_id]).definitions
)

# Agent B — writer (receives researcher's output as context)
writer = client.agents.create_agent(
    model="gpt-4o",
    name="writer",
    instructions="You write clear summaries based on research provided to you."
)

# Orchestrate manually
research_result = run_agent(researcher, "Research Azure Container Apps pricing")
final_summary = run_agent(writer, f"Summarise this research:\n{research_result}")
```

---

## Part 6 — Deploying to Azure Container Apps

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and push to ACR
az acr build --registry myregistry --image ai-api:latest .

# Deploy to Container Apps with Managed Identity
az containerapp create \
  --name ca-ai-api \
  --resource-group rg-ai-prod \
  --environment cae-prod \
  --image myregistry.azurecr.io/ai-api:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 5 \
  --system-assigned \
  --env-vars \
    FOUNDRY_PROJECT_ENDPOINT=https://... \
    SEARCH_ENDPOINT=https://...

# Grant RBAC roles to the container app's identity
APP_PRINCIPAL=$(az containerapp show --name ca-ai-api --resource-group rg-ai-prod --query "identity.principalId" -o tsv)

az role assignment create \
  --assignee $APP_PRINCIPAL \
  --role "Foundry User" \
  --scope /subscriptions/.../resourceGroups/rg-ai-prod

az role assignment create \
  --assignee $APP_PRINCIPAL \
  --role "Search Index Data Reader" \
  --scope /subscriptions/.../searchServices/search-myapp
```

---

## AI-102 Exam Checklist — Generative AI & Agentic Solutions

- [ ] What problem does RAG solve?
- [ ] What are the three steps in a RAG pipeline?
- [ ] Why set temperature low (0.1) for RAG?
- [ ] What is the difference between RAG and fine-tuning?
- [ ] When should you fine-tune vs use RAG?
- [ ] What is hybrid search? What three ranking layers does it combine?
- [ ] What is "semantic reranking" and how is it different from vector search?
- [ ] What is LLM-as-judge and when would you use it to evaluate RAG?
- [ ] What are the three groundedness/quality metrics for RAG? (groundedness, relevance, faithfulness)
- [ ] When would you use GPT-4o mini instead of GPT-4o?
- [ ] What is the Foundry Agent Service?
- [ ] What three tools can you give a Foundry agent (code interpreter, file search, function)?
- [ ] What is a thread in the agent API?
- [ ] What is multi-agent orchestration and name two patterns (sequential, parallel)?
- [ ] What RBAC roles does the deployed app need? (Foundry User, Search Index Data Reader)
- [ ] What does `create_and_process_run` do?

---

## Exercises

1. Build the complete RAG pipeline using hybrid search (keyword + vector). Index 10 documents. Test with 5 questions and print sources.
2. Add LLM-as-judge groundedness evaluation to your RAG pipeline. Print a warning when the answer contains unsupported claims.
3. Compare GPT-4o and GPT-4o mini on the same 5 RAG questions. Note any quality difference. Count tokens used.
4. Create a Foundry Agent with the Code Interpreter tool. Ask it a maths question and a data analysis question.
5. Add a custom function tool to your agent (e.g. `get_stock_price(ticker)`). Verify the agent calls it when asked.
6. Build a two-agent pipeline: Agent A searches your indexed documents, Agent B summarises the results.
7. Wrap in FastAPI. Deploy to Azure Container Apps with Managed Identity. Assign all required RBAC roles.
