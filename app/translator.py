import os
from dotenv import load_dotenv
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

endpoint = os.environ["TRANSLATOR_ENDPOINT"]
key = os.environ["TRANSLATOR_KEY"]
region = os.environ["TRANSLATOR_REGION"]

client = TextTranslationClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key),
    region=region
)

response = client.translate(
    body=["Hello, how are you?"],
    to_language=["fa", "de"]
)

for translation in response:
    print("Detected:", translation.detected_language.language, translation.detected_language.score)
    for result in translation.translations:
        print(result.language, result.text)
