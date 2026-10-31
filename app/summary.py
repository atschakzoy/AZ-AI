import os
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient, ExtractiveSummaryAction, AbstractiveSummaryAction
from azure.core.credentials import AzureKeyCredential

load_dotenv()

endpoint = os.environ["FOUNDRY_ENDPOINT"]
key = os.environ["FOUNDRY_KEY"]

client = TextAnalyticsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

long_text = ["Azure AI Language is a cloud-based service that provides many NLP capabilities. It can analyse sentiment, extract key phrases, recognise named entities, detect languages, and summarise long documents. Developers use it to build intelligent applications that understand human language. The service is part of the broader Azure AI platform and works with the multi-service Foundry Tools account."]

poller = client.begin_analyze_actions(
    long_text,
    actions=[ExtractiveSummaryAction(max_sentence_count=2)]
)

result = poller.result()

for doc_results in result: 
    for action_result in doc_results:
        for sentence in action_result.sentences:
            print(sentence.text)

print("---------------------------")

#### Abstractive summary action: here it generates new sentences for summarisation instead of extracting

poller2 = client.begin_analyze_actions(
    long_text,
    actions=[AbstractiveSummaryAction(sentence_count=2)]
)

result2 = poller2.result()

for doc_results in result2:
    for action_result in doc_results:
        for summary in action_result.summaries:
            print(summary.text)