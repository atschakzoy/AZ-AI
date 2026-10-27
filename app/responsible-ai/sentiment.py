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

documents = ["I love building azure ai but I hate using microsoft but it is okay to work in germany"]

result = client.analyze_sentiment(documents)

for doc in result:
    print(f"Sentiment: {doc.sentiment}")
    print(f"Positive score: {doc.confidence_scores.positive}")
    print(f"Negative score: {doc.confidence_scores.negative}")
    print(f"Neutral scores: {doc.confidence_scores.neutral}")