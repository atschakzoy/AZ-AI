import os
import json
import math
import base64
from dotenv import load_dotenv
from openai import AzureOpenAI
from pydantic import BaseModel

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.environ["OPENAI_ENDPOINT"],
    api_key=os.environ["OPENAI_KEY"],
    api_version="2024-12-01-preview"
)

print("Client ready")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        { 
        
            "role": "system",
            "content": "Your are a helpful Azure expert. only answer Azure-related questions. keep answers under 50 words."
        },
        {
            "role": "user",
            "content": "What is a resource group and when would I use one?"
        }
    ],
    temperature=0.3,
    max_tokens=200
)

print("\n--- Single-turn-chat ---")
print(response.choices[0].message.content)
print(f"Tokens used: {response.usage.total_tokens}")


#--- Multi-turn chat --

messages = [
    {"role": "system", "content": "Your are a helpful Azure assistant."}
]

def chat(user_input):
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.3,
        max_tokens=150
    )

    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    return reply

print("\n--- Multi_turn chat ---")
print("Turn 1:", chat("What is Azure App Services?"))
print("Turn 2:", chat("How does it compare to Container APPs"))

#--- PART 3 Streaming ---
print("\n--- Streaming ---")

stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Explain Azure Kubernetes Service in two sentences."}],
    stream=True
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

print()


# --- PART 4: Function Calling ---
# --- PART 4: Function Calling ---

# A real lookup — maps service names to actual Azure docs URLs and descriptions
def get_azure_service_info(service_name):
    services = {
        "app service": {
            "description": "Fully managed PaaS for web apps and APIs",
            "best_for": "Traditional web apps, REST APIs",
            "docs": "https://learn.microsoft.com/azure/app-service"
        },
        "container apps": {
            "description": "Serverless containers with automatic scaling",
            "best_for": "Microservices, event-driven workloads",
            "docs": "https://learn.microsoft.com/azure/container-apps"
        },
        "kubernetes service": {
            "description": "Managed Kubernetes cluster",
            "best_for": "Complex container orchestration, full control needed",
            "docs": "https://learn.microsoft.com/azure/aks"
        }
    }
    result = services.get(service_name.lower(), {"error": "Service not found"})
    return json.dumps(result)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_azure_service_info",
            "description": "Get information about an Azure compute service",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "The Azure service name, e.g. 'app service', 'container apps', 'kubernetes service'"
                    }
                },
                "required": ["service_name"]
            }
        }
    }
]

messages = [{"role": "user", "content": "I need to run microservices that scale to zero when idle. Which Azure service fits best and where can I read more?"}]

fc_response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

if fc_response.choices[0].finish_reason == "tool_calls":
    tool_call = fc_response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    result = get_azure_service_info(**args)

    messages.append(fc_response.choices[0].message)
    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})

    final = client.chat.completions.create(model="gpt-4o", messages=messages)
    print("\n--- Function Calling ---")
    print(f"Model called: {tool_call.function.name}({args})")
    print(final.choices[0].message.content)

