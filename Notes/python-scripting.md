# Python Scripting — Concepts & Patterns

A running reference of Python concepts used in this project, explained plainly.

---

## for loops — what the variable actually is

When you write `for x in some_list:`, the variable `x` is just a name you chose. Python takes the first item out of the list and puts it into `x`. Then the second item, and so on.

**The variable is whatever the list contains.** If the list contains strings, `x` is a string. If the list contains objects, `x` is an object.

```python
# List of strings — name is a string each time
names = ["Alice", "Bob"]
for name in names:
    print(name.upper())   # .upper() works because strings have that method

# List of objects — doc is an object each time
result = client.analyze_sentiment(documents)
for doc in result:
    print(doc.sentiment)  # .sentiment works because the object has that attribute
```

The SDK returns a list of **result objects** — not strings. So `doc` is a result object from the moment the loop hands it to you. You did not make it an object — it already was one, sitting inside `result`.

**The levels in an NLP result:**

```
documents = ["The food was amazing. But the service was really slow."]
                ↓
result          ← list with one item (one item per text you sent)
  └── doc       ← the result for the whole text (both sentences together)
        ├── doc.sentiment          overall label: "negative"
        ├── doc.confidence_scores  {positive: 0.05, negative: 0.94}
        └── doc.sentences          list of sentence results
              ├── sentence 1 → "The food was amazing."   → positive
              └── sentence 2 → "But the service was really slow." → negative
```

| Loop | What each item is |
|---|---|
| `for doc in result` | the result for one full text (everything in one slot of your list) |
| `for sentence in doc.sentences` | one sentence inside that text |

---

## Python Lingo — the correct words for things

When talking to other developers, use these words. They are not interchangeable.

| Word | What it means | Example |
|---|---|---|
| **Package / SDK** | The thing you `pip install` — a collection of files Microsoft (or anyone) wrote and published | `azure-ai-textanalytics` |
| **Module** | A single `.py` file — either inside an SDK, or one you write yourself | `nlp.py` is your module. `azure/ai/textanalytics/__init__.py` is Microsoft's |
| **Class** | A blueprint for creating objects — defines what data and methods an object has | `TextAnalyticsClient` |
| **Instance** | One specific object created from a class — has its own endpoint and credential | `client = TextAnalyticsClient(...)` — `client` is an instance |
| **Method** | A function that belongs to a class — you call it on an instance | `client.analyze_sentiment(...)` |
| **Function** | A standalone piece of code, not attached to a class | `load_dotenv()` |
| **Attribute** | A value stored on an object — you read it with a dot | `doc.sentiment`, `entity.category` |

**How to say it correctly in a sentence:**

> "I imported the `TextAnalyticsClient` **class** from the `azure-ai-textanalytics` **package**. I created a **client instance** from it and I call its **methods** — like `analyze_sentiment` and `extract_key_phrases`. Each method returns a result object and I read the result's **attributes** like `.sentiment` or `.key_phrases`."

---

## Method vs Attribute — how to tell them apart instantly

One rule: **parentheses = method, no parentheses = attribute.**

```python
client.analyze_sentiment(documents)   # method — has (), runs code, returns something
client.extract_key_phrases(documents) # method — has (), runs code, returns something

doc.sentiment        # attribute — no (), just holds a value, you read it
doc.confidence_scores  # attribute — no ()
entity.text          # attribute — no ()
entity.category      # attribute — no ()
```

Methods *do* something. Attributes *hold* something.

Think of it like a person:
- **Method** → `person.run()` — an action, has to be triggered
- **Attribute** → `person.name` — a fact stored on the object, always there to read

---

## Synchronous vs Long-running operations

Two types of SDK calls. The method name tells you which one it is.

**Synchronous** — no `begin_`, returns the result directly, your script waits inline:

```python
result = client.analyze_sentiment(documents)   # done immediately
```

Everything runs in order. Azure responds in milliseconds. You get the result on the same line.

**Long-running** — starts with `begin_`, returns a poller, Azure runs the job in the background:

```python
poller = client.begin_analyze_actions(documents, actions=[...])
result = poller.result()   # this line blocks — waits until Azure finishes
```

- `poller` — an object that tracks the background job. It knows the job ID and how to check Azure for status.
- `poller.result()` — the line that actually waits. Called **blocking** — it stops your script until Azure is done, then returns the results.
- Any method starting with `begin_` is a long-running operation.

**Why does summarisation need this?** Sending one sentence takes milliseconds. Sending a 50-page document takes seconds. If the SDK waited inline, your script would freeze with no feedback. The poller lets Azure run the job on their servers while your script stays in control.

**The restaurant analogy:**

| Step | Restaurant | Code |
|---|---|---|
| Place order | `begin_analyze_actions(...)` | starts the job |
| Get a buzzer | `poller` | object that tracks the job |
| Buzzer goes off | `poller.result()` returns | Azure finished |
| Pick up food | loop through results | read the output |

**There is also a third type — async/await** — which you will see in web frameworks and production code. It is more advanced: your script can do many things at once without blocking at all. You are not using it here, but now you know the word when you see it.

| Type | How you call it | Returns |
|---|---|---|
| Synchronous | `client.method(...)` | result directly |
| Long-running | `client.begin_method(...)` | poller — call `.result()` to wait |
| Async | `await client.method(...)` | result, but only inside `async` functions |

---

## One text vs multiple texts — how the list works

Every Language service method takes a **list** of texts, even if you only have one:

```python
documents = ["one sentence here"]         # one item — result has one item
documents = ["text one", "text two"]      # two items — result has two items
```

**Mixing languages in one string** gives Azure one text to analyse — it picks the dominant language and ignores the rest.

**Separate strings** give Azure separate texts — one result per string, one language detected per string.

---

## Imports

```python
import os
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
```

`import` brings in code that someone else wrote so you can use it in your script.

- `import os` — gives you access to the operating system, mainly used here to read environment variables
- `from dotenv import load_dotenv` — from the `dotenv` package, bring in just the `load_dotenv` function
- `from azure.ai.textanalytics import TextAnalyticsClient` — from Azure's SDK package, bring in the client class for the Language service
- `from azure.core.credentials import AzureKeyCredential` — bring in the class that wraps your API key so Azure accepts it

The difference between `import X` and `from X import Y`:
- `import os` — imports the whole `os` module, you then call `os.environ`
- `from dotenv import load_dotenv` — imports only `load_dotenv` from `dotenv`, you call it directly as `load_dotenv()` without the prefix

---

## Loading environment variables

```python
load_dotenv()
```

Reads your `.env` file and loads all the `KEY=value` pairs into the environment. After this line runs, your script can access them with `os.environ`.

Without this line, `os.environ["FOUNDRY_ENDPOINT"]` would fail because the values from `.env` are not loaded automatically.

```python
endpoint = os.environ["FOUNDRY_ENDPOINT"]
key = os.environ["FOUNDRY_KEY"]
```

`os.environ` is a dictionary (a collection of key-value pairs) that holds all environment variables. `["FOUNDRY_ENDPOINT"]` reads the value for that key.

If the key does not exist, Python raises an error immediately — which is good, because it means you will know straight away if something is missing.

---

## Creating a client

```python
client = TextAnalyticsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)
```

A **client** is an object that handles communication with the Azure service. You create it once and then use it to make all your API calls.

- `TextAnalyticsClient(...)` — creates a new client object for the Language service
- `endpoint=endpoint` — tells the client which URL to send requests to
- `credential=AzureKeyCredential(key)` — wraps your key in a format Azure expects for authentication
- The client does not make any network call here — it just sets up the connection details

---

## Calling the API

```python
documents = ["I love building AI apps on Azure"]
result = client.analyze_sentiment(documents)
```

- `documents` — a list (square brackets `[]`) of strings. The API accepts multiple texts at once, so it always expects a list even if you only send one
- `client.analyze_sentiment(documents)` — sends the documents to Azure and waits for the response. The result comes back as a list of objects, one per document

---

## Looping through results

```python
for doc in result:
    print(f"Sentiment: {doc.sentiment}")
    print(f"Positive score: {doc.confidence_scores.positive}")
    print(f"Negative score: {doc.confidence_scores.negative}")
    print(f"Neutral scores: {doc.confidence_scores.neutral}")
```

`for doc in result` — loops through every item in the result list. Since we sent one document, this runs once. If you sent three documents, it would run three times.

`doc.sentiment` — accesses the `sentiment` property on the result object. Python uses `.` to access properties on objects.

`f"Sentiment: {doc.sentiment}"` — an f-string (formatted string). The `f` before the quote tells Python to treat anything inside `{}` as a variable and replace it with its value when printing.

`doc.confidence_scores.positive` — a chain of properties. `doc` has a `confidence_scores` object, and that object has a `positive` property with a number between 0 and 1.

---

## Structured request objects (Content Safety pattern)

```python
from azure.ai.contentsafety.models import AnalyzeTextOptions

request = AnalyzeTextOptions(text="some text here")
response = client.analyze_text(request)
```

Some Azure SDK methods accept a plain list (like `analyze_sentiment`). Others require a structured object — you create the object first, then pass it to the method.

`AnalyzeTextOptions(text=...)` — wraps your text into a structured object the Content Safety API expects. The named argument `text=` tells Python which field you are setting.

This pattern appears across many Azure SDKs — when a plain list is not enough and you need to pass multiple fields or options.

---

## Classes, methods, and properties

In the Azure SDKs, three things appear constantly — classes, methods, and properties. They are different:

**Class** — a blueprint for an object. You create an instance of it by calling it like a function:
```python
client = ContentSafetyClient(endpoint=endpoint, credential=DefaultAzureCredential())
request = AnalyzeTextOptions(text="...")
```
`ContentSafetyClient` and `AnalyzeTextOptions` are classes. `client` and `request` are the objects you created from them.

**Method** — a function that belongs to a class. You call it on the object using a dot `.`:
```python
response = client.analyze_text(request)
response = client.send_request(http_request)
```
`analyze_text` and `send_request` are methods. The dot means "call this method on this object."

**Property** — a value stored inside an object. You also access it with a dot:
```python
response.user_prompt_analysis.attack_detected
category.severity
```
No parentheses `()` — you are reading a value, not calling a function.

**These are not built into Python** — they come from the `azure-ai-contentsafety` library that Microsoft wrote. When you `from azure.ai.contentsafety import ContentSafetyClient`, you import their class. Your code calls Microsoft's code, which calls their API endpoint, which runs their ML model, and returns a structured response object.

---

## SDK inheritance — send_request

Every Azure SDK client inherits from a base class in `azure-core`. This gives every client two methods for free — not just the service-specific ones:

```
azure-core (base)
    └── send_request()    ← available on ALL Azure SDK clients
    └── close()           ← available on ALL Azure SDK clients

ContentSafetyClient
    ├── analyze_text()    ← specific to Content Safety
    ├── analyze_image()   ← specific to Content Safety
    ├── send_request()    ← inherited from azure-core base
    └── close()           ← inherited from azure-core base
```

**When to use `send_request`:** When the SDK wrapper does not yet support a feature that the REST API already has. You build the HTTP request manually and the client still handles authentication for you.

```python
from azure.core.rest import HttpRequest
import json

body = {"userPrompt": "...", "documents": ["..."]}

http_request = HttpRequest(
    method="POST",
    url=f"{endpoint}contentsafety/text:shieldPrompt",
    params={"api-version": "2024-02-15-preview"},
    headers={"Content-Type": "application/json"},
    content=json.dumps(body)
)

response = client.send_request(http_request)
response.raise_for_status()    # raises an error if the API returned a failure status
result = response.json()       # parses the JSON body into a Python dictionary
```

**Dictionary access vs dot notation:**

When the SDK gives you a typed object, you use dots:
```python
response.user_prompt_analysis.attack_detected
```

When `send_request` gives you a raw JSON dictionary, you use square brackets and quoted key names:
```python
result['userPromptAnalysis']['attackDetected']
```

The REST API uses camelCase key names (`userPromptAnalysis`). The SDK wrapper would have translated these to snake_case (`user_prompt_analysis`) — but since we are bypassing the wrapper, we use the raw camelCase names from the API.

---

## Building a request body — nested dictionaries

When calling the REST API with `send_request`, you build the request data as a Python dictionary. Dictionaries can be nested — a value inside a dictionary can itself be another dictionary, or a list.

```python
body = {
    "domain": "Generic",          # string value
    "task": "QnA",                # string value
    "qna": {                      # nested dictionary — a dict inside a dict
        "query": "What is the return policy?"
    },
    "text": "Returns are accepted within 60 days.",
    "groundingSources": [         # list value — square brackets contain items
        "Our return policy allows customers to return items within 30 days."
    ]
}
```

**Dictionary** — curly braces `{}`, holds key-value pairs. Keys are always strings in JSON. Values can be strings, numbers, booleans, lists, or other dictionaries.

**Nested dictionary** — `"qna": { "query": "..." }` — the value for the key `"qna"` is itself a dictionary. This creates a hierarchy: `body["qna"]["query"]` reads the query field.

**List inside a dictionary** — `"groundingSources": [...]` — the value is a list. Square brackets `[]` hold the items. You can have multiple sources: `["source one", "source two"]`.

This structure maps directly to JSON — `json.dumps(body)` converts it exactly as written. Azure receives the same structure and reads each field by name.

---

## HttpRequest — building a raw HTTP request

`HttpRequest` is a class from `azure.core.rest`. You use it when the SDK does not have a wrapper for a feature — you describe the HTTP request yourself and send it via `client.send_request()`.

```python
from azure.core.rest import HttpRequest
import json

http_request = HttpRequest(
    method="POST",
    url=f"{endpoint}contentsafety/text:shieldPrompt",
    params={"api-version": "2024-02-15-preview"},
    headers={"Content-Type": "application/json"},
    content=json.dumps(body)
)
```

**Each field explained:**

| Field | What it does |
|---|---|
| `method` | The HTTP verb — `"POST"` sends data to the server, `"GET"` retrieves data. Azure AI APIs always use `POST` |
| `url` | The full endpoint URL. Built by combining `endpoint` (from your .env) + the API path for the specific feature |
| `params` | Query string parameters added to the URL. `api-version` tells Azure which version of the API to use — different versions have different features |
| `headers` | Metadata about your request. `Content-Type: application/json` tells Azure the body is JSON, not plain text or a file |
| `content` | The request body — the data you are sending. Must be a string, so `json.dumps(body)` converts your Python dictionary into a JSON string |

**What `json.dumps` does:**

```python
body = {"userPrompt": "hello", "documents": ["some text"]}
json.dumps(body)
# produces the string: '{"userPrompt": "hello", "documents": ["some text"]}'
```

`json.dumps` = "JSON dump to string". It converts a Python dictionary into a JSON-formatted string. Azure expects JSON, not a Python object.

---

## Groundedness Detection — request body fields

Groundedness Detection has specific fields that tell the API what kind of content it is checking:

**`domain`** — the subject area of the content:
| Value | When to use |
|---|---|
| `"Generic"` | General content — product descriptions, FAQs, general knowledge |
| `"Medical"` | Medical content — clinical notes, health information |

**`task`** — the type of AI output being checked:
| Value | When to use |
|---|---|
| `"QnA"` | The AI answered a question. Include a `qna.query` field with the original question |
| `"Summarization"` | The AI summarised a document. No query needed |

**`text`** — the AI's output (the answer or summary being checked for groundedness)

**`groundingSources`** — a list of the source documents the AI was supposed to base its answer on. The API compares `text` against these.

**`qna.query`** — (only for `task: QnA`) the original question the user asked. Helps the API understand what the answer was trying to address.

**Full example for QnA:**
```python
body = {
    "domain": "Generic",
    "task": "QnA",
    "qna": {
        "query": "What is the return policy?"
    },
    "text": "Returns are accepted within 60 days.",
    "groundingSources": [
        "Our return policy allows customers to return items within 30 days of purchase."
    ]
}
```

**Response fields:**
```python
result['ungroundedDetected']      # True if the answer is not supported by the sources
result['ungroundedPercentage']    # 0.0 to 1.0 — how much of the answer is ungrounded
result['ungroundedDetails']       # list of specific phrases that are ungrounded
```

---

## PII Detection pattern

PII uses `TextAnalyticsClient` from `azure-ai-textanalytics`. The method accepts a list of strings and returns one result object per document.

```python
documents = ["My name is Reza Nazari, my email is reza@example.com."]

response = client.recognize_pii_entities(documents)

for doc in response:
    print(doc.redacted_text)
    for entity in doc.entities:
        print(f"{entity.category}: {entity.text} (confidence: {entity.confidence_score:.2f})")
```

**Properties on the result object (`doc`):**

| Property | What it contains |
|---|---|
| `doc.redacted_text` | The original text with PII replaced by `****` — Microsoft builds this for you |
| `doc.entities` | List of detected PII items — one object per entity found |

**Properties on each entity:**

| Property | What it contains |
|---|---|
| `entity.category` | Type of PII — `"Person"`, `"Email"`, `"PhoneNumber"`, `"Address"`, etc. |
| `entity.text` | The exact text that was flagged |
| `entity.confidence_score` | 0.0 to 1.0 — how confident the model is. `0.99` = very confident |

**The `:.2f` format specifier:**

```python
print(f"Confidence: {entity.confidence_score:.2f}")
# prints: Confidence: 0.99
```

Inside an f-string, `:` after the variable name starts a format spec. `.2f` means: format as a float (`f`) with 2 decimal places (`.2`). Without it, you might get `0.9876543` — with it you get `0.99`. Use this whenever printing scores or percentages.

---

## Looping through a list of category results

```python
for category in response.categories_analysis:
    print(f"{category.category}: severity {category.severity}")
```

`response.categories_analysis` — a list of four objects, one per harm category (Hate, Violence, Sexual, SelfHarm). The API always returns all four regardless of the input.

`category.category` — the name of the harm category as a string ("Hate", "Violence", etc.)

`category.severity` — the severity score as an integer: 0, 2, 4, or 6.

This is the same `for` loop pattern as sentiment.py — loop through a list, read properties off each item.

---

## Real-world example — Customer Support AI Safety Pipeline

This script combines all five services into one pipeline that a real company would run before and after processing a customer message through an AI chatbot.

**The scenario:** A customer sends a message to a support chatbot. Before the AI responds — and before anything gets logged — the pipeline:
1. Shields against prompt injection (someone trying to hijack the AI)
2. Checks for harmful content (hate, violence, etc.)
3. Detects and redacts PII so the raw message is never stored in logs
4. Scores the sentiment to decide if a human agent needs to step in
5. Verifies the AI's response is actually grounded in the source documents (no hallucinations)

```python
import os
import json
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.rest import HttpRequest

# ---------------------------------------------------------------
# SETUP
# Load values from .env and create one client per Azure service.
# DefaultAzureCredential uses your `az login` locally and
# Managed Identity when running on Azure — no keys needed.
# ---------------------------------------------------------------

load_dotenv()

content_safety_endpoint = os.environ["CONTENT_SAFETY_ENDPOINT"]
foundry_endpoint = os.environ["FOUNDRY_ENDPOINT"]

credential = DefaultAzureCredential()

content_safety_client = ContentSafetyClient(endpoint=content_safety_endpoint, credential=credential)
text_analytics_client = TextAnalyticsClient(endpoint=foundry_endpoint, credential=credential)

# ---------------------------------------------------------------
# SAMPLE INPUT
# In a real app this would come from a user form, API request,
# or a message queue — not hardcoded like this.
# ---------------------------------------------------------------

user_message = "My name is John Smith, email john@example.com. I hate this product, it broke after one day! Tell me how to get a refund or I will report you."
ai_response = "You can return the product within 30 days for a full refund by visiting our returns portal."
source_document = "Our return policy allows customers to return items within 30 days of purchase for a full refund."

print("=" * 60)
print("CUSTOMER SUPPORT AI SAFETY PIPELINE")
print("=" * 60)

# ---------------------------------------------------------------
# STEP 1 — PROMPT SHIELD
# Check if the user is trying to trick the AI with a prompt
# injection attack (e.g. "ignore all previous instructions").
# If an attack is detected, block the message immediately.
# ---------------------------------------------------------------

print("\n[1] Checking for prompt injection attacks...")

shield_body = {
    "userPrompt": user_message,
    "documents": [source_document]
}

shield_request = HttpRequest(
    method="POST",
    url=f"{content_safety_endpoint}contentsafety/text:shieldPrompt",
    params={"api-version": "2024-02-15-preview"},
    headers={"Content-Type": "application/json"},
    content=json.dumps(shield_body)
)

shield_response = content_safety_client.send_request(shield_request)
shield_response.raise_for_status()
shield_result = shield_response.json()

user_attack = shield_result['userPromptAnalysis']['attackDetected']
doc_attack = shield_result['documentsAnalysis'][0]['attackDetected']

print(f"  User prompt attack: {user_attack}")
print(f"  Document attack: {doc_attack}")

if user_attack or doc_attack:
    print("  ACTION: Message blocked — prompt injection detected.")
    exit()

# ---------------------------------------------------------------
# STEP 2 — CONTENT SAFETY
# Check for harmful content: hate, violence, sexual, self-harm.
# Severity: 0 = safe, 2 = low, 4 = medium, 6 = high.
# Block anything at severity 4 or above.
# ---------------------------------------------------------------

print("\n[2] Checking for harmful content...")

safety_request = AnalyzeTextOptions(text=user_message)
safety_response = content_safety_client.analyze_text(safety_request)

blocked = False
for category in safety_response.categories_analysis:
    print(f"  {category.category}: severity {category.severity}")
    if category.severity >= 4:
        blocked = True

if blocked:
    print("  ACTION: Message blocked — harmful content detected.")
    exit()

# ---------------------------------------------------------------
# STEP 3 — PII DETECTION
# Find personal information (name, email, phone) in the message.
# Log only the redacted version — never store raw PII in logs.
# ---------------------------------------------------------------

print("\n[3] Detecting PII...")

pii_response = text_analytics_client.recognize_pii_entities([user_message])

for doc in pii_response:
    print(f"  Redacted for logging: {doc.redacted_text}")
    for entity in doc.entities:
        print(f"  Found: {entity.category} — '{entity.text}' (confidence: {entity.confidence_score:.2f})")

# ---------------------------------------------------------------
# STEP 4 — SENTIMENT ANALYSIS
# Score the emotional tone: positive, neutral, or negative.
# If strongly negative, flag for escalation to a human agent.
# ---------------------------------------------------------------

print("\n[4] Analysing sentiment...")

sentiment_response = text_analytics_client.analyze_sentiment([user_message])

for doc in sentiment_response:
    print(f"  Sentiment: {doc.sentiment}")
    print(f"  Positive: {doc.confidence_scores.positive:.2f}")
    print(f"  Negative: {doc.confidence_scores.negative:.2f}")
    print(f"  Neutral:  {doc.confidence_scores.neutral:.2f}")

    if doc.sentiment == "negative" and doc.confidence_scores.negative > 0.8:
        print("  ACTION: High-priority ticket — escalate to human agent.")

# ---------------------------------------------------------------
# STEP 5 — GROUNDEDNESS CHECK
# Before sending the AI's response to the customer, verify it is
# actually supported by the source document.
# This catches hallucinations — things the AI made up.
# ---------------------------------------------------------------

print("\n[5] Checking AI response groundedness...")

groundedness_body = {
    "domain": "Generic",
    "task": "QnA",
    "qna": {
        "query": user_message
    },
    "text": ai_response,
    "groundingSources": [source_document]
}

groundedness_request = HttpRequest(
    method="POST",
    url=f"{content_safety_endpoint}contentsafety/text:detectGroundedness",
    params={"api-version": "2024-02-15-preview"},
    headers={"Content-Type": "application/json"},
    content=json.dumps(groundedness_body)
)

groundedness_response = content_safety_client.send_request(groundedness_request)
groundedness_response.raise_for_status()
groundedness_result = groundedness_response.json()

print(f"  Ungrounded detected: {groundedness_result['ungroundedDetected']}")
print(f"  Ungrounded percentage: {groundedness_result['ungroundedPercentage']}")

if groundedness_result['ungroundedDetected']:
    print("  ACTION: AI response blocked — not supported by source documents.")
else:
    print("  AI response is safe to send to the customer.")

print("\n" + "=" * 60)
print("Pipeline complete.")
print("=" * 60)
```
