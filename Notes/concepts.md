# Azure AI — Core Concepts

A plain-English reference for understanding how Azure AI services work. No assumed knowledge beyond basic cloud fundamentals.

---

## What is Microsoft Foundry?

Microsoft Foundry is the unified platform on Azure for building AI applications and agents. It is where you manage everything AI-related in one place.

It has three main things inside it:

- **Model deployments** — hosted AI models you can call from your code (GPT-4o, DALL-E, embeddings)
- **Foundry Tools** — pre-built AI capabilities you call via API (Language, Speech, Vision, Document Intelligence, and more)
- **Agent Service** — infrastructure for building multi-step AI agents

You interact with Foundry mainly through the portal (web UI) or the Azure CLI. Your Python code talks directly to the individual Foundry Tools, not to Foundry itself.

---

## What are Foundry Tools?

Foundry Tools are ready-made AI capabilities that Microsoft has already trained and hosts for you. You do not build or train these — you just call them from code and get results back.

| Tool | What it does |
|---|---|
| **Language** | Analyse text — sentiment, entities, key phrases, PII detection |
| **Speech** | Convert audio to text (transcription) or text to audio (synthesis) |
| **Vision** | Analyse images — describe content, read text (OCR), detect objects |
| **Document Intelligence** | Extract structured data from PDFs, forms, invoices, receipts |
| **Translator** | Translate text between languages |
| **Content Safety** | Detect harmful content in text and images |

Think of them as specialist functions you can call from Python. You send data in, you get a structured result back.

**Example:** You send a customer review to the Language tool. It returns:
```json
{
  "sentiment": "negative",
  "confidence": 0.94,
  "key_phrases": ["terrible experience", "no warning", "3 hours"]
}
```

---

## How to Provision Foundry Tools

Before you can call any Foundry Tool from code, you need to create a resource in Azure. A resource is the Azure term for a provisioned service — it gives you an **endpoint** (the URL you send requests to) and a **key** (the password that proves you are allowed to use it).

There are two ways to provision Foundry Tools:

---

### Option 1 — Multi-service resource

One resource that unlocks access to **all** Foundry Tools.

- Single endpoint URL
- Single key
- Covers Language, Vision, Speech, Document Intelligence, and more — all in one

**When to use it:**
- Development and learning environments
- Projects that use multiple Foundry Tools and don't need separate cost tracking
- When simplicity matters more than granularity

**Real-world analogy:** A master key that opens every door in a building. Simple to manage, but you can't tell which doors are being used or control access per door.

**Example:** A startup building an AI assistant that analyses text, processes documents, and transcribes calls — all services, one resource, one bill.

---

### Option 2 — Single-service resource

One dedicated resource per capability. Language has its own resource, Vision has its own, Speech has its own.

- Separate endpoint and key per service
- Independent cost tracking per service
- Tighter access control — a team only gets the key for their service

**When to use it:**
- Production environments
- Teams where different groups own different services
- When you need to see exactly what each capability costs
- When compliance requires least-privilege access

**Real-world analogy:** Individual keys for individual rooms. More setup work, but each team only has access to what they need, and the facilities manager can see exactly which rooms are being used.

**Example:** A large company where the data team owns Document Intelligence, the product team owns Language, and the infra team manages access to each separately.

---

### How to decide

| Situation | Use |
|---|---|
| Learning, demos, prototypes | Multi-service |
| Using more than one Foundry Tool | Multi-service |
| Going to production | Single-service |
| Need cost tracking per capability | Single-service |
| Different teams own different services | Single-service |
| Security or compliance requirements | Single-service |

---

## The CLI and Terraform Naming Gap

Even though the service is now called **Foundry Tools**, the Azure CLI command and Terraform resource names have not been updated yet. This is normal — Microsoft renamed the service but the underlying Azure resource provider (`Microsoft.CognitiveServices`) has not changed.

**CLI:**
```bash
az cognitiveservices account create ...
```

**Terraform:**
```hcl
resource "azurerm_cognitive_account" "example" { ... }
```

Do not let this confuse you. These are the correct commands. Use them as-is and ignore the name mismatch.

---

## Endpoint and Key — What They Are

Every Foundry Tools resource gives you two things:

**Endpoint** — the URL your code sends requests to.
```
https://eastus.api.cognitive.microsoft.com/
```
The region in the URL (e.g. `eastus`) tells you which Azure data centre hosts your resource.

**Key** — a long string that proves to Azure you are authorised to use the resource.
```
2SRoC...
```

Your Python code needs both to make a call. Never hardcode them in your code — store them in a `.env` file locally or in Azure Key Vault in production.

---

## The Full Azure AI Hierarchy — What Belongs Where

Understanding the hierarchy is essential before anything else makes sense.

```
Microsoft Azure
└── Microsoft Foundry (the platform — your control panel for AI)
    ├── Foundry Tools (pre-built AI APIs — you call these from Python)
    │   ├── Multi-service resource (kind: CognitiveServices)
    │   │   └── Covers all Foundry Tools under one endpoint
    │   └── Single-service resources (one resource per capability)
    │       ├── Language       (kind: TextAnalytics)
    │       ├── Vision         (kind: ComputerVision)
    │       ├── Speech         (kind: SpeechServices)
    │       ├── Translator     (kind: TextTranslation)
    │       ├── Document Intel (kind: FormRecognizer)
    │       ├── Content Safety (kind: ContentSafety)
    │       ├── Anomaly Detect (kind: AnomalyDetector)
    │       ├── Face           (kind: Face)
    │       ├── Custom Vision  (kind: CustomVision.Training / CustomVision.Prediction)
    │       └── ...
    └── Azure OpenAI (separate — you choose the exact model)
        ├── GPT-4o
        ├── GPT-3.5-turbo
        ├── text-embedding-ada-002
        └── DALL-E
```

---

## Microsoft Foundry — The Platform

Microsoft Foundry is not a service you call from Python. It is the **platform** — the web portal and management layer where you:
- Create and manage your AI resources
- Deploy models
- Monitor usage
- Run evaluations and experiments

Think of it as the Azure portal but specifically for AI. You use it through the browser, not in code.

---

## Foundry Tools — Pre-built AI APIs

Foundry Tools is the collection of AI capabilities that Microsoft built and hosts for you. You call these from Python by sending data in and getting results back. You do not train, host, or maintain the models — Microsoft does all of that.

### How Microsoft decides which model runs

When you call a Foundry Tools API, three things determine what runs behind the scenes:

1. **The API method you call** — `analyze_sentiment` vs `recognize_entities` vs `read` each routes to a different internal model
2. **The API version in the SDK** — e.g. `v2023_04_01`. Microsoft can silently swap the underlying model as long as the output format stays the same
3. **Microsoft's current production model** — they update it when they have a better one. You have no control and no visibility into the model name

You never see the model. You just see the result.

---

## Foundry Tools — All Single Services

| Kind (Terraform/CLI) | Service name | What it does |
|---|---|---|
| `CognitiveServices` | Multi-service | All Foundry Tools under one endpoint — for development |
| `TextAnalytics` | Language | Sentiment analysis, entity recognition, key phrases, PII detection, language detection, summarisation, translation detection |
| `ComputerVision` | Vision | Describe images, read text from images (OCR), detect objects and people, spatial analysis |
| `Face` | Face | Detect faces in images, verify if two faces match, analyse attributes. Restricted — requires Microsoft approval to use |
| `CustomVision.Training` | Custom Vision Training | Upload your own labelled images and train a custom image classification model |
| `CustomVision.Prediction` | Custom Vision Prediction | Run predictions using your own trained custom vision model |
| `SpeechServices` | Speech | Convert audio to text (transcription), convert text to audio (synthesis), identify speakers, real-time captioning |
| `TextTranslation` | Translator | Translate text between 100+ languages, detect source language, transliterate scripts |
| `FormRecognizer` | Document Intelligence | Extract structured data from PDFs, invoices, receipts, forms, ID cards — returns JSON with field names and values |
| `ContentSafety` | Content Safety | Detect harmful content in text and images — violence, hate speech, sexual content, self-harm |
| `AnomalyDetector` | Anomaly Detector | Analyse time-series data (metrics over time) and flag data points that don't fit the normal pattern |

---

## Azure OpenAI — Different Category, Different Control

Azure OpenAI sits alongside Foundry Tools under Microsoft Foundry, but it works differently.

**The key difference:**

| | Foundry Tools | Azure OpenAI |
|---|---|---|
| You choose the model | No — Microsoft picks it | Yes — you deploy a specific model |
| Model is visible to you | No | Yes — you name the deployment |
| Microsoft updates it silently | Yes | No — your deployment stays on the version you chose |
| You control the model version | No | Yes |

**How Azure OpenAI works:**

You create two things:
1. The resource — `kind: OpenAI` in Terraform
2. A deployment inside it — where you pick the exact model

```bash
# The resource
az cognitiveservices account create --kind OpenAI ...

# The deployment — you choose the model here
az cognitiveservices account deployment create \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-05-13"
```

Your Python code then calls the deployment by the name you gave it:

```python
response = client.chat.completions.create(
    model="gpt-4o",  # this is your deployment name
    ...
)
```

**Available models in Azure OpenAI:**

| Model | What it does |
|---|---|
| `gpt-4o` | Most capable chat model — understands text and images |
| `gpt-35-turbo` | Faster, cheaper chat model — text only |
| `text-embedding-ada-002` | Converts text into vectors — used in RAG pipelines |
| `dall-e-3` | Generates images from text descriptions |

---

## Foundry Tools vs Azure OpenAI — When to Use Which

| Use case | Use |
|---|---|
| Analyse existing text (sentiment, entities, language) | Foundry Tools — Language |
| Read text from a document or image | Foundry Tools — Document Intelligence or Vision |
| Translate between languages | Foundry Tools — Translator |
| Transcribe or generate audio | Foundry Tools — Speech |
| Detect harmful content | Foundry Tools — Content Safety |
| Detect anomalies in data | Foundry Tools — Anomaly Detector |
| Generate text, answer questions, summarise with a large language model | Azure OpenAI |
| Build a RAG pipeline (search + answer) | Azure OpenAI (embeddings + chat) + AI Search |
| Generate images | Azure OpenAI — DALL-E |

---

## RBAC Role Assignment — Giving Access to a User or Identity

After provisioning a Foundry Tools resource, you need to explicitly grant access to any identity that needs to call it.

### The role

**Foundry User** — grants permission to call the Foundry Tools APIs. In the CLI it still appears as `Cognitive Services User` (old name, same role).

### Assign via CLI

```bash
az role assignment create \
  --assignee <object-id> \
  --role "Cognitive Services User" \
  --scope /subscriptions/<sub-id>/resourceGroups/<rg-name>/providers/Microsoft.CognitiveServices/accounts/<resource-name>
```

- `--assignee` — the object ID of the user, service principal, or managed identity
- `--role` — the role name
- `--scope` — how broad the permission is. Scoping to the specific resource (not the whole subscription) is best practice — the identity can only call that one resource

### Who gets this role

| Identity | When |
|---|---|
| A specific user in Entra ID | When a person needs to call the service directly |
| A service principal | When an external app or script needs access |
| A managed identity | When a deployed Azure app (Container App, App Service) needs access |

### What the role does NOT give

- Cannot create or delete resources
- Cannot view keys
- Cannot change network rules or configuration
- Only allows calling the AI service APIs

### Getting the object ID of a user

```bash
az ad user list --filter "displayName eq 'Test User'" --query "[0].id" -o tsv
```

---

## Custom Subdomain — Required for Token Authentication

When you create a Foundry Tools resource, Azure gives you a generic regional endpoint by default:
```
https://eastus.api.cognitive.microsoft.com/
```

This endpoint only works with an API key. It does not support `DefaultAzureCredential` or Managed Identity.

To use token-based authentication you must give your resource a **custom subdomain**. This creates a unique endpoint specific to your resource:
```
https://ai-myaiapp-dev.cognitiveservices.azure.com/
```

In Terraform, add `custom_subdomain_name` to the resource:

```hcl
resource "azurerm_cognitive_account" "foundry" {
  name                  = "ai-${var.workload}-${var.environment}"
  custom_subdomain_name = "ai-${var.workload}-${var.environment}"
  ...
}
```

The subdomain name must be globally unique across all Azure customers — using your resource name is the safest convention.

**Rule:** If you plan to use `DefaultAzureCredential` or Managed Identity, always set `custom_subdomain_name`. Without it, you are forced to use keys.

---

## Two Ways to Authenticate

Once you have a resource, your code needs to prove its identity to Azure before it can call the API. There are two approaches:

### Keys (simple, not recommended for production)

You pass the key directly in your code via an environment variable.

```python
from azure.core.credentials import AzureKeyCredential

credential = AzureKeyCredential(os.environ["AI_KEY"])
```

Easy to set up. The risk is that keys can be copied and misused if they leak.

### Managed Identity (recommended for production)

No key at all. Azure automatically handles authentication between your app and the Foundry Tools resource using its own identity system.

```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
```

`DefaultAzureCredential` tries several auth methods in order:
1. Environment variables (works in CI/CD pipelines)
2. Managed Identity (works when your app runs on Azure — App Service, Container App, VM)
3. Azure CLI login (works on your local machine during development)

You write the same code everywhere. It picks the right method automatically depending on where the code is running.

The RBAC role your identity needs to call Foundry Tools: **Foundry User**

---

## Securing Foundry Tools — Network Access Control

Every Foundry Tools resource is public by default — anyone on the internet can try to reach it (they still need a valid key or identity, but the network door is open).

You control this with `network_acls` in Terraform:

```hcl
network_acls {
  default_action = "Allow"
  ip_rules       = []
}
```

### default_action options

| Value | What it means |
|---|---|
| `Allow` | Everyone can reach the resource over the network |
| `Deny` | Nobody can reach it unless explicitly allowed |

### Locking it down — IP rules

Allow only specific IP addresses:

```hcl
network_acls {
  default_action = "Allow"
  ip_rules       = ["203.0.113.10"]
}
```

### Locking it down — VNet rules

Allow only traffic from inside a specific Virtual Network subnet:

```hcl
network_acls {
  default_action = "Deny"
  virtual_network_rules {
    subnet_id = var.subnet_id
  }
}
```

### When to use what

| Stage | Setting | Why |
|---|---|---|
| Learning locally | `Allow` | Your local machine needs to reach the resource |
| Production with deployed app | `Deny` + VNet rule | App lives inside VNet, public access is closed |

### Private Endpoint

A step beyond network rules. The resource gets a private IP address inside your VNet — traffic never leaves Microsoft's network at all. Used in high-security environments where even the public endpoint should not exist.

---

## Monitoring Foundry Tools Usage

After you deploy a resource, Azure collects metrics automatically. You can view them in the portal or via CLI.

### View metrics via CLI

```bash
az monitor metrics list \
  --resource /subscriptions/.../cognitiveservices/accounts/ai-myaiapp-dev \
  --metric "TotalCalls,TotalErrors" \
  --interval PT1H
```

- `TotalCalls` — how many API calls were made
- `TotalErrors` — how many failed
- `PT1H` — interval of 1 hour (ISO 8601 duration format)

### Set a cost alert

Even on pay-as-you-go, you can set a budget so Azure emails you if spending goes above a threshold:

```bash
az consumption budget create \
  --budget-name ai-monthly-budget \
  --amount 50 \
  --time-grain Monthly \
  --category Cost
```

This does not stop spending — it just alerts you. Set it low (e.g. $10) while learning so you catch any accidental usage early.

### What to monitor in production

| Metric | Why it matters |
|---|---|
| TotalCalls | Track usage volume |
| TotalErrors | Catch broken integrations early |
| Latency | Detect performance issues |
| SuccessRate | Overall health of the service |

---

## Keys vs DefaultAzureCredential — Full Comparison

| | API Key | DefaultAzureCredential |
|---|---|---|
| What proves your identity | A long secret string | Your Azure login / Managed Identity |
| Where it's stored | `.env` file or Key Vault | Azure AD — nothing to store |
| Risk if it leaks | Anyone with the key can call your service | Nothing to leak |
| Works locally | Yes | Yes — uses `az login` session |
| Works on Azure (deployed app) | Yes — but you must store the key somewhere | Yes — uses Managed Identity automatically |
| Recommended for production | No | Yes |
| Requires custom subdomain | No | Yes |

**How DefaultAzureCredential decides what to use:**

It tries authentication methods in this order:
1. Environment variables — used in CI/CD pipelines
2. Managed Identity — used when your app runs on Azure (App Service, Container App, VM)
3. Azure CLI login — used on your local machine during development

You write the same code everywhere. It picks the right method automatically.

**The simple way to think about it:**
- Key = showing a password. If someone steals it, they get in.
- DefaultAzureCredential = showing your identity. There is nothing to steal.
