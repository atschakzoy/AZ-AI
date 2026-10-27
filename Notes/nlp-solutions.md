# NLP Solutions

A plain-English reference covering Azure AI Language service. Written so anyone can read it and learn — not project-specific.

---

## What is NLP

**NLP** stands for Natural Language Processing. It is the field of AI where a model reads text written by humans and produces structured information from it — what is the topic, is the writer happy or angry, what names or places are mentioned, what language is this written in.

Just like Computer Vision, you do not train these models yourself. Azure AI Language provides pre-trained models that already understand human language. You send text, you get structured data back.

---

## The Azure AI Language Service

In Stage 02 (Responsible AI / Content Safety) you used the Language service already — PII detection and sentiment analysis were both Language service calls. Now in Stage 04 you go deeper and use more of what Language can do.

**One resource, many capabilities.** Unlike Computer Vision (which had separate resources for Custom Vision, Face API, etc.), the Language service is one resource that handles all NLP tasks. The multi-service `CognitiveServices` account covers it — no new Terraform resource needed.

---

## The Capabilities — What Language Can Do

| Capability | What it does |
|---|---|
| **Sentiment Analysis** | Is this text positive, negative, or neutral? |
| **Key Phrase Extraction** | What are the main topics mentioned? |
| **Entity Recognition (NER)** | What names, places, organisations, dates are mentioned? |
| **Entity Linking** | Matches recognised entities to a Wikipedia article |
| **PII Detection** | Finds personally identifiable information (names, emails, phone numbers) |
| **Language Detection** | What language is this text written in? |
| **Text Summarisation** | Condense a long document into key points |
| **Question Answering** | Build a knowledge base and answer questions from it |
| **Conversational Language Understanding (CLU)** | Train a model to understand user intent in chat |
| **Custom NER** | Train your own entity recogniser on your own categories |

You already used Sentiment and PII in Stage 02. This stage adds Key Phrase Extraction, NER, Entity Linking, Language Detection, and Summarisation.

---

## Part 1 — Sentiment Analysis (review)

You already built this in Stage 02. Here is the full picture now that you have more context.

**Sentiment** answers: is the writer happy, unhappy, or neutral about the subject?

Azure returns sentiment at two levels:
- **Document level** — the overall tone of the whole text
- **Sentence level** — the tone of each individual sentence

This matters because a review might say "The food was excellent but the service was terrible" — overall mixed, but each sentence has a clear direction.

**Three sentiment labels:** `positive`, `negative`, `neutral`

**Confidence scores** — Azure returns a probability for each label:
```
positive: 0.92  negative: 0.03  neutral: 0.05
```
These three always add up to 1.0. The label returned is whichever has the highest score.

**Opinion Mining** — an optional extension that tells you not just the sentiment but *what* it is about. Instead of "this sentence is negative", it returns "the opinion target is 'service', the aspect is 'speed', and the sentiment is 'negative'." Useful for customer feedback analysis where you want to know which product feature is getting negative feedback.

---

## Part 2 — Key Phrase Extraction

**Key phrases** are the main topics, concepts, or subjects mentioned in the text. Azure reads the text and returns a list of the most important phrases.

**Example:**
```
Input:  "The weather in London has been terrible this week. Rain every day."
Output: ["weather", "London", "terrible", "Rain"]
```

**When to use it:**
- Summarising what a long document is about at a glance
- Tagging documents automatically (customer support tickets, articles)
- Building a search index by extracting meaningful terms

**Key phrases vs entities — the difference:**
- **Key phrases** — what topics are discussed (unstructured)
- **Entities (NER)** — specifically named things like a person, a place, an organisation (structured, with a category)

"London" might appear in both — as a key phrase (topic) and as an entity (type: Location).

---

## Part 3 — Named Entity Recognition (NER)

NER finds specific, categorised things mentioned in text. It does not just find keywords — it classifies them.

**Categories Azure recognises:**

| Category | Examples |
|---|---|
| `Person` | "Elon Musk", "the doctor", "my sister" |
| `Location` | "London", "the warehouse", "the Nile River" |
| `Organization` | "Microsoft", "the government", "Contoso Ltd" |
| `DateTime` | "next Tuesday", "January 2024", "3pm" |
| `Quantity` | "five dollars", "20 kilometres", "$1.2 million" |
| `URL` | "https://example.com" |
| `Email` | "user@example.com" |
| `PhoneNumber` | "+1-555-0100" |

**What you get back for each entity:**
- `text` — the exact text as it appeared: "Elon Musk"
- `category` — the type: "Person"
- `subcategory` — more specific if available: "PersonType" vs "Person"
- `confidence_score` — 0.0 to 1.0 — how confident Azure is in its classification
- `offset` — character position in the original text where the entity starts (useful for highlighting)
- `length` — how many characters long the entity is

**NER vs PII — the difference:**

Both find entities in text, but they serve different purposes:

| | NER | PII Detection |
|---|---|---|
| **Purpose** | Understand what is mentioned | Protect private information |
| **Output** | All named entities with categories | Only private data, with redaction option |
| **Use case** | Search indexing, content tagging, analytics | Compliance, data masking, privacy |

NER finds "Microsoft" and "London" alongside personal names. PII detection focuses specifically on data that could identify an individual and allows you to replace it with `[REDACTED]`.

---

## Part 4 — Entity Linking

Entity Linking goes one step further than NER. It does not just say "this is a Location" — it matches the entity to a specific Wikipedia article.

**Example:**
```
Input:  "I visited the Colosseum last summer."
Output:
  - Text: "Colosseum"
  - Category: Location
  - Wikipedia URL: https://en.wikipedia.org/wiki/Colosseum
  - Wikipedia data source: Wikipedia
  - Score: 0.97
```

**Why this is useful — disambiguation.** Many words have multiple meanings:
- "Apple" — the fruit, or the tech company?
- "Jordan" — the country, or the basketball player?
- "Jaguar" — the animal, or the car brand?

Entity Linking resolves the ambiguity by linking to the specific Wikipedia article that matches the context. It reads the surrounding text to figure out which meaning applies.

**When to use it:**
- Enriching a knowledge base with linked data
- Building structured representations of unstructured text
- Journalism tools — automatically link mentioned people and places to their profiles

---

## Part 5 — Language Detection

Azure reads text and tells you what language it is written in.

**What you get back:**
- `name` — the full language name: "English", "French", "Arabic"
- `iso6391_name` — the two-letter ISO code: "en", "fr", "ar"
- `confidence_score` — 0.0 to 1.0

**When to use it:**
- Before running other NLP — Language service performs best when it knows what language it is processing
- Routing multilingual content — send French text to a French-language processing pipeline
- Filtering — only process English content

**Handles mixed-language text.** If a document contains multiple languages, Azure returns the dominant one.

**Unknown language.** If it cannot detect the language, it returns `(Unknown)` with a score of `0.0`.

---

## Part 6 — Text Summarisation

Azure AI Language can summarise long documents into shorter forms. There are two types:

### Extractive Summarisation

Picks the most important **existing sentences** from the document and returns them in order. No new text is generated — every word in the summary was already in the original.

**Good for:** Legal documents, contracts, news articles where exact wording matters.

**You control how many sentences to return** — typically 3 to 5.

### Abstractive Summarisation

Generates **new sentences** that describe the content — like a human would write a summary. The words in the summary may not appear in the original.

**Good for:** Customer support tickets, long reports, emails — anywhere a natural-sounding condensed version is more readable than extracted sentences.

**Which to use:** Extractive is more reliable (no hallucination risk) but sounds choppy. Abstractive is more natural but can occasionally misrepresent details. For compliance or legal use, always use extractive.

---

## Part 7 — Question Answering

Azure AI Language can build a **knowledge base** — a set of question-and-answer pairs — and then answer questions against it.

**Two sources for the knowledge base:**
- **Manual pairs** — you write the questions and answers yourself
- **Documents / URLs** — you feed in a document or webpage, Azure extracts Q&A pairs automatically

**How it differs from ChatGPT / general LLMs:**
- It only knows what is in the knowledge base — it does not guess from general world knowledge
- Answers are grounded in specific source content — you can trace every answer back to a source
- This makes it predictable and auditable — good for enterprise use cases

**When to use it:**
- FAQ bots — customer support, HR policies, IT help desks
- Product documentation — "how do I reset my password"
- Anywhere you need constrained, source-backed answers

This is one of the most practical services for real-world applications and is heavily tested on the AI-102 exam.

---

## Part 8 — Conversational Language Understanding (CLU)

CLU lets you train a model to understand what a user is trying to do — their **intent** — and extract the key **entities** from what they said.

**Intent** — what the user wants to do:
```
"Book a flight to Paris" → intent: BookFlight
"What's the weather in Tokyo?" → intent: GetWeather
"Cancel my order" → intent: CancelOrder
```

**Entities** — the specific details from the request:
```
"Book a flight to Paris next Tuesday" 
  → intent: BookFlight
  → entity: destination = "Paris"
  → entity: date = "next Tuesday"
```

**CLU vs general chat models:**
- CLU is trained by you, on your domain, with your intents — it does not know about anything outside what you teach it
- This makes it fast, cheap, and predictable — you know exactly what it will and will not understand
- A general chat LLM (like ChatGPT) would handle arbitrary input but costs much more per call and can go off-topic

**When to use CLU:**
- Voice assistants for specific domains (book a restaurant, control smart home)
- Chatbots with a defined set of tasks
- Anywhere you need reliable intent detection without open-ended generation

CLU replaced the older **LUIS** (Language Understanding) service — if you see LUIS in older documentation or exam prep materials, CLU is its replacement.

---

## SDK — One Package for Everything

```bash
pip install azure-ai-textanalytics azure-identity
```

`azure-ai-textanalytics` is the Python SDK for all Language service capabilities — sentiment, key phrases, NER, entity linking, language detection, and summarisation. It is the same package you used in Stage 02.

One client, one endpoint, many methods.

---

## Resource — Same Multi-Service Account

All Language capabilities use the existing `CognitiveServices` account — the same one you used for content safety and PII in Stage 02. No new Terraform resource is needed.

Use `FOUNDRY_ENDPOINT` from your `.env` directly.

---

## AI-102 Exam — Key Points

- The Language service is **one resource** covering many capabilities — sentiment, NER, PII, key phrases, language detection, summarisation, question answering, CLU.
- The SDK package is `azure-ai-textanalytics` — not `azure-ai-language` (that is not the package name).
- All Language calls go through the multi-service `CognitiveServices` account — no dedicated resource needed.
- **NER vs PII:** NER finds and categorises all named things (people, places, organisations). PII focuses only on private data and supports redaction.
- **Entity Linking** resolves ambiguity by mapping entities to Wikipedia articles.
- **Extractive summarisation** returns existing sentences. **Abstractive summarisation** generates new text.
- **Question Answering** is grounded in a knowledge base — it does not guess from general knowledge.
- **CLU replaced LUIS** — any exam question about "Language Understanding" refers to CLU now.
- Opinion Mining is an extension of Sentiment Analysis that returns the target of the sentiment (e.g. "service speed was negative").
- Confidence scores are always 0.0 to 1.0. Sentiment scores (positive + negative + neutral) always sum to 1.0.
