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

The model has **no memory** — it does not remember previous conversations. To implement multi-turn chat, you must manually append each message and reply to the `messages` list and send the full history every time.

```
Turn 1:
  messages = [system, user1]  →  reply1

Turn 2:
  messages = [system, user1, reply1, user2]  →  reply2
```

This is why conversation history can get expensive: every turn sends all previous messages again.

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

Real use cases:
- Look up a user's account data
- Check the current price of a product
- Search a knowledge base
- Call an external API (weather, calendar, database)

This is how "AI agents" work — the model orchestrates multiple tool calls to complete a task.

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

By default, the model returns free-form text. For real applications you want structured data you can parse and use in code. Two options:

### JSON mode

Add `response_format={"type": "json_object"}` to force the model to return valid JSON. You still need to tell it in the system message what fields to include.

### Structured Outputs with pydantic

The stricter option. You define a Python class with typed fields using `pydantic`. The model is forced to return an object that matches your class exactly — no missing fields, no wrong types. You get back a typed Python object, not raw JSON.

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
| **API key** | Local development — simple, fast to set up |
| **Managed Identity** | Production — no credentials in code or `.env`, RBAC-controlled |

For local development we use API key. For the final project deployed to Azure, everything switches to Managed Identity — same pattern as every other service in this repo.

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
