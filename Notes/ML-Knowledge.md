# ML Knowledge — Models, Algorithms & How They Work

A plain-English reference for understanding the machine learning that powers Azure AI services. No math assumed — just concepts, context, and pointers to go deeper.

---

## What is Machine Learning?

Traditional programming: you write the rules.
```
if review contains "terrible" → sentiment = negative
```
This breaks immediately. "Not terrible" is positive. "Terribly good" is positive. You cannot write enough rules.

Machine learning: you show the algorithm examples and let it find the rules itself.
```
algorithm sees 1 million reviews labeled positive/negative
→ it discovers the patterns
→ you get a model that can predict on new text it has never seen
```

The algorithm does not understand language. It finds statistical patterns in numbers. Everything — text, images, audio — gets converted to numbers first.

---

## The Core Idea — Parameters

Every ML model is, at its heart, a huge collection of numbers called **parameters** (also called weights).

- A small model might have 1 million parameters
- GPT-4o has an estimated 1.8 trillion parameters
- Training = adjusting those parameters until the model makes good predictions
- Once trained, the parameters are frozen — that frozen state is the model you call

When you call `analyze_sentiment()`, your text flows through those frozen parameters and produces a prediction. No new learning happens — it just computes.

---

## The Main Algorithm Families

### 1. Transformers — the dominant architecture today

**What it is:**
A neural network architecture designed specifically to understand relationships between words (or image patches, or audio segments) across long distances.

The key innovation is called **Attention** — the model learns to pay attention to the right words when processing each word. When reading "The bank by the river was steep", it learns that "bank" relates to "river", not "money".

**Where it is used:**
- All modern language AI: GPT-4o, BERT, Language service
- Document Intelligence (LayoutLM — Transformer + document layout)
- Modern vision AI (Vision Transformer, or ViT)
- Modern speech AI (Whisper)

**Two main variants:**

| Variant | How it works | Used for |
|---|---|---|
| Encoder-only (BERT) | Reads the whole text at once, builds understanding | Classification, sentiment, entity recognition |
| Decoder-only (GPT) | Generates text one word at a time, left to right | Chat, text generation, summarisation |
| Encoder-decoder (T5) | Reads input, generates output | Translation, summarisation |

**Why it matters for you:**
Every Foundry Tool you call, and all of Azure OpenAI, runs on a Transformer variant. Understanding Transformers at a conceptual level means you understand the foundation of modern AI.

**Python — using a Transformer yourself (via Hugging Face):**
```python
# pip install transformers
from transformers import pipeline

# This downloads a small BERT model and runs sentiment analysis locally
classifier = pipeline("sentiment-analysis")
result = classifier("I love building AI apps on Azure")
print(result)
# [{'label': 'POSITIVE', 'score': 0.9998}]
```
This is what the Language service does behind the scenes — you just call their hosted, larger, better-tuned version via the SDK.

---

### 2. CNN — Convolutional Neural Network

**What it is:**
A neural network designed to process grids of data — primarily images (a grid of pixels).

The key idea: instead of connecting every pixel to every neuron (too many connections, too slow), CNNs slide small filters across the image. Each filter learns to detect a pattern — an edge, a curve, a colour gradient. Deep layers combine those into higher-level patterns — eyes, wheels, text.

**Where it is used:**
- Computer Vision service (image description, OCR, object detection)
- Face service
- Custom Vision (you train your own CNN on your images)
- Still widely used — though Vision Transformers are taking over for the biggest models

**How it processes an image:**
```
Input image (pixels)
→ Layer 1: detects edges and gradients
→ Layer 2: detects shapes and curves
→ Layer 3: detects parts (eyes, wheels, letters)
→ Layer 4: detects objects (face, car, word)
→ Output: class label or bounding box
```

**Python — using a CNN yourself (via PyTorch):**
```python
# pip install torch torchvision
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

# Load a pre-trained ResNet (famous CNN architecture)
model = models.resnet50(pretrained=True)
model.eval()

# Prepare an image
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
])
image = Image.open("dog.jpg")
tensor = transform(image).unsqueeze(0)

# Run prediction
output = model(tensor)
# output is a vector of 1000 scores, one per ImageNet class
```

---

### 3. RNN / LSTM — Recurrent Neural Network

**What it is:**
A neural network designed for sequences — data where order matters and each step depends on what came before.

A standard neural network processes one input and produces one output with no memory. An RNN passes a hidden state from one step to the next — it "remembers" what it has seen.

**LSTM (Long Short-Term Memory)** is an improved RNN that handles long sequences better — it has gates that decide what to keep in memory and what to forget.

**Where it is used:**
- Anomaly Detector — time-series data (metrics over time are a sequence)
- Older speech models (before Transformers took over)
- Any task where you need to model dependencies over time

**When time-series matters:**
```
CPU usage: [10, 12, 11, 13, 10, 10, 95, 10, 11]
                                      ↑
                              LSTM flags this as anomalous
                              because it learned the normal pattern
```

**Python — a simple LSTM with PyTorch:**
```python
import torch
import torch.nn as nn

# One LSTM layer: input size 1, hidden size 32, one layer
lstm = nn.LSTM(input_size=1, hidden_size=32, num_layers=1, batch_first=True)

# Fake time-series: 1 sample, 10 time steps, 1 feature each
x = torch.randn(1, 10, 1)

output, (hidden, cell) = lstm(x)
# output: predictions at each time step
# hidden: the final memory state
```

---

### 4. Classical ML — Before Deep Learning

Not all ML is neural networks. These are older, simpler algorithms that still work well for structured data (tables, numbers) and small datasets.

**Random Forest:**
- Builds many decision trees and takes a vote across all of them
- Great for tabular data (think spreadsheets)
- Interpretable — you can see which features mattered

**Gradient Boosting (XGBoost, LightGBM):**
- Builds trees sequentially, each one fixing the errors of the last
- Often wins competitions on structured data
- Very fast, very accurate for the right problem

**When to use classical ML vs deep learning:**

| Situation | Use |
|---|---|
| Tabular data (spreadsheets, databases) | Classical ML (XGBoost, Random Forest) |
| Images | CNN or Vision Transformer |
| Text | Transformer |
| Audio | Transformer (Whisper) |
| Time-series / anomaly | LSTM or classical statistical models |
| Small dataset (< 10K samples) | Classical ML — deep learning needs more data |
| Large dataset | Deep learning wins |

---

## Embeddings — How Text Becomes Numbers

This is critical for RAG, so it deserves its own section.

A model cannot process words directly. Every word, sentence, or document must become a vector — a list of numbers.

**Word embedding example:**
```
"king"   → [0.2, 0.8, -0.3, 0.9, ...]   (a list of 1536 numbers)
"queen"  → [0.2, 0.7, -0.2, 0.8, ...]   (similar — close in meaning)
"banana" → [-0.5, 0.1, 0.7, -0.4, ...]  (different — far in meaning)
```

The numbers are meaningless individually. What matters is the **distance** between them. Words with similar meanings cluster close together in this 1536-dimensional space.

**Why this matters for RAG:**
1. You embed every chunk of your document → store vectors in AI Search
2. User asks a question → you embed the question → get its vector
3. AI Search finds the document chunks whose vectors are closest to the question vector
4. You pass those chunks to GPT-4o to generate the answer

In Azure: `text-embedding-ada-002` (Azure OpenAI) creates these vectors.

**Python — creating an embedding:**
```python
from openai import AzureOpenAI

client = AzureOpenAI(
    endpoint=os.environ["OPENAI_ENDPOINT"],
    api_key=os.environ["OPENAI_KEY"],
    api_version="2024-02-01"
)

response = client.embeddings.create(
    input="I love building AI apps on Azure",
    model="text-embedding-ada-002"  # your deployment name
)

vector = response.data[0].embedding
print(len(vector))  # 1536 numbers
```

---

## How Training Works — The Big Picture

You do not train these models yourself when using Azure AI. But understanding training helps you understand why the models behave as they do.

```
1. Collect data
   └── millions of labeled examples (text + label, image + label)

2. Initialise parameters
   └── random numbers to start

3. Forward pass
   └── run an example through the model
   └── get a prediction

4. Calculate loss
   └── how wrong was the prediction?
   └── loss function measures the error (e.g. cross-entropy)

5. Backward pass (backpropagation)
   └── calculate how each parameter contributed to the error
   └── adjust each parameter slightly in the right direction

6. Repeat millions of times
   └── parameters gradually settle into values that minimise error

7. Done — the trained model is frozen and deployed
```

The algorithm that does steps 4-6 is called **gradient descent**. It is the engine behind all deep learning.

---

## How Azure AI Services Fit In

| Service | Algorithm family | You see |
|---|---|---|
| Language — sentiment | Transformer (BERT variant) | positive / negative / neutral + score |
| Language — entities | Transformer | entity name + category |
| Vision — image analysis | CNN or Vision Transformer | description + confidence |
| Speech — transcription | Transformer (Whisper-like) | text |
| Document Intelligence | Transformer (LayoutLM) | structured JSON from the document |
| Content Safety | Transformer classifier | category + severity score |
| Anomaly Detector | LSTM + statistical | anomaly flag + severity |
| Azure OpenAI — GPT-4o | Large Language Model (Transformer) | generated text |
| Azure OpenAI — embeddings | Transformer encoder | vector (list of numbers) |

---

## Python Libraries for ML

If you want to go deeper and experiment with these models yourself:

| Library | What it is | Install |
|---|---|---|
| `scikit-learn` | Classical ML (Random Forest, etc.) | `pip install scikit-learn` |
| `pytorch` | Deep learning framework — most research uses this | `pip install torch` |
| `tensorflow` | Deep learning framework — Google's version | `pip install tensorflow` |
| `transformers` | Hugging Face — thousands of pre-trained models, easy to use | `pip install transformers` |
| `sentence-transformers` | Embeddings made easy | `pip install sentence-transformers` |
| `numpy` | Numbers and arrays — everything ML needs this | `pip install numpy` |
| `pandas` | Data in tables | `pip install pandas` |

**Hugging Face** is the best starting point for experimenting. They host thousands of open-source models you can run locally for free — the same architectures that power Azure AI services, just smaller versions.

---

## Learning Path — Go Deeper

### Start here (visual, no math)
1. **3Blue1Brown — Neural Networks series** (YouTube)
   Search: "3blue1brown neural networks"
   Covers: what neurons are, how training works, backpropagation — visually beautiful
   Time: ~4 hours total

2. **3Blue1Brown — Attention in Transformers** (YouTube)
   Search: "3blue1brown attention"
   Covers: how the Transformer attention mechanism works visually
   Time: ~30 min

### Go practical
3. **fast.ai — Practical Deep Learning for Coders**
   URL: fast.ai
   Covers: CNN, image classification, NLP — code first, theory second
   Approach: build things first, understand why later

4. **Hugging Face Course** (free)
   URL: huggingface.co/learn
   Covers: Transformers, BERT, GPT, fine-tuning, embeddings
   Directly relevant to what Azure AI uses

### Go deep
5. **Andrej Karpathy — Let's build GPT from scratch** (YouTube)
   Search: "Karpathy build GPT"
   Covers: builds a GPT model from scratch in Python, line by line
   Time: ~2 hours — the best single video for understanding LLMs

6. **The original Transformer paper — "Attention Is All You Need"** (2017, Google)
   Search: "attention is all you need arxiv"
   The paper that started everything — readable if you watch the 3Blue1Brown video first

### For classical ML
7. **Kaggle Learn — Intro to Machine Learning**
   URL: kaggle.com/learn
   Free, interactive, uses scikit-learn, real datasets
