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

### Production (Managed Identity — no keys)

```python
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# get_bearer_token_provider creates a function that fetches a token automatically
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"   # the scope for Azure AI services
)

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_ad_token_provider=token_provider,           # no api_key needed
    api_version="2024-12-01-preview"
)
```

Use this in production. `DefaultAzureCredential` picks up the Managed Identity of the Azure service your code runs in (Container App, VM, etc.) — no `.env` file needed.

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
- `**args` — "unpack" a dict as keyword arguments. If `args = {"name": "rg-production"}`, then `func(**args)` is the same as `func(name="rg-production")`
- `"role": "tool"` — this is how you send a function result back. The `tool_call_id` links it to the original request

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
