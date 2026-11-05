# Azure OpenAI — Python Patterns

Quick reference for writing Python scripts that call Azure OpenAI.

---

## Install

```bash
pip install openai azure-identity python-dotenv pydantic
```

- `openai` — the official Python SDK (works with both OpenAI.com and Azure OpenAI)
- `azure-identity` — for Managed Identity authentication (production)
- `pydantic` — for Structured Outputs (typed Python objects from the model)

---

## Client Setup

### Development (API key from .env)

```python
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],   # e.g. https://oai-myapp-dev.openai.azure.com
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-12-01-preview"                      # the API version, not the model version
)
```

- `azure_endpoint` — the URL for YOUR Azure OpenAI resource (not a global OpenAI URL)
- `api_version` — Azure requires this. Use `"2024-12-01-preview"` or the latest stable version. This is the REST API version, not the model version.
- The difference from OpenAI.com: you use `AzureOpenAI` not `OpenAI`, and you pass `azure_endpoint` not `base_url`.

### DefaultAzureCredential — local and production (recommended)

This is the most secure and up-to-date approach. Same code works locally and in production — no changes needed when you deploy.

```python
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)

client = AzureOpenAI(
    azure_endpoint=os.environ["OPENAI_ENDPOINT"],
    azure_ad_token_provider=token_provider,
    api_version="2024-12-01-preview"
)
```

Before running locally, log in once with the Azure CLI:

```bash
az login
```

- **Locally:** `DefaultAzureCredential` picks up your `az login` session — no key needed in `.env`
- **On Azure:** `DefaultAzureCredential` automatically picks up the Managed Identity of the Container App or VM — same code, no changes

#### What is `get_bearer_token_provider`?

Azure tokens expire after ~1 hour. If you fetched one token at startup, your calls would start failing mid-session.

`get_bearer_token_provider` does not fetch a token immediately. It creates a small function that knows *how* to fetch one. The OpenAI client calls that function automatically before each request — reusing the token if it is still valid, or fetching a fresh one if it expired.

```python
get_bearer_token_provider(
    DefaultAzureCredential(),                          # WHERE to get the token from
    "https://cognitiveservices.azure.com/.default"     # WHAT the token grants access to
)
```

The scope `"https://cognitiveservices.azure.com/.default"` tells Azure: "I want a token for Azure AI / Cognitive Services." Without the right scope, the token would be valid but rejected by the service.

Think of it as: instead of handing the client a key card, you give it a key card machine — it prints a fresh card whenever it needs one.

---

## Chat Completion — Single Turn

```python
response = client.chat.completions.create(
    model="gpt-4o",         # YOUR deployment name (not the model name from OpenAI)
    messages=[
        {
            "role": "system",
            "content": "You are a helpful Azure expert. Only answer Azure-related questions."
        },
        {
            "role": "user",
            "content": "What is a resource group?"
        }
    ],
    temperature=0.3,        # 0 = deterministic, 1 = creative
    max_tokens=500          # maximum number of tokens in the response
)

# The model's reply is here
print(response.choices[0].message.content)

# How many tokens did this cost?
print(f"Input tokens:  {response.usage.prompt_tokens}")
print(f"Output tokens: {response.usage.completion_tokens}")
print(f"Total tokens:  {response.usage.total_tokens}")
```

- `client.chat.completions.create` — this is the main method for chat
- `response.choices` — a list of possible responses. Index 0 is always the first (and usually only) response
- `response.choices[0].message.content` — the actual text reply from the model
- `response.usage` — token usage for this request. Always check this when testing to understand cost

---

## Chat Completion — Multi-Turn (Conversation History)

The model has no memory. You must manually keep the full conversation history and send it every turn.

```python
# Start with just the system message
messages = [
    {"role": "system", "content": "You are a helpful Azure assistant."}
]

def chat(user_input):
    # Add the user's message to history
    messages.append({"role": "user", "content": user_input})

    # Send the full history to the model
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.3
    )

    # Get the model's reply
    reply = response.choices[0].message.content

    # Append the reply to history so the next turn includes it
    messages.append({"role": "assistant", "content": reply})

    return reply

# Each call remembers what was said before
print(chat("What is Azure App Service?"))
print(chat("How does it compare to Azure Container Apps?"))
```

- `messages` is a regular Python list — you start with the system message and grow it with every turn
- `messages.append({"role": "assistant", "content": reply})` — you manually add the model's reply to the list. Without this, the model forgets what it just said on the next turn
- Every call to `chat()` sends the full `messages` list — this is why multi-turn conversations cost more over time (more tokens every turn)

---

## Streaming

Instead of waiting for the full response, print tokens as they arrive (the "typing" effect).

```python
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Explain Azure Kubernetes Service in detail."}],
    stream=True      # ← this enables streaming
)

# Iterate through chunks as they arrive
for chunk in stream:
    # chunk.choices[0].delta.content is the new text in this chunk (can be None)
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

print()  # move to a new line when done
```

- `stream=True` — tells Azure to send back chunks instead of waiting for the full response
- `chunk.choices[0].delta.content` — the new text in this chunk. `delta` means "what changed" — i.e. the new part only, not the full response so far
- `end=""` in `print` — suppresses the automatic newline so tokens print on the same line
- `flush=True` — forces Python to print immediately without buffering. Without this, text would appear in batches, not token by token

---

## Function Calling

The model can request to call your Python functions. You define what functions exist, the model decides when to use them.

```python
import json

# Step 1 — describe the tools to the model
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_resource_group_info",
            "description": "Get information about an Azure resource group",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the resource group"
                    }
                },
                "required": ["name"]
            }
        }
    }
]

# Step 2 — your actual Python function
def get_resource_group_info(name):
    # In a real app, this would call the Azure SDK
    return json.dumps({"name": name, "location": "eastus", "resources": 12})

# Step 3 — send a message with the tools available
messages = [{"role": "user", "content": "How many resources are in rg-production?"}]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice="auto"   # model decides whether to call a tool
)

# Step 4 — check if the model wants to call a function
if response.choices[0].finish_reason == "tool_calls":
    tool_call = response.choices[0].message.tool_calls[0]

    # Extract the function name and arguments (model sends these as JSON)
    function_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    # Step 5 — call your function with the model's chosen arguments
    result = get_resource_group_info(**args)

    # Step 6 — send the result back to the model
    messages.append(response.choices[0].message)   # add the model's tool_call message
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,              # must match the original tool call
        "content": result                          # the result of your function
    })

    # Step 7 — the model now has the result and writes the final reply
    final_response = client.chat.completions.create(model="gpt-4o", messages=messages)
    print(final_response.choices[0].message.content)
```

Key things:
- `finish_reason == "tool_calls"` — the model stopped because it wants to call a function, not because it finished replying
- `tool_call.function.arguments` is a JSON string — use `json.loads()` to convert it to a Python dict
- `**args` — "unpack" a dict as keyword arguments. If `args = {"name": "rg-production"}`, then `func(**args)` is the same as writing `func(name="rg-production")` manually. Used when you don't know the arguments at write time — the model chose them at runtime.
- `"role": "tool"` — this is how you send a function result back. The `tool_call_id` links it to the original request

### Breaking down every part of a function calling block

```python
# ── PART A: Your real Python function ─────────────────────────────────────
def get_azure_service_info(service_name):
    services = {
        "container apps": {"description": "Serverless containers", "docs": "https://..."}
    }
    return json.dumps(services.get(service_name.lower()))
```
**What it is:** a normal Python function you write. Nothing Azure-specific here.
**What you control:** the name, the arguments, everything it does inside.
**`json.dumps()`:** converts a Python dict into a JSON string — required because the model only receives text back, not Python objects.

---

```python
# ── PART B: The tool description ──────────────────────────────────────────
tools = [
    {
        "type": "function",          # always "function" — this never changes
        "function": {
            "name": "get_azure_service_info",   # must match your Python function name exactly
            "description": "Get information about an Azure compute service",  # you write this — the model reads it to decide WHEN to call the function
            "parameters": {
                "type": "object",    # always "object" — this never changes
                "properties": {
                    "service_name": {              # the argument your function expects
                        "type": "string",          # the data type of that argument
                        "description": "The Azure service name"  # helps the model fill in the right value
                    }
                },
                "required": ["service_name"]       # which arguments are mandatory
            }
        }
    }
]
```
**What it is:** a Python dict (not JSON text — the SDK converts it) that you write and send to the model. It is NOT code that runs — it is a job posting that tells the model what tools exist.
**What you control:** the description text — this is the most important part. The model reads `description` to decide whether this tool fits the user's question. Write it clearly.
**What is fixed:** `"type": "function"` and `"type": "object"` — always the same, never change these.

---

```python
# ── PART C: First API call — ask the model with tools available ────────────
messages = [{"role": "user", "content": "I need microservices that scale to zero. Which Azure service?"}]

fc_response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,          # give the model the tool list
    tool_choice="auto"    # let the model decide whether to use a tool or answer directly
)
```
**What it is:** the first API call. Same as a normal chat call but with `tools=` added.
**`tool_choice="auto"`:** the model decides on its own whether to call a tool or just answer. Use `"required"` to force it to always call a tool, or pass a specific tool name to force one tool.
**What comes back:** either a normal reply (if the model decides no tool is needed) OR a `finish_reason == "tool_calls"` response (model wants to call a function).

---

```python
# ── PART D: Check if the model wants to call a function ───────────────────
if fc_response.choices[0].finish_reason == "tool_calls":
```
**What it is:** a check on why the model stopped generating.
**`finish_reason`** possible values:
- `"stop"` — model finished its reply normally
- `"tool_calls"` — model stopped to request a function call, has not written a final reply yet
- `"length"` — stopped because it hit `max_tokens`

---

```python
# ── PART E: Extract what the model wants to call ──────────────────────────
    tool_call = fc_response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
```
**`tool_calls[0]`:** the first tool call the model requested. If you gave it multiple tools and it wants to call more than one, they are all in this list.
**`tool_call.function.name`:** which function the model chose — e.g. `"get_azure_service_info"`
**`tool_call.function.arguments`:** a JSON string with the arguments the model chose — e.g. `'{"service_name": "container apps"}'`
**`json.loads()`:** converts that JSON string into a Python dict so you can use it — e.g. `{"service_name": "container apps"}`

---

```python
# ── PART F: Call your function with the model's chosen arguments ───────────
    result = get_azure_service_info(**args)
```
**`**args`:** unpacks the dict as keyword arguments. `get_azure_service_info(**{"service_name": "container apps"})` is the same as `get_azure_service_info(service_name="container apps")`. The model chose the value; you just pass it through.

---

```python
# ── PART G: Send the result back ──────────────────────────────────────────
    messages.append(fc_response.choices[0].message)   # the model's tool_call request
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,    # links this result to the original request
        "content": result                # the string your function returned
    })
```
**Why append the model's message first:** the conversation history must include the model's tool_call request before the tool result — the model needs to see its own request in the history to understand the context.
**`"role": "tool"`:** a special role that means "this is a function result". The model knows to treat this as data, not as something a human said.
**`tool_call_id`:** a unique ID on each tool call. If the model requested multiple tools, the ID tells it which result belongs to which request.

---

```python
# ── PART H: Second API call — model writes the final reply ─────────────────
    final = client.chat.completions.create(model="gpt-4o", messages=messages)
    print(final.choices[0].message.content)
```
**What it is:** a second normal API call with the full conversation history — now including the tool result. The model reads the data your function returned and writes the final answer to the user. This is a regular reply with `finish_reason == "stop"`.

---

### Three things worth knowing about tools

**1. `tools` is Python dicts, not JSON text.**

You write `tools = [{ "type": "function", ... }]` as a Python list of dicts. The SDK converts it to JSON for you before sending it to the API. You do not need to call `json.dumps()` on it.

**2. `tools` can live at the top of the file — it does not have to be inside a function.**

It is just a variable. Define it once at module level and pass it to any API call that needs it:

```python
# Top of the file — global scope
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_account_balance",
            ...
        }
    }
]

# Used anywhere in the file
response = client.chat.completions.create(model="gpt-4o", messages=messages, tools=tools)
```

**3. One `tools` list can hold many functions.**

The model receives all of them and picks the right one based on the user's question:

```python
tools = [
    {"type": "function", "function": {"name": "get_account_balance", ...}},
    {"type": "function", "function": {"name": "create_calendar_event", ...}},
    {"type": "function", "function": {"name": "search_knowledge_base", ...}},
]
```

You pass the same `tools` list to every call. The model decides which function (if any) fits the question. You still only handle the one it picked via `tool_calls[0]`.

---

### Real-world function calling use cases

The example in the script uses a dict — that's just to keep the syntax clean while learning. In production, the function body would call a real system:

| What user says | Function the model calls | What the function actually does |
|---|---|---|
| "What's my account balance?" | `get_account_balance(user_id)` | Queries your database |
| "Book a meeting tomorrow at 3pm" | `create_calendar_event(date, time)` | Calls Outlook or Google Calendar API |
| "How many VMs haven't been used in 30 days?" | `list_vms()` then `get_vm_metrics(vm_id)` | Calls Azure SDK, runs for each VM |
| "My order hasn't arrived" | `get_order_status(order_id)` | Hits your order management system |
| "Find docs about this error" | `search_knowledge_base(query)` | Calls Azure AI Search |

**The key value:** without function calling, you write `if/elif` chains to route every possible question. With function calling, the model reads the question and picks the right function itself — no routing logic needed in your code.

---

## Embeddings

An embedding is a list of numbers representing the meaning of text. Close vectors = similar meaning.

```python
# Generate an embedding
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="Azure resource groups are containers for related Azure resources."
)

# The embedding is a list of floats (1536 numbers for text-embedding-3-small)
embedding = response.data[0].embedding
print(f"Number of dimensions: {len(embedding)}")   # 1536
```

- `response.data[0].embedding` — a Python list of floats. This is the vector.
- `model="text-embedding-3-small"` — use this for new projects. Newer and better than `ada-002`.

### Cosine Similarity — comparing two embeddings

Cosine similarity measures how close two vectors are. Returns a number between -1 and 1.

```python
import math

def cosine_similarity(vec_a, vec_b):
    # Calculate dot product (multiply each pair of numbers and sum)
    dot = sum(a * b for a, b in zip(vec_a, vec_b))

    # Calculate the magnitude (length) of each vector
    magnitude_a = math.sqrt(sum(a ** 2 for a in vec_a))
    magnitude_b = math.sqrt(sum(b ** 2 for b in vec_b))

    # Divide dot product by the product of magnitudes
    return dot / (magnitude_a * magnitude_b)

# Compare two pieces of text
embedding_a = client.embeddings.create(model="text-embedding-3-small", input="I love Azure").data[0].embedding
embedding_b = client.embeddings.create(model="text-embedding-3-small", input="I enjoy cloud computing").data[0].embedding
embedding_c = client.embeddings.create(model="text-embedding-3-small", input="The weather is sunny today").data[0].embedding

print(cosine_similarity(embedding_a, embedding_b))  # high — similar topic
print(cosine_similarity(embedding_a, embedding_c))  # low — unrelated topic
```

- `zip(vec_a, vec_b)` — pairs up elements from two lists: `[(a[0], b[0]), (a[1], b[1]), ...]`
- `sum(a * b for a, b in zip(...))` — multiplies each pair and sums the results. This is called the dot product.
- `math.sqrt(sum(a ** 2 for a in vec))` — squares each element, sums, then takes the square root. This is the vector length (magnitude).
- The result is between -1.0 and 1.0. In practice for similar sentences: 0.85+. For unrelated sentences: 0.1–0.3.

---

## Structured Outputs — JSON Mode

Force the model to return valid JSON. Simpler than pydantic but no type guarantees.

```python
import json

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "You extract information from text. Always respond with valid JSON."
        },
        {
            "role": "user",
            "content": "Extract the person's name, age, and city: John Smith, 34, lives in Manchester."
        }
    ],
    response_format={"type": "json_object"}  # forces the model to return valid JSON
)

# Parse the JSON string into a Python dict
data = json.loads(response.choices[0].message.content)
print(data["name"])   # "John Smith"
print(data["age"])    # 34
print(data["city"])   # "Manchester"
```

- `response_format={"type": "json_object"}` — the model will always return valid JSON. It will never output a broken response.
- You still need to tell the model what fields to include in the system message — this parameter does not define the shape.
- `json.loads()` — converts a JSON string (text) into a Python dict. The model returns text; `json.loads` turns it into data you can use.

---

## Structured Outputs — pydantic (Stricter)

Define a class with typed fields. The model is forced to match it exactly. You get a typed Python object back.

```python
from pydantic import BaseModel

# Define the shape of the data you want
class PersonInfo(BaseModel):
    name: str     # must be a string
    age: int      # must be an integer
    city: str     # must be a string

response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Extract information from the text."},
        {"role": "user", "content": "John Smith, 34, lives in Manchester."}
    ],
    response_format=PersonInfo   # pass the class itself, not an instance of it
)

# You get a typed Python object, not a dict
person = response.choices[0].message.parsed
print(person.name)   # "John Smith" — dot notation, not dict["key"]
print(person.age)    # 34 — already an int, not the string "34"
```

- `BaseModel` — the base class from pydantic. Inherit from it to define a data shape.
- `name: str` — typed field. `str` means string. `int` means integer. `float` means decimal.
- `client.beta.chat.completions.parse` — a different method than `.create`. Uses the schema to validate the response.
- `response_format=PersonInfo` — pass the class, not `PersonInfo()`. The class itself is the schema.
- `response.choices[0].message.parsed` — a real Python object with attributes. Access fields with `.name`, `.age`, not `["name"]`.
- **Why use this over JSON mode?** The SDK raises an error if the model returns the wrong type or omits a field — you catch the error early instead of getting a runtime crash when you try to use the data later.

---

## GPT-4o Vision — Image Input

Send an image alongside text. The `content` field becomes a list instead of a string.

### Option 1 — Image URL

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What is happening in this image?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "high"   # "low" = faster/cheaper, "high" = fine-grained (for text in images)
                    }
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
```

### Option 2 — Local Image (base64 encoded)

```python
import base64

# Read the image file as bytes and encode it as base64 text
with open("invoice.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract the total amount, vendor name, and invoice date from this invoice."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_data}"
                    }
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
```

Key things:
- `content` is now a **list** not a string — each item is a dict with a `type` key
- `"rb"` — open in read-binary mode. Images are binary files (not plain text)
- `base64.b64encode(f.read())` — converts the raw bytes into a base64 string (only letters, numbers, and `+/=`)
- `.decode("utf-8")` — converts the bytes output of `b64encode` into a regular Python string
- `f"data:image/png;base64,{image_data}"` — the format Azure expects for inline images. Change `image/png` to `image/jpeg` for JPG files
- `"detail": "high"` — Azure tiles the image into 512×512 pieces for analysis. Use for documents, charts, anything with text. Costs more tokens. `"low"` for quick descriptions.

---

## DALL-E Image Generation

```python
response = client.images.generate(
    model="dall-e-3",
    prompt="A diagram showing Azure resource hierarchy: subscription, resource group, resources. Flat design, blue and white.",
    size="1024x1024",    # "1024x1024", "1792x1024", or "1024x1792"
    quality="standard",  # "standard" or "hd"
    n=1                  # number of images (DALL-E 3 only supports n=1)
)

# The generated image is available at this URL (expires after a few hours)
image_url = response.data[0].url
print(f"Generated image: {image_url}")
```

---

## Why `response` and `reply` are different names

`response` is the full object Azure sends back — it contains the message text, token count, model name, finish reason, and more.

`reply` is just the text pulled out of it:

```python
reply = response.choices[0].message.content
```

Think of it like a letter arriving in an envelope:
- `response` = the envelope with everything inside
- `reply` = the actual letter you pulled out of it

The names themselves don't matter — you could call them `api_response` and `text`. The pattern is always the same: call the API, get the full object back, then dig into it to get the text you actually want.

---

## Why no `azure-core` import for OpenAI

`AzureKeyCredential` (from `azure-core`) is a wrapper object some Azure SDKs require around a key. The Search SDK requires it. The OpenAI SDK accepts a plain string directly via `api_key=` — no wrapper needed.

`DefaultAzureCredential` (from `azure-identity`) is only for Managed Identity — the production approach where no key exists. It looks for a Managed Identity, environment variables, or a logged-in `az` CLI session to get a token automatically.

| Situation | What you need |
|---|---|
| OpenAI SDK + API key | Just `api_key="..."` — nothing extra to import |
| Search SDK + API key | `AzureKeyCredential` from `azure-core` — the SDK requires the wrapper |
| Any SDK + Managed Identity | `DefaultAzureCredential` from `azure-identity` |

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `AuthenticationError` | Wrong API key | Check `.env` — key must not have quotes around it |
| `NotFoundError` — deployment not found | Wrong `model=` name | The `model=` parameter must be your deployment name, not the model family name |
| `RateLimitError` | Too many requests, or not enough capacity on the deployment | Wait and retry, or increase capacity (tokens per minute) on the deployment |
| `InvalidRequestError` on `response_format` | Model version does not support JSON mode | Use `gpt-4o` or `gpt-4o-mini` — older models do not support `response_format` |
| `json.JSONDecodeError` after JSON mode | Model returned text before the JSON | Make sure the system message says to *only* return JSON, no preamble |
| `BadRequestError` on image | Image too large | Resize to under 20MB, or use `"detail": "low"` to reduce token cost |
| `ContentFilterFinished` | Content Safety blocked the response | Adjust the prompt — Azure OpenAI has built-in content filtering that cannot be disabled |
