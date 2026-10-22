# Stage 04 — NLP Solutions: Language, Translation & Speech

## What is this and why does it matter?

This is the largest exam domain in AI-102 (~25%). You will write Python code that analyses text, extracts entities, translates languages, and converts speech — the same capabilities that power customer support systems, translation services, and voice assistants.

---

## What you will learn

- Calling Azure AI Language from Python (sentiment, NER, key phrases, summarisation)
- Training and using a Custom NER and CLU model
- Building a Question Answering knowledge base
- Calling Azure AI Translator
- Calling Azure AI Speech (speech to text, text to speech, translation)

---

## Part 1 — Azure AI Language: Text Analysis

```bash
pip install azure-ai-textanalytics azure-identity
```

```python
import os
from azure.ai.textanalytics import TextAnalyticsClient
from azure.identity import DefaultAzureCredential

client = TextAnalyticsClient(
    endpoint=os.environ["AI_LANGUAGE_ENDPOINT"],
    credential=DefaultAzureCredential()
)

documents = [
    "The Azure portal is really intuitive and the support team was excellent.",
    "I had a terrible experience, the service was down for 3 hours with no warning."
]

# Sentiment analysis
sentiment_results = client.analyze_sentiment(documents, show_opinion_mining=True)
for doc in sentiment_results:
    print(f"Sentiment: {doc.sentiment}")
    for sentence in doc.sentences:
        for opinion in sentence.mined_opinions:
            print(f"  Aspect: {opinion.target.text} → {opinion.target.sentiment}")

# Key phrases
kp_results = client.extract_key_phrases(documents)
for doc in kp_results:
    print(f"Key phrases: {doc.key_phrases}")

# Named entity recognition
ner_results = client.recognize_entities(documents)
for doc in ner_results:
    for entity in doc.entities:
        print(f"  Entity: {entity.text} | Category: {entity.category} | Confidence: {entity.confidence_score:.2f}")

# Language detection
lang_results = client.detect_language(["Bonjour le monde", "Hola mundo"])
for doc in lang_results:
    print(f"Language: {doc.primary_language.name} ({doc.primary_language.iso6391_name})")
```

---

## Part 2 — Text Summarisation

```python
from azure.ai.textanalytics import AbstractiveSummaryAction, ExtractiveSummaryAction

long_text = """Azure AI Services provides a comprehensive set of AI capabilities...
[long document here]"""

# Extractive summarisation — picks the most important sentences from the original
poller = client.begin_analyze_actions(
    [long_text],
    actions=[ExtractiveSummaryAction(max_sentence_count=3)]
)
for result in poller.result():
    for doc in result:
        for summary in doc.sentences:
            print(summary.text)

# Abstractive summarisation — generates new sentences that summarise the content
poller = client.begin_analyze_actions(
    [long_text],
    actions=[AbstractiveSummaryAction(sentence_count=2)]
)
for result in poller.result():
    for doc in result:
        for summary in doc.summaries:
            print(summary.text)
```

---

## Part 3 — Conversational Language Understanding (CLU)

CLU requires training your model in Azure AI Language Studio (the web UI) or via the REST API. Once trained and deployed, you call it like this:

```bash
pip install azure-ai-language-conversations
```

```python
from azure.ai.language.conversations import ConversationAnalysisClient
from azure.core.credentials import AzureKeyCredential

client = ConversationAnalysisClient(
    endpoint=os.environ["AI_LANGUAGE_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AI_LANGUAGE_KEY"])
)

result = client.analyze_conversation(
    task={
        "kind": "Conversation",
        "analysisInput": {
            "conversationItem": {
                "participantId": "user1",
                "id": "1",
                "modality": "text",
                "language": "en",
                "text": "Book me a flight to Paris next Friday"
            }
        },
        "parameters": {
            "projectName": "travel-assistant",
            "deploymentName": "production",
            "verbose": True
        }
    }
)

prediction = result["result"]["prediction"]
print(f"Top intent: {prediction['topIntent']}")
for entity in prediction["entities"]:
    print(f"  Entity: {entity['text']} → {entity['category']}")
```

---

## Part 4 — Question Answering

```python
from azure.ai.language.questionanswering import QuestionAnsweringClient
from azure.core.credentials import AzureKeyCredential

client = QuestionAnsweringClient(
    endpoint=os.environ["AI_LANGUAGE_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AI_LANGUAGE_KEY"])
)

result = client.get_answers(
    question="What is your return policy?",
    project_name="company-faq",
    deployment_name="production"
)

for answer in result.answers:
    print(f"Answer: {answer.answer}")
    print(f"Confidence: {answer.confidence:.2f}")
    print(f"Source: {answer.source}")
```

**Building the knowledge base (REST API):**
```python
import requests

headers = {
    "Ocp-Apim-Subscription-Key": os.environ["AI_LANGUAGE_KEY"],
    "Content-Type": "application/json"
}

# Import a FAQ URL as a source
payload = {
    "assets": {
        "sources": [
            {
                "displayName": "Company FAQ",
                "source": "https://example.com/faq",
                "sourceKind": "url"
            }
        ]
    }
}

requests.post(
    f"{os.environ['AI_LANGUAGE_ENDPOINT']}/language/query-knowledgebases/projects/company-faq/import",
    headers=headers,
    json=payload
)
```

---

## Part 5 — Azure AI Translator

```bash
pip install azure-ai-translation-text
```

```python
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential

client = TextTranslationClient(
    credential=AzureKeyCredential(os.environ["TRANSLATOR_KEY"]),
    region=os.environ["TRANSLATOR_REGION"]
)

# Translate text
response = client.translate(
    body=["Hello, how are you?", "What is a resource group?"],
    to_language=["fr", "es"],
    from_language="en"
)

for translation in response:
    for result in translation.translations:
        print(f"{result.to}: {result.text}")

# Detect language
detect_result = client.detect_language(body=["Bonjour le monde"])
print(f"Detected: {detect_result[0].language} ({detect_result[0].score:.2f})")
```

---

## Part 6 — Azure AI Speech

```bash
pip install azure-cognitiveservices-speech
```

**Speech to text (from a file):**
```python
import azure.cognitiveservices.speech as speechsdk

speech_config = speechsdk.SpeechConfig(
    subscription=os.environ["SPEECH_KEY"],
    region=os.environ["SPEECH_REGION"]
)
speech_config.speech_recognition_language = "en-US"

audio_config = speechsdk.audio.AudioConfig(filename="audio.wav")
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

result = recognizer.recognize_once()
if result.reason == speechsdk.ResultReason.RecognizedSpeech:
    print(f"Transcribed: {result.text}")
elif result.reason == speechsdk.ResultReason.NoMatch:
    print("No speech detected")
```

**Text to speech:**
```python
speech_config = speechsdk.SpeechConfig(
    subscription=os.environ["SPEECH_KEY"],
    region=os.environ["SPEECH_REGION"]
)
speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"

audio_config = speechsdk.audio.AudioOutputConfig(filename="output.wav")
synthesiser = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

result = synthesiser.speak_text_async("Hello, I am your Azure AI assistant.").get()
print("Audio saved to output.wav")
```

**SSML for fine-grained speech control:**
```python
ssml = """
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    <voice name="en-US-JennyNeural">
        <prosody rate="slow" pitch="+5%">
            Welcome to Azure AI Services.
        </prosody>
    </voice>
</speak>
"""
synthesiser.speak_ssml_async(ssml).get()
```

---

## AI-102 Exam Checklist — NLP Solutions

- [ ] What parameters does `analyze_sentiment` accept and what does it return?
- [ ] What is opinion mining and how do you enable it?
- [ ] What is the difference between extractive and abstractive summarisation?
- [ ] What three things does CLU return in its prediction? (intent, entities, confidence)
- [ ] How do you call a deployed CLU project from Python?
- [ ] What is the difference between Question Answering and CLU?
- [ ] How do you add a URL as a source to a Question Answering knowledge base?
- [ ] What does the Translator service return when you request translation to multiple languages?
- [ ] What is the difference between `recognize_once` and continuous recognition?
- [ ] What is SSML and what can you control with it?

---

## Exercises

1. Analyse 5 product reviews with sentiment analysis and opinion mining. Print the aspect and its sentiment for each opinion.
2. Extract named entities from a paragraph of news text. Group them by category.
3. Build a CLU project in Language Studio with 3 intents and 10+ example utterances each. Deploy and call it from Python.
4. Create a Question Answering knowledge base from a real FAQ URL. Query it with 5 different questions and print the confidence scores.
5. Transcribe a 30-second audio file with Speech to Text. Save the transcript to a text file.
6. Generate speech from the transcript using a Neural voice. Compare the audio to the original.
