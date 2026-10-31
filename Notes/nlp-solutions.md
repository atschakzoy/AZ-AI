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

**Where it is mostly used:**

| Industry | Use case |
|---|---|
| E-commerce | Analyse product reviews at scale — flag products with rising negative sentiment |
| Hospitality | Monitor hotel and restaurant reviews across Tripadvisor, Google, Booking.com |
| Social media | Track brand sentiment on Twitter/X in real time during a product launch or crisis |
| Customer support | Prioritise tickets from angry customers before they escalate |
| Finance | Analyse earnings call transcripts or news articles for market sentiment |

---

## Part 2 — Key Phrase Extraction

**Key phrases** are the main topics, concepts, or subjects mentioned in the text. Azure reads the text and returns a list of the most important phrases.

**Example:**
```
Input:  "The weather in London has been terrible this week. Rain every day."
Output: ["weather", "London", "terrible", "Rain"]
```

**Where it is mostly used:**

| Industry | Use case |
|---|---|
| Media & publishing | Auto-tag articles with topics so readers can find related content |
| Customer support | Extract what each ticket is about without reading it manually — route to the right team |
| Search engines | Build a keyword index from documents without manually writing tags |
| Research | Quickly understand what a collection of academic papers is about |
| HR | Scan CVs and extract skills, technologies, and job titles automatically |

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

**Where it is mostly used:**

| Industry | Use case |
|---|---|
| Legal | Extract all person names, organisations, and dates from contracts automatically |
| Healthcare | Pull patient names, medications, diagnoses from clinical notes |
| Finance | Extract company names and dates from earnings reports to feed into a database |
| News / media | Identify all people and places mentioned in an article for automatic linking |
| Security | Scan logs and alerts for IP addresses, usernames, and timestamps |

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

**Where it is mostly used:**

| Industry | Use case |
|---|---|
| Journalism | Automatically hyperlink every person or place mentioned in an article to their Wikipedia profile |
| Knowledge graphs | Build structured databases from unstructured text — link "Apple" in a tech article to the company, not the fruit |
| Academic research | Disambiguate author names and institution names across thousands of papers |
| Search & discovery | Enrich search results with linked data — clicking "Jordan" shows whether it means the country or the athlete |

---

## Part 5 — Language Detection

Azure reads text and tells you what language it is written in.

**What you get back:**
- `name` — the full language name: "English", "French", "Arabic"
- `iso6391_name` — the two-letter ISO code: "en", "fr", "ar"
- `confidence_score` — 0.0 to 1.0

**Where it is mostly used:**

| Industry | Use case |
|---|---|
| Global platforms | Route incoming user messages to the correct language support team automatically |
| Content moderation | Only run moderation on languages the model supports — skip unknown scripts |
| E-commerce | Detect what language a product review was written in before displaying it |
| Analytics pipelines | Pre-filter a dataset so only English text goes to an English-only model |
| Chatbots | Detect user language on first message and switch the bot to reply in the same language |

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

**Where summarisation is mostly used:**

| Industry | Use case |
|---|---|
| Legal | Condense 50-page contracts into a 1-page brief for a manager |
| Healthcare | Summarise a patient's full medical history for a doctor seeing them for the first time |
| Finance | Summarise quarterly earnings reports so analysts can review more in less time |
| News aggregators | Show a 3-sentence preview of a long article |
| Customer support | Summarise a long email thread before it gets assigned to an agent |

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

---

## The Translator Service

A completely separate Azure resource from the Language service. It does not use the multi-service account — it needs its own dedicated resource with `kind = "TextTranslation"`.

**What it does:** Translates text from one language to another. Supports 100+ languages.

**Key difference from the Language service:**
- Language service uses a region-specific endpoint URL
- Translator uses a global endpoint (`api.cognitive.microsofttranslator.com`) but requires the region to be passed as a parameter on every API call
- The SDK is `azure-ai-translation-text` — a different package from `azure-ai-textanalytics`

**What the SDK can do:**

| Method | What it does |
|---|---|
| `client.translate()` | Translate text to one or more target languages. Language detection is automatic and included in the response. |
| `client.transliterate()` | Convert text between scripts — e.g. Arabic in Arabic script → Arabic in Latin letters |
| `client.get_supported_languages()` | List all languages and scripts the service supports |
| `client.find_sentence_boundaries()` | Find where sentences start and end (useful before splitting text for translation) |

**Language detection is free with every translate call** — the response includes `detected_language.language` and `detected_language.score` automatically. No separate API call needed.

**Where Translator is mostly used:**

| Industry | Use case |
|---|---|
| E-commerce | Translate product descriptions to sell in multiple countries |
| Customer support | Translate incoming tickets from any language so a single team can handle them |
| Healthcare | Translate patient instructions into the patient's native language |
| Travel & hospitality | Translate hotel listings, menus, and reviews for international guests |
| Legal / compliance | Translate regulatory documents for filing in other jurisdictions |
| Real-time chat | Translate messages between users who speak different languages |

---

## The Speech Service

A completely separate Azure resource. Needs its own dedicated resource with `kind = "SpeechServices"`.

**What it does:** Converts between audio and text in both directions — speech-to-text and text-to-speech.

**Key difference from all other Azure AI SDKs:**
- Other SDKs: one `Client` class, you call methods on it
- Speech SDK: no client — you create a `SpeechConfig` (settings), then attach it to a `SpeechRecognizer` or `SpeechSynthesizer`
- Like Language service, the region is baked into the endpoint — but unlike Translator, you do not pass the region separately. You pass it to `SpeechConfig` once, and the SDK handles the rest.

**The two main capabilities:**

| Capability | Class | What it does |
|---|---|---|
| Speech-to-Text (STT) | `SpeechRecognizer` | Listens to a microphone or audio file, returns text |
| Text-to-Speech (TTS) | `SpeechSynthesizer` | Takes text, generates spoken audio, plays it through speakers or saves to a file |

**Speech SDK package:** `azure-cognitiveservices-speech` — imported as `import azure.cognitiveservices.speech as speechsdk`

**Where Speech is mostly used:**

| Industry | Use case |
|---|---|
| Accessibility | Convert text content to audio so visually impaired users can listen |
| Call centres | Transcribe every customer call automatically for quality review and compliance |
| Voice assistants | Accept spoken commands and respond with synthesised speech |
| Healthcare | Doctors dictate notes by voice — STT transcribes to structured text in real time |
| Education | Read content aloud to students, or accept spoken answers from students |
| Automotive | In-car voice control — navigate, call, play music by speaking |
| Media | Auto-generate subtitles and captions for video content |

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
- **Translator** requires a dedicated resource (`kind = "TextTranslation"`) — it is NOT covered by the multi-service account.
- **Translator** uses a global endpoint but requires the region as a parameter on every API call — unlike Language service which bakes the region into the endpoint URL.
- **Language detection is free with every Translator call** — the response always includes the detected source language.
- **Speech** requires a dedicated resource (`kind = "SpeechServices"`) — it is NOT covered by the multi-service account.
- **Speech SDK design is different from all other Azure SDKs** — no client class, instead uses `SpeechConfig` + `SpeechRecognizer` / `SpeechSynthesizer`.
- **STT** = Speech-to-Text = `SpeechRecognizer`. **TTS** = Text-to-Speech = `SpeechSynthesizer`. Know which class does which.
