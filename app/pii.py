import os
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.identity import DefaultAzureCredential

load_dotenv()

endpoint = os.environ["FOUNDRY_ENDPOINT"]

client = TextAnalyticsClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential()
)

documents = ["My name is Reza Nazari, my email is reza.nazari@gmial.com and my phone number is ß178723283823"]

response = client.recognize_pii_entities(documents)

for doc in response:
    print(f"Redacted text: {doc.redacted_text}")
    print()
    for entity in doc.entities:
        print(f"{entity.category}: {entity.text} (confidence: {entity.confidence_score:.2f})")