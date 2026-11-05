import os
import math
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.environ["OPENAI_ENDPOINT"],
    api_key=os.environ["OPENAI_KEY"],
    api_version="2024-12-01-preview"
)

print("Client ready")

def get_embedding(text):
    result = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return result.data[0].embedding

embedding = get_embedding("Azure resource groups are containers for related resources")

print(f"Dimensions: {len(embedding)}")
print(f"First 5 values: {embedding[:5]}" )


def cosine_similarity(vec_a, vec_b):
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a ** 2 for a in vec_a))
    magnitude_b = math.sqrt(sum(b ** 2 for b in vec_b))
    return dot / (magnitude_a * magnitude_b)

azure_1 = get_embedding("Azure resource groups are containers for related resources")
azure_2 = get_embedding("A resource group is a logical container in Azure")
unrelated = get_embedding("The weather in Berlin is cold today")

print("\n--- Embeddings ---")
print(f"Similar pair:  {cosine_similarity(azure_1, azure_2):.4f}")
print(f"Unrelated:     {cosine_similarity(azure_1, unrelated):.4f}")

import json

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You extract information from text. Always respond with valid JSON only, no extra text."},
        {"role": "user", "content": "Extract the name, role, and company: Reza is a data engineer at Microsoft Azure."}
    ],
    response_format={"type": "json_object"}
)

data = json.loads(response.choices[0].message.content)
print("\n--- JSON Mode ---")
print(data)
print(f"Name: {data['name']}")

from pydantic import BaseModel

class PersonInfo(BaseModel):
    name: str
    role: str
    company: str

response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Extract information from the text."},
        {"role": "user", "content": "Reza is a data engineer at Microsoft Azure."}
    ],
    response_format=PersonInfo
)

person = response.choices[0].message.parsed
print("\n--- Pydantic Structured Output ---")
print(f"Name: {person.name}")
print(f"Role: {person.role}")
print(f"Company: {person.company}")

import base64

with open("test-pic.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What is in this image? Describe it in one sentence."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_data}"
                    }
                }
            ]
        }
    ]
)

print("\n--- Vision ---")
print(response.choices[0].message.content)


