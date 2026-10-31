import os
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

endpoint = os.environ["FOUNDRY_ENDPOINT"]
key = os.environ["FOUNDRY_KEY"]

client = TextAnalyticsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

documents = ["the food was amazing. but the service was really slow.."]

result = client.analyze_sentiment(documents)

for doc in result:
    print(doc.sentiment)
    print(doc.confidence_scores)

for sentence in doc.sentences:
    print(sentence.text)
    print(sentence.sentiment)

    print ("-----------------------")

######### here starts the Key phrase extraction


documents2 = ["Azure AI Language can extract key phrases from text. it finds the main topic and concepts mentioned"]

result2 = client.extract_key_phrases(documents2)

for doc in result2:
    print(doc.key_phrases)

print ("-----------------------")

##### here starts the Named Entity Recognition

documents3 = ["Cristiano Ronaldo was born in Madeira, Portugal in 1985. when his father was 42."]

result3 = client.recognize_entities(documents3)

for doc in result3:
    for entity in doc.entities:
        print(entity.text, entity.category, entity.confidence_score)


print ("-----------------------")

##### here starts the Entity Linging

documents4 = ["I visited the Colosseum in Rome last summer. The Colosseum is a famous ancient Roman amphitheatre. It was built in ancient Rome."]


result4 = client.recognize_linked_entities(documents4)

for doc in result4:
    for entity in doc.entities:
        print(entity.name, entity.url)


print ("-----------------------")

##### here starts the language detection

documents5 = [
    "Bonjour, comment allez-vous?",
    "بیا بریم کجا",
    "bin seni istamıram",
    "du bist fett genug"
]

result5 = client.detect_language(documents5)

for doc in result5:
    print(doc.primary_language.name)
    print(doc.primary_language.iso6391_name)
    print(doc.primary_language.confidence_score)
