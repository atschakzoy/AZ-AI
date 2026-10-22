# Python Scripting — Concepts & Patterns

A running reference of Python concepts used in this project, explained plainly.

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
