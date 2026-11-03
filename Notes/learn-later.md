# Learn Later

A running list of skills and topics to pick up after AI-102 is complete.

---

## Python — skills to learn next

These unlock stages 07–09 and make reading any new Azure SDK package easy. Learn in this order.

### 1. Functions — highest priority

All scripts so far run top-to-bottom as flat code. Real Python wraps logic into reusable `def` blocks. Once you can write functions, SDK documentation becomes readable because docs always show functions, not flat scripts.

```python
# flat (what you write now)
client = TextAnalyticsClient(...)
result = client.analyze_sentiment(...)
print(result)

# with a function (what to aim for)
def analyse_sentiment(text):
    client = TextAnalyticsClient(...)
    return client.analyze_sentiment([text])
```

Why it matters: every new package you pick up will show functions in its examples. If you can't write them, the docs look foreign.

---

### 2. `async` / `await`

Stages 07 and 08 (Azure OpenAI and agents) are almost entirely async. Without this, stage 07 will not make sense.

```python
import asyncio

async def call_openai():
    # async def = this function is asynchronous
    response = await client.chat.completions.create(...)
    # await = pause here and wait for the result without freezing the whole program
    return response

asyncio.run(call_openai())
# asyncio.run() starts the async engine and runs your function
```

---

### 3. `try` / `except` — error handling

Right now if an API call fails, the script crashes with a wall of text. One `try/except` block makes scripts robust.

```python
try:
    result = client.analyze_sentiment([text])
except Exception as e:
    # Exception is the base type for all errors
    # 'as e' gives you the error object so you can print what went wrong
    print(f"Call failed: {e}")
```

---

### 4. Classes — enough to read them, not write them

Every Azure SDK object is a class. When you see `self`, `__init__`, or method chaining in docs or error messages, you need to not be confused.

- `__init__` is the setup code that runs when you create an object
- `self` refers to the object itself
- You already use classes every time you write `client = SomeClient(...)` — you just haven't written one yourself

---

### 5. FastAPI — turn a script into a real service

Wrap your AI scripts in a REST API so they become callable services, not just terminal scripts.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/analyse")
def analyse(text: str):
    return {"sentiment": analyse_sentiment(text)}
```

Why it matters: closes the gap between "script" and "deployed application."

---

### What to skip for now

| Skill | Why to skip |
|---|---|
| Decorators (`@something`) | You'll see them but don't need to write them yet |
| Generators (`yield`) | Not relevant to Azure AI scripts |
| Type hints | Useful but not blocking |
| Full OOP design | Not needed until the end-to-end project |

---

## AI Engineering — skills to learn after AI-102

### 1. RAG — Retrieval Augmented Generation (highest priority)

Combine Azure AI Search (stage 06) + Azure OpenAI (stage 07) to build a system that answers questions from your own documents. This is the most-asked-about pattern in AI engineering interviews right now.

---

### 2. Agentic patterns

Stage 08 introduces this, but go deeper after. Learn how agents decide what tool to call, how to chain steps, and how to handle failures.

Options to pick one from:
- **Semantic Kernel** — Microsoft's framework, most Azure-native
- **LangChain / LangGraph** — popular in the broader market
- **Azure AI Agent Service** — managed, less code to write

---

### 3. Evaluation — how to measure if your AI is working

Most candidates skip this. Being able to score your model's answers for groundedness, relevance, and coherence shows engineering maturity.

Tools: Azure AI Evaluation, Promptflow.

---

### 4. Docker basics

Being able to containerise your app closes the last gap between "scripts" and "deployed application."

Goal: put your FastAPI app in a Docker container and deploy it to Azure Container Apps.

---

## The end-to-end project target

Once AI-102 stages are done, build one app that combines:
- Azure AI Search (RAG retrieval)
- Azure OpenAI (generation)
- FastAPI (REST endpoint)
- Docker + Container Apps (deployment)
- GitHub Actions (CI/CD)

That stack, on a public GitHub repo, answers "have you built anything real?" better than any additional certification.
