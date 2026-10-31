# SDK — Software Development Kit

## What is an SDK?

An SDK is a package of pre-written code that handles communication between your application and an external service. Instead of writing everything from scratch, you install the SDK and use the methods it provides.

When you call an external service like Azure AI, five things need to happen every time:

1. Build the HTTP request in the exact format the service expects
2. Send it to the right URL
3. Wait for the response
4. Parse the JSON that comes back
5. Give you a clean object to work with in your code

The SDK does all five of these for you. You just call a method.

---

## Without an SDK vs With an SDK

**Without SDK — you write everything manually:**
```python
import requests
import json

headers = {
    "Ocp-Apim-Subscription-Key": key,
    "Content-Type": "application/json"
}
body = {
    "documents": [{"id": "1", "text": "I love Azure"}]
}
response = requests.post(
    "https://ai-myaiapp-dev.cognitiveservices.azure.com/text/analytics/v3.1/sentiment",
    headers=headers,
    json=body
)
data = response.json()
sentiment = data["documents"][0]["sentiment"]
```

**With SDK — the same result in three lines:**
```python
client = TextAnalyticsClient(endpoint=endpoint, credential=credential)
result = client.analyze_sentiment(["I love Azure"])
print(result[0].sentiment)
```

---

## The Pattern — Same Every Time

Every Azure SDK follows this exact same structure:

```python
# Step 1 — create the client (set up the connection)
client = SomeAzureClient(endpoint=..., credential=...)

# Step 2 — call a method (send the request)
result = client.do_something(your_data)

# Step 3 — read the result (use what came back)
print(result.some_property)
```

The client, method name, and result shape change per service. The pattern never does.

---

## Azure SDKs Used in This Project

| Package | Service | What it covers |
|---|---|---|
| `azure-ai-textanalytics` | Language | Sentiment, entity recognition, key phrases, PII, summarisation |
| `azure-ai-vision-imageanalysis` | Vision | Image description, OCR, object detection |
| `azure-cognitiveservices-speech` | Speech | Speech to text, text to speech |
| `azure-ai-documentintelligence` | Document Intelligence | Extract data from PDFs and forms |
| `azure-search-documents` | AI Search | Index and search documents |
| `openai` | Azure OpenAI | GPT-4o chat, embeddings, image generation |
| `azure-identity` | Authentication | `DefaultAzureCredential` and all auth methods |
| `python-dotenv` | Utility | Reads `.env` file into environment variables |

---

## How to Install an SDK

```bash
pip install azure-ai-textanalytics
```

`pip` is Python's package manager. It downloads the package from PyPI (Python Package Index) — a public registry of Python packages, similar to npm for JavaScript or NuGet for .NET.

---

## AzureKeyCredential vs DefaultAzureCredential — which to use

Every modern Azure SDK accepts both. They are not the same thing.

| | `AzureKeyCredential` | `DefaultAzureCredential` |
|---|---|---|
| **What it uses** | An API key from your `.env` | Your Azure CLI login, or Managed Identity in production |
| **Where the key lives** | In `.env` on your machine | Nowhere — no key exists |
| **Works locally without setup** | Yes — just copy the key from Terraform output | Only if you ran `az login` AND have the right RBAC role on the resource |
| **Safe for GitHub / CI/CD** | No — keys must never be committed | Yes — this is the production pattern |
| **Requires RBAC role** | No | Yes — the user or identity must have `Foundry User` (or similar) role |

**Rule for this project:**
- **Local Python scripts** → `AzureKeyCredential` — simpler, works immediately, key stays in `.env` which is gitignored
- **GitHub Actions and Container Apps** → `DefaultAzureCredential` — no keys stored anywhere, Managed Identity handles auth

You will switch to `DefaultAzureCredential` properly when you reach Stage 07/08 and deploy to Container Apps. That is when it matters most.

```python
# Local development (what we use now)
from azure.core.credentials import AzureKeyCredential
client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))

# Production / CI/CD (Stage 07+)
from azure.identity import DefaultAzureCredential
client = TextAnalyticsClient(endpoint=endpoint, credential=DefaultAzureCredential())
```

---

## HTTP and REST — What the SDK Hides

Under the hood, every SDK is making HTTP requests to a REST API. REST is a standard way services communicate over the internet — your code sends a request to a URL and gets JSON back.

You do not need to know the details of HTTP or REST to use an SDK. But it helps to know the SDK is not magic — it is just a cleaner interface on top of standard web communication.
