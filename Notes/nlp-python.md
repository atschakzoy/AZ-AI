# NLP Solutions — Python Patterns

Python concepts and patterns introduced in Stage 04. Builds on the patterns in `python-scripting.md`.

---

## What attributes does each method give you

Every method returns a list of result objects — one per text you sent. Each result object has attributes you can read. Here are the useful ones.

**`analyze_sentiment`**

| Attribute | What it is |
|---|---|
| `doc.sentiment` | Overall label — `"positive"`, `"negative"`, `"neutral"`, `"mixed"` |
| `doc.confidence_scores.positive` | Probability 0.0–1.0 (positive + negative + neutral always = 1.0) |
| `doc.confidence_scores.negative` | Same |
| `doc.confidence_scores.neutral` | Same |
| `doc.sentences` | List of sentence results — loop through it |
| `sentence.text` | The sentence as it appeared in your text |
| `sentence.sentiment` | Label for just that sentence |

**`extract_key_phrases`**

| Attribute | What it is |
|---|---|
| `doc.key_phrases` | A list of strings — the main topics Azure found |

**`recognize_entities`**

| Attribute | What it is |
|---|---|
| `doc.entities` | List of entity results — loop through it |
| `entity.text` | The exact word or phrase from your text |
| `entity.category` | Type: `Person`, `Location`, `Organization`, `DateTime`, `Quantity`, etc. |
| `entity.subcategory` | More specific type if available, e.g. `City` under `Location` |
| `entity.confidence_score` | 0.0–1.0 |
| `entity.offset` | Character position where the entity starts in the original text |

**`recognize_linked_entities`**

| Attribute | What it is |
|---|---|
| `doc.entities` | List of linked entity results — loop through it |
| `entity.name` | The canonical Wikipedia article name |
| `entity.url` | The full Wikipedia URL |
| `entity.data_source` | Usually `"Wikipedia"` |
| `entity.matches` | List of places in the text where this entity appeared |
| `match.text` | The exact text as it appeared |
| `match.confidence_score` | 0.0–1.0 |

**`detect_language`**

| Attribute | What it is |
|---|---|
| `doc.primary_language.name` | Full name — `"French"`, `"English"`, `"Arabic"` |
| `doc.primary_language.iso6391_name` | Two-letter code — `"fr"`, `"en"`, `"ar"` |
| `doc.primary_language.confidence_score` | 0.0–1.0 |

**On every result object (all methods)**

| Attribute | What it is |
|---|---|
| `doc.is_error` | `True` if this document failed. Always check before reading other attributes. |
| `doc.error` | The error details if `is_error` is `True` |

---

## Imports

```python
import os
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
```

- `TextAnalyticsClient` — the single client class for all Language service capabilities. From `azure-ai-textanalytics`.
- `AzureKeyCredential` — wraps an API key for authentication. Modern SDK pattern — same as Content Safety in Stage 02.

---

## Client Setup

```python
load_dotenv()

endpoint = os.environ["FOUNDRY_ENDPOINT"]
key = os.environ["FOUNDRY_KEY"]

client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))
```

- Same endpoint and key as Stage 02 — the multi-service account covers all Language capabilities.
- `AzureKeyCredential(key)` — wraps the key. The client uses it to authenticate every request automatically.

---

## How Text is Sent — Always a List

Every Language service method takes a **list of strings**, not a single string. This is because the API is designed to process batches — you can send multiple texts in one call and get results back for each.

```python
documents = ["I love this product. The quality is amazing!"]
result = client.analyze_sentiment(documents)
```

Even if you only have one piece of text, you still wrap it in a list: `["your text here"]`. The result is also always a list — one result per input document.

---

## Iterating Results

```python
for doc in result:
    if not doc.is_error:
        print(doc.sentiment)
    else:
        print(f"Error: {doc.error.message}")
```

- `for doc in result` — loops through one result per input document. If you sent 3 texts, you get 3 result objects.
- `doc.is_error` — `True` if this document failed to process (too long, unsupported language, etc.). Always check before reading the result.
- `doc.sentiment` — available when the call was `analyze_sentiment`. Other methods have different properties.

---

## Sentiment Analysis

```python
documents = ["The hotel was wonderful but the breakfast was disappointing."]
result = client.analyze_sentiment(documents, show_opinion_mining=True)

for doc in result:
    if not doc.is_error:
        print(f"Overall: {doc.sentiment}")
        print(f"Positive: {doc.confidence_scores.positive:.2f}")
        print(f"Negative: {doc.confidence_scores.negative:.2f}")

        for sentence in doc.sentences:
            print(f"  Sentence: {sentence.text}")
            print(f"  Sentiment: {sentence.sentiment}")
```

- `analyze_sentiment(documents)` — sends text and returns sentiment at document and sentence level.
- `show_opinion_mining=True` — optional parameter that enables Opinion Mining. Returns which part of the text the sentiment is about.
- `doc.sentiment` — the overall label: `"positive"`, `"negative"`, `"neutral"`, or `"mixed"`.
- `doc.confidence_scores.positive` — the probability for positive (0.0 to 1.0). `.positive`, `.negative`, `.neutral` always sum to 1.0.
- `doc.sentences` — a list of sentence-level results. Each sentence has its own `.sentiment` and `.confidence_scores`.
- `:.2f` — formats a float to 2 decimal places: `0.9234` → `0.92`.

---

## Opinion Mining (extension of Sentiment)

When `show_opinion_mining=True`, each sentence can have opinion targets:

```python
for sentence in doc.sentences:
    for assessment in sentence.mined_opinions:
        target = assessment.target
        print(f"Target: {target.text} — {target.sentiment}")
        for opinion in assessment.assessments:
            print(f"  Opinion: {opinion.text} ({opinion.sentiment})")
```

- `sentence.mined_opinions` — a list of opinion mining results in this sentence. Empty if no opinion target was found.
- `assessment.target` — the *thing* being talked about (e.g. "breakfast", "service", "room").
- `target.sentiment` — whether the opinion about that target is positive or negative.
- `assessment.assessments` — the descriptive words used (e.g. "wonderful", "disappointing").

---

## Key Phrase Extraction

```python
documents = ["The weather in London has been terrible this week. Rain every day."]
result = client.extract_key_phrases(documents)

for doc in result:
    if not doc.is_error:
        print(f"Key phrases: {doc.key_phrases}")
```

- `extract_key_phrases(documents)` — finds the main topics in the text.
- `doc.key_phrases` — a list of strings. e.g. `["weather", "London", "terrible", "Rain"]`.

---

## Named Entity Recognition (NER)

```python
documents = ["Elon Musk founded SpaceX in 2002 in Hawthorne, California."]
result = client.recognize_entities(documents)

for doc in result:
    if not doc.is_error:
        for entity in doc.entities:
            print(f"{entity.text} — {entity.category} ({entity.confidence_score:.2f})")
```

- `recognize_entities(documents)` — finds named things in the text and classifies them.
- `doc.entities` — a list of entity objects found in this document.
- `entity.text` — the exact text as it appeared: `"Elon Musk"`.
- `entity.category` — the type: `"Person"`, `"Location"`, `"Organization"`, `"DateTime"`, etc.
- `entity.confidence_score` — 0.0 to 1.0. How confident Azure is in the classification.
- `entity.offset` — character position where this entity starts in the original text.

---

## Entity Linking

```python
documents = ["I visited the Colosseum last summer. It was built in ancient Rome."]
result = client.recognize_linked_entities(documents)

for doc in result:
    if not doc.is_error:
        for entity in doc.entities:
            print(f"{entity.name} → {entity.url}")
            print(f"  Data source: {entity.data_source}")
            for match in entity.matches:
                print(f"  Matched text: '{match.text}' (score: {match.confidence_score:.2f})")
```

- `recognize_linked_entities(documents)` — finds entities and links them to Wikipedia.
- `entity.name` — the canonical name (Wikipedia article title), e.g. `"Colosseum"`.
- `entity.url` — the full Wikipedia URL.
- `entity.data_source` — usually `"Wikipedia"`.
- `entity.matches` — a list of places in the text where this entity appeared (the same entity can be mentioned multiple times).
- `match.text` — the exact text as it appeared in the document.
- `match.confidence_score` — confidence this text refers to the linked entity.

---

## Language Detection

```python
documents = ["Bonjour, comment allez-vous?"]
result = client.detect_language(documents)

for doc in result:
    if not doc.is_error:
        lang = doc.primary_language
        print(f"Language: {lang.name}")
        print(f"ISO code: {lang.iso6391_name}")
        print(f"Confidence: {lang.confidence_score:.2f}")
```

- `detect_language(documents)` — detects the language of the text.
- `doc.primary_language` — the detected language (a single object, not a list — Azure picks the dominant one).
- `lang.name` — full name: `"French"`, `"English"`, `"Arabic"`.
- `lang.iso6391_name` — two-letter code: `"fr"`, `"en"`, `"ar"`.
- `lang.confidence_score` — 0.0 to 1.0.

---

## Text Summarisation (Extractive)

Summarisation is a **long-running operation** — Azure processes the document in the background and you poll for the result. The SDK handles the polling for you automatically.

```python
from azure.ai.textanalytics import ExtractiveSummaryAction

documents = ["Azure AI Language is a cloud-based service that provides NLP capabilities. It includes sentiment analysis, key phrase extraction, named entity recognition, and more. Developers use it to build intelligent applications that understand human language."]

poller = client.begin_analyze_actions(
    documents,
    actions=[ExtractiveSummaryAction(max_sentence_count=3)]
)

result = poller.result()

for doc_results in result:
    for action_result in doc_results:
        if not action_result.is_error:
            for sentence in action_result.sentences:
                print(sentence.text)
```

- `begin_analyze_actions(documents, actions=[...])` — starts a long-running analysis job. `begin_` always means it returns a **poller**, not a result directly.
- `ExtractiveSummaryAction(max_sentence_count=3)` — picks the 3 most important sentences from the original text.
- `poller.result()` — waits for the job to finish and returns the results. This blocks your script until done.
- The result has two levels of looping: once for each document, once for each action (you can run multiple actions in one call).
- `action_result.sentences` — the selected sentences, in original document order.

---

## Text Summarisation (Abstractive)

```python
from azure.ai.textanalytics import AbstractiveSummaryAction

poller = client.begin_analyze_actions(
    documents,
    actions=[AbstractiveSummaryAction(sentence_count=3)]
)

result = poller.result()

for doc_results in result:
    for action_result in doc_results:
        if not action_result.is_error:
            for summary in action_result.summaries:
                print(summary.text)
```

- `AbstractiveSummaryAction(sentence_count=3)` — generates 3 new sentences summarising the document. These sentences are not copied from the original.
- `action_result.summaries` — for abstractive, each item is a summary object (not a sentence object). Use `.text` to get the string.
- Same polling pattern as extractive — `begin_analyze_actions` → `poller.result()` → loop.

---

## Long-running operations — what `begin_` means

Several Language methods start with `begin_`. This means the operation is **asynchronous** — Azure runs it in the background, and you have to wait for it.

```python
poller = client.begin_analyze_actions(...)   # starts the job, returns immediately
result = poller.result()                      # waits here until the job is done
```

- `poller` — an object that tracks the background job. Not the result itself.
- `poller.result()` — blocks your script and waits until Azure finishes. When it returns, you have the actual results.

This is different from methods like `analyze_sentiment()` which return results directly (synchronous — runs and finishes before moving on).

**Why the distinction?** Sentiment analysis on one sentence takes milliseconds. Summarising a 50-page document takes seconds or minutes. Azure runs long jobs in the background so your application does not freeze while waiting.

---

## Sending Multiple Documents at Once

The API accepts up to 25 documents in a single call (check current limits in Azure docs). Each document in the list gets its own result.

```python
documents = [
    "I love this product!",
    "This was a terrible experience.",
    "It was okay, nothing special.",
]

result = client.analyze_sentiment(documents)

for i, doc in enumerate(result):
    if not doc.is_error:
        print(f"Doc {i}: {doc.sentiment}")
```

- `enumerate(result)` — gives you both the index number (`i`) and the item (`doc`) at the same time.
- Results come back in the **same order** as your input. `result[0]` is always the result for `documents[0]`.

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Wrong key in `.env` | Check `FOUNDRY_KEY`. No quotes around the value. |
| `InvalidRequest` — document too long | Text exceeds the character limit | Split into smaller chunks before sending |
| `is_error = True` on a document | That one document failed | Check `doc.error.code` and `doc.error.message` |
| `AttributeError: module has no attribute` | Wrong import or wrong SDK version | Make sure you installed `azure-ai-textanalytics` not `azure-ai-language` |
| Empty `key_phrases` list | Text is too short or too generic | Short sentences often yield no key phrases — try a longer paragraph |
