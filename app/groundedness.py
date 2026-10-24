import os
import json
from dotenv import load_dotenv
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.rest import HttpRequest
from azure.identity import DefaultAzureCredential

load_dotenv()

endpoint = os.environ["CONTENT_SAFETY_ENDPOINT"]

client = ContentSafetyClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential()
)

body = {
    "domain": "Generic",
    "task": "QnA",
    "qna": {
        "query": "What is the return policy?"
    },
    "text": "Returns are accepted around 30 days.",
    "groundingSources": [
        "Our return policy allows customers to return items within 30 days of purchase."
    ]
}

http_request = HttpRequest(
    method="POST",
    url=f"{endpoint}contentsafety/text:detectGroundedness",
    params={"api-version": "2024-02-15-preview"},
    headers={"Content-Type": "application/json"},
    content=json.dumps(body)
)

response = client.send_request(http_request)
response.raise_for_status()
result = response.json()

print(f"Ungrounded detected: {result['ungroundedDetected']}")
print(f"Ungrounded percentage: {result['ungroundedPercentage']}")
