# Azure OpenAI Service — Theory and Concepts

A plain-English reference for Azure OpenAI. Written so anyone can read it and learn.

---

## What is Azure OpenAI

Azure OpenAI is Microsoft's managed API for OpenAI's models — GPT-4o, embeddings, DALL-E — running inside Azure. You get the same models as OpenAI.com but:

- Your data stays in your Azure region — it is never used to train OpenAI's models
- Authentication uses Azure identity (Managed Identity, RBAC) — no shared API keys floating around
- You stay inside your existing Azure subscription, compliance boundary, and private network

This is the standard choice for enterprise AI work on Azure. For AI-102, it is the service that ties everything together — especially for RAG (Retrieval-Augmented Generation).

---

## The Two-Layer Architecture

Azure OpenAI has two separate things you must set up before you can call a model:

```
1. The Azure OpenAI resource  →  your account inside Azure
2. A deployment               →  a specific model version running inside that resource
```

When you call the API, you always call a **deployment name**, not a model name. This is a key difference from OpenAI.com.

```python
# On OpenAI.com: you pass the actual model name
model="gpt-4o"

# On Azure OpenAI: you pass YOUR deployment name (which points to gpt-4o internally)
model="my-gpt4o-deployment"  # whatever name YOU chose when you deployed the model
```

Why this matters: you might have two deployments of the same model — one for production with high capacity, one for testing with low capacity. The deployment name lets you control this.

---

## Models Available

| Model | Use for |
|---|---|
| `gpt-4o` | Chat, reasoning, text tasks, structured outputs, vision |
| `gpt-4o-mini` | Same capabilities, cheaper, faster — use for simple tasks |
| `text-embedding-3-small` | Generating embeddings (vectors) for semantic search |
| `text-embedding-3-large` | Higher accuracy embeddings — use when precision matters |
| `text-embedding-ada-002` | Legacy — only use to match vectors you already have |
| `dall-e-3` | Image generation from text |

**Recommendation:** Use `gpt-4o` for chat tasks and `text-embedding-3-small` for embeddings. Do not use `ada-002` for new projects.

---

## SKUs and Deployment Types

Azure OpenAI has two separate SKU decisions:

**For the resource itself** (`azurerm_cognitive_account`):
- `S0` — the only option. There is no free tier for Azure OpenAI.

**For each model deployment** (`azurerm_cognitive_deployment`):

| Deployment SKU | What it is | When to use |
|---|---|---|
| `Standard` | Pay per token, no commitment | Learning, development, variable workloads |
| `GlobalStandard` | Same pay-per-token, Azure routes across regions | Production apps needing high availability |
| `ProvisionedManaged` | Reserved capacity — fixed monthly fee for guaranteed throughput (PTU units) | High-volume production (50M+ tokens/month) |
| `GlobalProvisionedManaged` | Same as above but globally routed | Large-scale production |

For learning: always use `Standard`. `ProvisionedManaged` has a minimum commitment and is expensive — it exists for enterprises with predictable high volume.

The `capacity` field on a `Standard` deployment is a **rate limit** (tokens per minute), not a cost. Setting `capacity = 10` means 10,000 tokens per minute maximum throughput. You only pay for tokens you actually use.

### Capacity limits and best practices

`capacity = 1` equals 1,000 tokens per minute. The default Azure quota in `eastus` for GPT-4o is **150K TPM** (`capacity = 150`) — you can request higher from Microsoft, but it is shared across all deployments in that subscription and region.

| Scenario | Capacity | Notes |
|---|---|---|
| Learning / dev | `10` | Prevents accidental overuse, near-zero cost |
| Internal tool, small team | `50` | Handles dozens of concurrent requests comfortably |
| Normal production SaaS | `100–150` | Typical for a B2B app with moderate traffic |
| High demand (consumer app) | Multiple deployments + load balancer | A single Standard deployment throttles at scale |

**Production pattern for high demand:**
1. Deploy 2–3 `GlobalStandard` deployments across regions
2. Put Azure API Management (APIM) in front as a load balancer
3. APIM round-robins requests and retries automatically on `429` (rate limit hit)
4. If volume is very predictable and consistently high, switch to `ProvisionedManaged` (PTU) — flat monthly rate, guaranteed throughput, no throttling

---

## Key Concepts

### Tokens

Everything you send and receive is measured in tokens. One token ≈ 0.75 words in English.

- Input tokens (your messages) cost money
- Output tokens (the model's response) cost money
- `max_tokens` controls the maximum number of output tokens
- `usage.total_tokens` in the response tells you how many were used

Why this matters: a model has a **context window** — the maximum total tokens it can process at once. If your conversation history gets too long, you hit the limit and the model forgets the earliest messages.

### Temperature

Controls how creative (random) the model is.

| Value | Behaviour | Use when |
|---|---|---|
| `0.0` | Fully deterministic — same input always gives same output | Classification, data extraction, structured tasks |
| `0.3` | Mostly deterministic, small variation | Q&A, technical explanations |
| `0.7` | Balanced | General chat |
| `1.0` | Creative, varied | Writing, brainstorming |

For business applications — extraction, classification, structured outputs — use `temperature=0` or close to it.

### Roles in a conversation

Every message you send has a `role`:

| Role | What it is | When it is used |
|---|---|---|
| `system` | Invisible instructions to the model | Set at the start — defines how the model should behave |
| `user` | The human's message | What the user typed |
| `assistant` | The model's reply | What the model said — you append this to keep conversation history |
| `tool` | Result of a function call | Sent back to the model after you run a tool it requested |

---

## Chat Completion

The core feature. You send a list of messages and the model replies.

### Statelessness — the model has no memory

The model has **no memory** — it does not remember previous conversations. Every API call is completely independent. To implement multi-turn chat, you must manually append each message and reply to the `messages` list and send the full history every time.

```
Turn 1:
  messages = [system, user1]  →  reply1

Turn 2:
  messages = [system, user1, reply1, user2]  →  reply2

Turn 3:
  messages = [system, user1, reply1, user2, reply2, user3]  →  reply3
```

**What this means in practice:**

- Every single API call sends ALL previous messages from scratch — not just the latest one
- A 20-turn conversation sends 20 messages on turn 20, not 1
- Cost grows with every turn because input tokens include the full history
- If the conversation grows past the model's context window limit, the oldest messages must be dropped or summarised

**Real-life example — customer support bot:**

A user starts a chat on your website. They ask 10 questions about their order. By question 10, every API call is sending the full transcript of all 9 previous turns plus the new one. If 1,000 customers are chatting at the same time, that is a lot of tokens — and cost — per request. This is why production apps:
- Summarise conversation history when it gets long ("truncate and summarise")
- Store the summary and use that instead of the raw transcript
- Set a maximum conversation length after which a new session begins

**What looks like "memory" in tools like Claude Code or ChatGPT:**

Those tools inject notes, project files, and compressed summaries into the context window at the start of every call. The model still has no internal memory — it just starts each turn with more context already loaded. The "memory" is in the files and messages, not in the model itself.

---

## Prompt Engineering

Prompt engineering is the skill of writing messages that reliably produce useful outputs. The most important thing is the **system message** — it sets the rules for every turn.

### System message design

A good system message:
- Defines the model's role ("You are a customer support agent for...")
- Sets constraints ("Only answer questions about our product")
- Defines the output format ("Always reply in JSON with fields: answer, confidence")
- Handles edge cases ("If you do not know, say 'I don't have that information'")

### Zero-shot vs Few-shot

| Technique | What it means | When to use |
|---|---|---|
| Zero-shot | No examples — just the instruction | Simple, well-defined tasks |
| Few-shot | Include 2–5 examples of input → correct output | Complex formatting, classification, any task where showing is faster than explaining |

### Chain of thought

Adding "Think step by step" to a prompt forces the model to reason before answering. This reliably improves accuracy on logic, maths, and multi-step reasoning problems.

---

## Streaming

By default, the API returns the full response at once — you wait, then everything arrives. With streaming, tokens arrive as they are generated — exactly like the typing effect on ChatGPT.

Why you want this in real apps:
- Users see something happening immediately — better perceived performance
- Long responses do not time out
- You can cancel early if the user types a new message

---

## Function Calling

Function calling lets the model decide to call one of your Python functions mid-conversation.

The flow:
1. You tell the model what functions exist (their names, descriptions, parameters)
2. The model decides whether to call one based on the user's message
3. If it wants to call a function, it returns a structured request — it does NOT call it itself
4. Your code calls the actual function and sends the result back
5. The model uses the result to form its final reply

### Real-world use cases

**1. Live data lookup**
User asks "what's my account balance?" — model calls `get_account_balance(user_id)` which hits your database and returns the real number. Without function calling, the model would guess or refuse. With it, the answer is always accurate and live.

**2. Taking actions**
User says "book me a meeting tomorrow at 3pm" — model calls `create_calendar_event(date, time, title)` which calls the Outlook or Google Calendar API and actually creates the event. The model decided what to do; your function did the work.

**3. Multi-step agent**
User says "find all my Azure VMs not used in 30 days and tell me their cost" — model calls `list_vms()`, gets the list, then calls `get_vm_metrics(vm_id)` for each one, then `get_vm_cost(vm_id)`, then writes a summary. You didn't write any routing logic — the model decided the steps on its own.

**4. Customer support bot**
User says "my order hasn't arrived" — model calls `get_order_status(order_id)` which hits your order system, gets real tracking data, and answers with actual shipping info instead of a generic reply.

**5. RAG with smart routing**
User asks a question — model decides whether to call `search_knowledge_base(query)`, `get_live_pricing(product)`, or `escalate_to_human()` based on what the question actually needs. You don't write any `if/else` routing logic — the model routes itself.

**The key value:** without function calling you would have to write `if "balance" in question: ... elif "book meeting" in question: ...` for every possible intent. Function calling replaces all of that — the model reads the question and picks the right function itself.

### How to think about function calling — the manager analogy

Imagine you are a manager. You have an assistant (the model) and an employee (your Python function). The assistant cannot talk to the employee directly — only you can.

1. A customer asks: *"How many resources are in rg-production?"*
2. You pass the question to the assistant
3. The assistant says: *"I don't know — but you told me there's an employee called `get_resource_group_info`. Ask them and tell me what they say."*
4. YOU call the employee: `get_resource_group_info("rg-production")`
5. The employee answers: *"12 resources"*
6. You tell the assistant what the employee said
7. The assistant writes the final answer to the customer

The model never touches your function. It tells you which function to call and with what arguments. You call it and report back. The `tools` list is you telling the assistant what employees exist and what they know. Without it, the assistant doesn't know the function exists.

### The two parts of function calling

**1. Your Python function** — a normal function that does something real. In production this calls a database, an API, or the Azure SDK. You write it like any other function.

**2. The tool description** — a JSON object that tells the model the function exists, what it does in plain English, and what arguments it takes. The model reads this and decides on its own whether to call it.

**The model never calls your function directly.** The flow is:

```
User asks a question
    ↓
Model reads the tools list and decides: "I need to call a tool"
    ↓
Model returns finish_reason = "tool_calls" with the function name and arguments it wants
    ↓
Your code calls the actual Python function with those arguments
    ↓
Your code sends the result back with role = "tool"
    ↓
Model reads the result and writes the final reply
```

`finish_reason == "tool_calls"` means the model stopped mid-conversation to request a function — it has not written a final reply yet. You run the function, return the result, and call the API again for the final answer.

---

## Agents

### Function calling is NOT an agent

Function calling is a single capability — the model decides a tool is needed, returns a structured request, your code runs the function, your code sends the result back. That is one turn. It stops there.

An **agent** is a loop built around that capability. It keeps calling the model, running tools, and feeding results back — repeating until the model decides it has a final answer.

```
Function calling:
  User asks → model requests a tool → you run it → you send result → model replies → DONE

Agent:
  User asks → model requests tool A → run it → model requests tool B → run it
            → model requests tool C → run it → model writes final answer → DONE
```

The key difference: **the agent decides how many steps to take.** You didn't write `if/elif/else` logic to pick the next step — the model reads each tool result and figures out what to do next on its own.

### What an agent uses

An agent is not just tools. A real agent combines several things:

| Component | What it is | Real example |
|---|---|---|
| **Tools / functions** | Python functions the model can call | `search_database()`, `send_email()`, `get_weather()` |
| **Short-term memory** | The conversation history (context window) | All the messages so far in this session |
| **Long-term memory** | External storage the agent reads and writes | A vector database, files, a database table |
| **Other models** | Calling a specialist model for a subtask | A vision model to read an image, then pass the text to GPT-4o |
| **Other agents** | Sub-agents the main agent delegates to | A "research agent" that searches the web, a "writer agent" that drafts the report |
| **Planning** | An explicit reasoning step before acting | "Break this goal into subtasks, then execute each one" |

The simplest possible agent uses only tools in a loop. That is what most tutorials show and what this stage covers.

### Real-life examples of agents

**1. HR onboarding agent**
An employee joins. The agent:
- Calls `create_ad_account(name, department)` → creates their Active Directory account
- Calls `assign_licenses(user_id, ["M365", "Azure"])` → assigns software licences
- Calls `add_to_groups(user_id, department)` → adds them to the right Teams channels
- Calls `send_welcome_email(user_id)` → sends the welcome email
- Writes a summary back: "Onboarding complete. 4 steps completed."

A human used to do all of these steps manually across 4 different systems. The agent does them in sequence with no routing logic written by you.

**2. Azure cost review agent**
You ask: "Find all my VMs that haven't been used in 30 days and show me their monthly cost."
- Agent calls `list_all_vms()` → gets a list of 40 VMs
- For each VM, calls `get_vm_metrics(vm_id, days=30)` → checks CPU usage
- For idle VMs, calls `get_vm_cost(vm_id)` → gets the monthly cost
- Writes a final table with the results

You didn't write any loop or branching logic — the model decided to iterate over each VM on its own.

**3. Research and write agent (multi-agent)**
You ask: "Write me a summary of GPT-4o vs Gemini 1.5 Pro."
- Main agent delegates to a "research sub-agent" that searches the web and returns structured notes
- Main agent delegates to a "writing sub-agent" that drafts the summary from the notes
- Main agent reviews the draft and returns the final answer

Each sub-agent is itself a model in a loop. The main agent coordinates them without knowing the internal steps each one took.

---

## Embeddings

An embedding is a list of numbers (a vector) that represents the *meaning* of a piece of text.

- "Azure resource groups are containers for related resources" → `[0.02, -0.14, 0.88, ...]` (1536 numbers)
- Two texts with similar meaning produce vectors that are close together in space
- Two texts about completely different topics produce vectors far apart

You compare vectors using **cosine similarity**:
- `1.0` = identical meaning
- `0.0` = completely unrelated
- `-1.0` = opposite meaning (rare in practice)

### Why embeddings matter — they power vector search

When you do vector search in Azure AI Search:
1. At index time: generate an embedding for each document → store it in the index
2. At query time: generate an embedding for the user's query → search the index for close vectors
3. Result: find documents that are *semantically similar* even if they share no keywords

This is the link between Stage 06 (Azure AI Search) and Stage 07 (Azure OpenAI). Embeddings are what make vector search work.

### Which model to use

| Model | Dimensions | Notes |
|---|---|---|
| `text-embedding-3-small` | 1536 | Recommended for new projects — newer, cheaper, more accurate than ada-002 |
| `text-embedding-3-large` | 3072 | Higher accuracy — use when search quality matters most |
| `text-embedding-ada-002` | 1536 | Legacy — only use to match existing ada-002 vectors |

---

## Structured Outputs

### Structured vs unstructured information

**Unstructured information** is text a human wrote with no predictable shape. Your code cannot reliably read it.

> "The order arrived late and the box was damaged. I'm pretty unhappy about it."

You understand this. Code does not — there is no consistent field to read.

**Structured information** has a known, consistent shape. Every record has the same fields and types.

```json
{
  "sentiment": "negative",
  "issues": ["late delivery", "damaged packaging"],
  "rating_predicted": 2
}
```

Now code can sort by sentiment, count how many orders had damage, trigger a refund workflow, or store this in a database.

**More real-life examples:**

| Unstructured | Structured equivalent |
|---|---|
| A CV as a Word document | `{"name": "Reza", "skills": ["Python", "Azure"], "years_exp": 3}` |
| A doctor's handwritten notes | `{"diagnosis": "hypertension", "medication": "X", "dosage": "10mg"}` |
| An invoice PDF | `{"vendor": "Acme", "total": 450.00, "due_date": "2026-12-01"}` |
| A customer complaint email | `{"category": "shipping", "urgency": "high", "sentiment": "negative"}` |
| A property listing description | `{"bedrooms": 3, "bathrooms": 2, "price": 450000, "parking": true}` |

The world produces enormous amounts of unstructured information — emails, documents, notes, reviews. Before LLMs the only way to extract structure was to pay people to read and label them, or write fragile regex rules. Now you prompt a model, ask for JSON back, and it does the extraction.

### Why you need JSON mode or Pydantic — the problem with plain text

If you ask the model "what is the sentiment of this review?" it might reply:

- `"Positive"`
- `"The sentiment is positive."`
- `"I'd say it's mostly positive, though with some neutral undertones."`

All three are correct answers. None of them are easy to use in code. You'd have to write string-parsing logic and handle every variation — fragile and error-prone.

**JSON mode** solves this. Add `response_format={"type": "json_object"}` and you get:

```json
{"sentiment": "positive", "confidence": 0.92}
```

Your code reads `response["sentiment"]` reliably every time. You still need to tell the model in the system message what fields to include — JSON mode only guarantees valid JSON, not what's inside it.

**Pydantic** goes one step further. You define a Python class describing exactly what shape the data must have. The SDK validates the model's output against it before your code ever touches it. If the model returns the wrong type or a missing field, Pydantic catches it immediately — not somewhere deep in your code later.

```python
# You define the shape you want:
class SentimentResult(BaseModel):
    sentiment: str        # must be a string
    confidence: float     # must be a number
    issues: list[str]     # must be a list of strings

# You get back a typed Python object — not raw text, not raw JSON
result = client.beta.chat.completions.parse(...)
print(result.sentiment)    # "negative"
print(result.confidence)   # 0.87
```

### When to use each

| Situation | Use |
|---|---|
| Simple extraction, one or two fields | JSON mode |
| Complex extraction, nested fields, strict types | Pydantic |
| Output will be stored in a database | Pydantic — catch bad data before it gets in |
| Output will be passed to another service or agent step | JSON mode or Pydantic |
| Classification from a fixed list of categories | Pydantic with `Literal["a", "b", "c"]` type |
| A human will read the answer (chat, Q&A) | Neither — plain text is fine |

**When to use structured outputs:**
- Extracting data from documents (invoices, forms, support tickets)
- Classification tasks (return a category from a fixed list)
- Any time the output will be stored in a database or passed to another service

---

## GPT-4o Vision

GPT-4o is a multimodal model — it can read images alongside text.

You can send:
- A public image URL (Azure fetches it)
- A local image file encoded as base64

What you can do with it:
- Describe what is in an image
- Extract text from scanned documents (like OCR but with reasoning)
- Interpret charts, diagrams, screenshots
- Answer questions about specific details in an image

### GPT-4o Vision vs Azure AI Vision (Image Analysis)

| Use Azure AI Vision when | Use GPT-4o Vision when |
|---|---|
| High volume, low cost | Low volume, need reasoning not just detection |
| You need structured output (tags, bounding boxes) | You need to understand *why* something is in the image |
| Simple tasks: "what objects are in this?" | Complex tasks: "what is wrong in this photo?" |
| Already using Azure AI Vision in your pipeline | Combining vision with chat, extraction, or structured output |

The most powerful pattern: **GPT-4o Vision + Structured Outputs** — send an invoice image and get back a typed Python object with vendor name, amount, and date.

---

## DALL-E Image Generation

DALL-E 3 generates images from a text description. You pass a prompt and get back an image URL.

---

## Authentication

Two options:

| Method | When to use |
|---|---|
| **API key** | Quick throwaway scripts — simple but less secure |
| **DefaultAzureCredential** | Local dev (`az login`) and production (Managed Identity) — same code, no keys anywhere |

The recommended approach is `DefaultAzureCredential` for everything. Locally it picks up your `az login` session. On Azure it picks up the Managed Identity automatically. No keys in `.env`, no risk of leaking credentials. The only requirement is running `az login` once before your first local run.

---

## Cost Awareness

Azure OpenAI has **no free tier**. Every call costs money.

| Model | Input | Output |
|---|---|---|
| gpt-4o | ~$2.50 per 1M tokens | ~$10 per 1M tokens |
| gpt-4o-mini | ~$0.15 per 1M tokens | ~$0.60 per 1M tokens |
| text-embedding-3-small | ~$0.02 per 1M tokens | — |

For this stage: keep `max_tokens` small, keep test inputs short, destroy the resource when done.

---

## Where Azure OpenAI Is Used in Real Projects

| Use case | How |
|---|---|
| **RAG assistants** | User asks a question → Search retrieves relevant chunks → GPT-4o reads them and answers |
| **Document extraction** | Send invoice/contract image → Structured Outputs returns typed data |
| **Customer support bots** | System message constrains the model to company knowledge, function calling retrieves live account data |
| **Code review tools** | Send a diff → model explains what changed and flags issues |
| **Content moderation** | Combined with Content Safety (Stage 02) — model classifies, Content Safety blocks |
| **Data enrichment pipelines** | Indexer + AzureOpenAIEmbeddingSkill generates vectors for every document at indexing time |

---

## AI-102 Exam — Key Points

- Azure OpenAI requires a **dedicated resource** — not covered by the multi-service account. SKU: S0. No free tier.
- The `model` parameter in `chat.completions.create` is the **deployment name**, not the model name.
- Know the four roles: `system`, `user`, `assistant`, `tool`.
- `temperature`: 0 = deterministic, 1 = creative.
- `max_tokens` controls maximum output length.
- Multi-turn conversation requires appending all messages to the `messages` list and sending the full history every request.
- **Streaming**: set `stream=True` and iterate `chunk.choices[0].delta.content`.
- **Function calling**: model returns a `tool_calls` object — your code calls the function and sends the result back via a `tool` role message.
- **Embeddings**: `text-embedding-3-small` is the recommended model. Output is a list of floats. Compare with cosine similarity.
- **Cosine similarity**: 1.0 = identical meaning, 0.0 = unrelated.
- **JSON mode**: `response_format={"type": "json_object"}` — forces valid JSON, but you must tell the model what fields to include in the system message.
- **Structured Outputs**: use `pydantic.BaseModel` and `client.beta.chat.completions.parse` — gives you a typed Python object directly.
- **GPT-4o Vision**: `content` becomes a list with `text` and `image_url` blocks. `"detail": "high"` tiles the image for fine-grained analysis.
- `AzureOpenAIEmbeddingSkill` in an Azure AI Search skillset generates embeddings at indexing time — this is how you automate vector field population without writing custom code.
