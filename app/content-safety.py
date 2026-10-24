import os
from dotenv import load_dotenv
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.identity import DefaultAzureCredential

load_dotenv()

endpoint = os.environ["CONTENT_SAFETY_ENDPOINT"]

client = ContentSafetyClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential()
)

request = AnalyzeTextOptions(text=" I want to shoot everyone in my building.")

response = client.analyze_text(request)

for category in response.categories_analysis:
    print(f"{category.category}: severity {category.severity}")

