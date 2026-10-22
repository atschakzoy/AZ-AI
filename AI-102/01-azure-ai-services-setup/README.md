# Stage 01 — Microsoft Foundry & Foundry Tools: Setup, SDKs & Security

## What is this and why does it matter?

Every AI-102 topic uses Microsoft Foundry and Foundry Tools. Before you can call any of them, you need to know how to provision a Foundry resource, authenticate to it, call it from Python, and secure it properly.

This stage is the foundation for everything else in AI-102. Get this right and every other stage is just learning a new capability on top of the same pattern.

---

## What you will learn here

- What Foundry Tools is (the umbrella resource)
- How to provision Foundry Tools resources with the Azure CLI and Terraform
- How to authenticate with keys and with Managed Identity
- How to call Foundry Tools from Python using the SDK and REST
- How to secure Foundry Tools resources (Private Endpoints, network rules)
- How to monitor usage and set cost alerts

---

## Part 1 — Microsoft Foundry & Foundry Tools Overview

**Microsoft Foundry** is the unified platform for building AI apps and agents. It includes:
- Model deployments (GPT-4o, embeddings, DALL-E)
- **Foundry Tools** — the pre-built AI service APIs (Language, Speech, Vision, Document Intelligence, and more)
- Agent Service, evaluations, and tracing

**Foundry Tools** give you AI capabilities without training your own models — Language, Speech, Vision, Document Intelligence, and more.

**The two provisioning options:**

| Option | What it is | When to use |
|--------|-----------|------------|
| **Foundry resource (multi-service)** | One resource for all Foundry Tools | Development, when you use many services |
| **Single-service resource** | One resource for one specific service (e.g. only Language) | Production, for cost tracking and tighter access control |

Both give you an **endpoint URL** and **API keys** to authenticate. The underlying Azure resource type is `Microsoft.CognitiveServices/accounts` — this is the real Azure resource provider name and it has not changed, even though the service is now called Foundry Tools.

---

## Part 2 — Provisioning with Azure CLI

```bash
# NOTE: The CLI command is "az cognitiveservices" — this is the real Azure CLI command.
# It has not been renamed even though the service is now called Foundry Tools. Use it as-is.

# Create a multi-service Foundry Tools resource
az cognitiveservices account create \
  --name ai-myapp-dev \
  --resource-group rg-ai-dev \
  --kind CognitiveServices \
  --sku S0 \
  --location eastus \
  --yes

# Get the endpoint
az cognitiveservices account show \
  --name ai-myapp-dev \
  --resource-group rg-ai-dev \
  --query "properties.endpoint" -o tsv

# Get the key
az cognitiveservices account keys list \
  --name ai-myapp-dev \
  --resource-group rg-ai-dev \
  --query "key1" -o tsv
```

**Single-service examples (`--kind` values):**
- `TextAnalytics` — Foundry Tools Language
- `ComputerVision` — Foundry Tools Vision
- `SpeechServices` — Foundry Tools Speech
- `FormRecognizer` — Foundry Tools Document Intelligence
- `OpenAI` — Azure OpenAI

---

## Part 3 — Provisioning with Terraform

```hcl
resource "azurerm_cognitive_account" "ai" {
  name                = "ai-${var.workload}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  kind                = "CognitiveServices"
  sku_name            = "S0"

  identity {
    type = "SystemAssigned"
  }

  network_acls {
    default_action = "Deny"
    ip_rules       = [var.allowed_ip]
  }
}

output "ai_endpoint" {
  value = azurerm_cognitive_account.ai.endpoint
}
```

---

## Part 4 — Authentication: Keys vs Managed Identity

**Option 1: API Keys (simple, not recommended for production)**

```python
import os
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

endpoint = os.environ["AI_ENDPOINT"]
key = os.environ["AI_KEY"]

client = TextAnalyticsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)
```

Never hardcode keys. Always use environment variables or Key Vault.

**Option 2: Managed Identity (recommended for production)**

No keys needed — your Azure resource (App Service, Container App, VM) authenticates automatically.

```python
import os
from azure.ai.textanalytics import TextAnalyticsClient
from azure.identity import DefaultAzureCredential

endpoint = os.environ["AI_ENDPOINT"]

client = TextAnalyticsClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential()
)
```

`DefaultAzureCredential` tries multiple auth methods in order:
1. Environment variables (for CI/CD)
2. Managed Identity (for Azure-hosted apps)
3. Azure CLI login (for local development)

You write the same code everywhere — it picks the right method automatically.

**RBAC role for Managed Identity access to Foundry Tools:**
`Foundry User` — grants permission to call the Foundry Tools APIs.

```bash
az role assignment create \
  --assignee <managed-identity-object-id> \
  --role "Foundry User" \
  --scope /subscriptions/.../resourceGroups/.../providers/Microsoft.CognitiveServices/accounts/ai-myapp-dev
```

---

## Part 5 — Making Your First Call (Python SDK Pattern)

Every Azure AI SDK follows the same pattern:

```python
from azure.ai.textanalytics import TextAnalyticsClient
from azure.identity import DefaultAzureCredential
import os

# 1. Create client
client = TextAnalyticsClient(
    endpoint=os.environ["AI_ENDPOINT"],
    credential=DefaultAzureCredential()
)

# 2. Call the service
documents = ["Azure AI Services are incredibly powerful."]
result = client.analyze_sentiment(documents)

# 3. Process result
for doc in result:
    print(f"Sentiment: {doc.sentiment}")
    print(f"Confidence: {doc.confidence_scores}")
```

**Install the SDKs:**
```bash
pip install azure-ai-textanalytics azure-ai-vision-imageanalysis azure-cognitiveservices-speech
pip install azure-identity  # always needed for auth
```

---

## Part 6 — Securing Foundry Tools

**Network security:**

```bash
# Disable public access — only allow specific IPs or VNets
az cognitiveservices account update \
  --name ai-myapp-dev \
  --resource-group rg-ai-dev \
  --default-action Deny

# Allow a specific IP
az cognitiveservices account network-rule add \
  --name ai-myapp-dev \
  --resource-group rg-ai-dev \
  --ip-address 203.0.113.10
```

**Private Endpoint** — the AI service gets a private IP inside your VNet. Traffic never leaves Microsoft's network.

```hcl
resource "azurerm_private_endpoint" "ai" {
  name                = "pe-ai-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  subnet_id           = var.private_subnet_id

  private_service_connection {
    name                           = "ai-connection"
    private_connection_resource_id = azurerm_cognitive_account.ai.id
    subresource_names              = ["account"]
    is_manual_connection           = false
  }
}
```

---

## Part 7 — Monitoring Usage

```bash
# View metrics in CLI
az monitor metrics list \
  --resource /subscriptions/.../cognitiveservices/accounts/ai-myapp-dev \
  --metric "TotalCalls,TotalErrors" \
  --interval PT1H

# Set a cost alert
az consumption budget create \
  --budget-name ai-monthly-budget \
  --amount 50 \
  --time-grain Monthly \
  --category Cost
```

---

## AI-102 Exam Checklist — Foundry Tools Setup

- [ ] What is the difference between a multi-service and single-service AI resource?
- [ ] What two things do you always need to call an AI service? (endpoint + key/credential)
- [ ] What is the difference between key authentication and Managed Identity?
- [ ] What does `DefaultAzureCredential` do and why is it useful?
- [ ] What RBAC role does a Managed Identity need to call AI services?
- [ ] What does a Private Endpoint do for an AI service?
- [ ] How do you disable public access to an AI service?

---

## Exercises

1. Create an Azure AI multi-service resource using the CLI. Save the endpoint and key to environment variables.
2. Install `azure-ai-textanalytics` and `azure-identity`. Write a Python script that calls sentiment analysis using `DefaultAzureCredential` locally (it will use your CLI login).
3. Create the same resource with Terraform. Add `identity { type = "SystemAssigned" }`.
4. Assign the `Foundry User` role to your own user identity and test calling without a key.
5. Set `default_action = "Deny"` in your Terraform config and redeploy. Confirm you can no longer call the service from a public IP.
