# Computer Vision Solutions

A plain-English reference covering Azure AI Vision, Custom Vision, and the Face API. Written so anyone can read it and learn — not project-specific.

---

## What is Computer Vision

Computer vision is the field of AI where a model looks at an image or video and produces structured information from it — what objects are in the scene, what text appears, who is in the photo, what is happening.

You do not train these models yourself. Azure AI Vision provides pre-trained models that already understand the visual world. You send an image, you get structured data back.

There are three separate services in this stage:

| Service | What it does | Resource kind |
|---|---|---|
| **Azure AI Vision** | Analyse images — caption, objects, tags, OCR, people | `ComputerVision` |
| **Custom Vision** | Train your own image classifier on your own categories | `CustomVision.Training` + `CustomVision.Prediction` |
| **Face API** | Detect faces in images | `Face` |

---

## Part 1 — Azure AI Vision (Image Analysis)

Azure AI Vision is a pre-trained model that can look at any image and tell you:

- **Caption** — one plain-English sentence describing the whole image
- **Dense captions** — multiple captions for different regions of the image
- **Objects** — what physical objects are visible and where (bounding boxes)
- **Tags** — keywords describing what is in the image, each with a confidence score
- **Text (OCR)** — any printed or handwritten text visible in the image
- **People** — detects human figures and their location in the frame

You request only the features you need — you do not have to ask for all of them every time.

### SDK

```bash
pip install azure-ai-vision-imageanalysis azure-identity
```

The package is `azure-ai-vision-imageanalysis` — different from Content Safety (`azure-ai-contentsafety`) and Language (`azure-ai-textanalytics`). Each Azure AI service has its own SDK package.

### Resource

Azure AI Vision (Image Analysis) works with the existing **multi-service `CognitiveServices` account** — no new Terraform resource needed. Use `FOUNDRY_ENDPOINT` from your `.env` directly.

If you wanted to create a dedicated resource, the Terraform kind would be `ComputerVision`. But for this project the multi-service account covers it, the same way it covers Language service calls (PII, sentiment).

---

## Visual Features — What You Can Ask For

`VisualFeatures` is an enum (a fixed list of named options) that you import from `azure.ai.vision.imageanalysis.models`. You pass a list of the features you want when calling `analyze_from_url`.

| Feature | What it returns |
|---|---|
| `VisualFeatures.CAPTION` | One sentence describing the whole image |
| `VisualFeatures.DENSE_CAPTIONS` | Multiple captions for different regions |
| `VisualFeatures.OBJECTS` | List of detected objects with bounding boxes |
| `VisualFeatures.TAGS` | Keywords with confidence scores |
| `VisualFeatures.READ` | All text visible in the image (OCR) |
| `VisualFeatures.PEOPLE` | Detected human figures with bounding boxes |

---

## Image Analysis — What the Results Look Like

When `analyze_from_url` returns, the result object has one property per feature you requested. If you did not request a feature, that property is `None`.

**Caption** — one sentence Azure generated to describe the whole image:
```
Caption: a large stone structure with many arches with Colosseum in the background (confidence: 0.58)
```
Confidence is 0 to 1. A lower confidence (like 0.58) means the model is less certain about its description — not that the code is wrong.

**Objects** — a list of detected physical objects with bounding boxes showing where each one is in the image. Not every image returns objects — Azure only returns an object if it is confident it can draw a box around something specific.

**Tags** — keywords describing the image, sorted by confidence. Azure always returns tags from highest to lowest confidence:
```
Tag: outdoor (0.99)
Tag: building (0.99)
Tag: ancient rome (0.96)
Tag: ruins (0.95)
```
Tags describe general themes in the image — they do not tell you where something is.

**The difference between objects and tags:**
- **Tags** — what is in the image (keywords, no location)
- **Objects** — what is in the image AND where it is (with bounding box coordinates)

---

## Part 2 — OCR (Reading Text from Images)

**OCR** stands for Optical Character Recognition. It means reading text that appears visually in an image — printed signs, receipts, labels, documents, handwritten notes.

Azure AI Vision includes OCR through the `VisualFeatures.READ` feature. You use the same `ImageAnalysisClient` and the same `analyze_from_url` method — you just pass `VisualFeatures.READ` instead of `CAPTION` or `TAGS`.

**When to use OCR:**
- Reading text from a photo of a sign, receipt, or label
- Extracting text from a scanned document image
- Processing images where text is the important information

**For multi-page documents (PDFs):** Use **Document Intelligence** (Stage 05) instead. `VisualFeatures.READ` is for single images.

**Real-world OCR is never perfect.** If a character is at the edge of the image, partially obscured, or in poor lighting, Azure skips it or misreads it. Example from a nutrition label image:
- `"alories 190"` — the `C` was cut off at the image edge
- `"nt Daily Values"` — `"Perce"` was cut off

This is expected. In production you clean the output — strip incomplete lines, fix known misreads, or flag low-confidence words for human review.

**How the result is structured — three levels:**

```
result.read
  └── blocks  — groups of text (like paragraphs or regions)
        └── lines  — one line of text per item
              └── words  — individual words with their own bounding boxes
```

You loop through blocks → lines to get the text. You loop through words only if you need to know exactly where each word sits in the image.

---

## Part 3 — Custom Vision

Azure AI Vision uses a pre-trained model that knows general categories — it recognises dogs, cars, buildings, people. But it does not know your specific categories — your company's three product models, your factory's defect types, your medical images.

**Custom Vision lets you train your own image classifier** on your own images and your own categories. You provide the training images, Azure does the training.

### When to use Custom Vision instead of Azure AI Vision

| Use Azure AI Vision when | Use Custom Vision when |
|---|---|
| General categories are enough (car, person, building) | You need domain-specific categories Azure does not know |
| You do not have training images | You have labelled training images |
| You need OCR or captions | You need to classify images into your own classes |

### Key concepts

**Project** — a container for one trained model. You give it a name, a classification type (single label or multi-label), and a domain (General, Food, Retail, etc.). F0 allows 2 projects at the same time.

**Tag** — a label/class you define. If you are building a dog breed classifier, your tags might be `"labrador"`, `"poodle"`, `"beagle"`. Every image you upload gets assigned one or more tags.

**Iteration** — one completed training run. Every time you train the project (with the images you have uploaded so far), you get a new iteration. You can have multiple iterations and compare their performance.

**Publish** — before you can call your model for predictions, you must explicitly publish an iteration. Publishing gives it a name (e.g. `"Iteration1"`) and makes it available on the Prediction endpoint.

### The two resources — Training and Prediction

Custom Vision uses two completely separate Azure resources:

| Resource | Kind | Purpose |
|---|---|---|
| Training | `CustomVision.Training` | Upload images, create tags, trigger training, publish iterations |
| Prediction | `CustomVision.Prediction` | Send images to your trained model and get predictions back |

They have separate endpoints, separate keys, and separate SDKs. The Training resource is used only when you are building the model. The Prediction resource is used in your application.

### How training works — the full flow

```
1. Create a project (give it a name and classification type)
2. Create tags (the classes your model will learn)
3. Upload images with tags (minimum ~15 images per class recommended)
4. Train the project → Azure runs the training job → returns an Iteration
5. Publish the iteration (give it a name) → now it is callable
6. Use the Prediction resource to classify new images
```

### Real-world script structure

Training and prediction are always two separate Python scripts — not one combined file. The reason is their lifecycle:

```
train.py    → runs once (or occasionally when you retrain)
predict.py  → runs constantly in production for every new image
```

`train.py` is a developer/data-team tool. Once the model is trained and published, it is done. `predict.py` is what your application actually calls at runtime.

```
custom-vision/
├── train.py        ← one-off: build and publish the model
├── predict.py      ← runtime: classify new images in the app
└── images/         ← labelled images used for training
```

Mixing them into one file would mean your production app carries all the training logic — code it never needs to run again.

### Minimum images per class

Azure recommends at least **15 images per tag** for reasonable accuracy. More is better — 50+ per tag gives significantly better results. The images should be varied — different angles, lighting conditions, backgrounds.

### SDK

```bash
pip install azure-cognitiveservices-vision-customvision msrest
```

Note: this SDK (`azure-cognitiveservices-vision-customvision`) uses the older `msrest` authentication library, not `DefaultAzureCredential`. Custom Vision uses **API keys** for authentication, not Managed Identity. This is an older SDK that predates the modern Azure identity model.

### How Custom Vision differs from Azure AI Vision — full comparison

This table covers every dimension where Custom Vision behaves differently from the standard Azure AI Vision service:

| | Azure AI Vision | Custom Vision |
|---|---|---|
| **What it does** | Pre-trained model for general images | You train your own model on your own categories |
| **Azure resource kind** | `ComputerVision` (one resource) | `CustomVision.Training` + `CustomVision.Prediction` (two resources) |
| **Works with multi-service account?** | Yes — uses the `CognitiveServices` account | No — requires its own dedicated resources |
| **Authentication** | `DefaultAzureCredential` (Managed Identity / Azure CLI) | `ApiKeyCredentials` from `msrest` — API keys only, no Managed Identity support |
| **SDK package** | `azure-ai-vision-imageanalysis` | `azure-cognitiveservices-vision-customvision` + `msrest` |
| **Endpoints** | One endpoint | Two separate endpoints — Training and Prediction |
| **Keys** | One key (or no key if using Managed Identity) | Two keys — Training key and Prediction key |
| **`.env` variables needed** | `FOUNDRY_ENDPOINT` (already exists) | 5 new variables: training endpoint, training key, prediction endpoint, prediction key, prediction resource ID |
| **`custom_subdomain_name`** | Required in Terraform | Not supported — omit it |
| **Recommended SKU** | S0 (pay-as-you-go, near zero cost for testing) | F0 (free tier — training charges per compute hour on S0) |
| **Terraform outputs** | endpoint + primary_access_key | 5 outputs: training endpoint, training key, prediction endpoint, prediction key, prediction resource ID |

**Why is `prediction_resource_id` needed?**

When you publish a trained iteration, you link it to your Prediction resource. Azure needs the full resource ID (not just the endpoint) to make that link. The format is:
```
/subscriptions/<id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<name>
```
Terraform outputs this automatically via `.id` on the resource.

### Resource provisioning — Terraform

Two separate `azurerm_cognitive_account` resources, both on `F0`:

```hcl
resource "azurerm_cognitive_account" "custom_vision_training" {
  kind     = "CustomVision.Training"
  sku_name = "F0"
  ...
}

resource "azurerm_cognitive_account" "custom_vision_prediction" {
  kind     = "CustomVision.Prediction"
  sku_name = "F0"
  ...
}
```

**Custom Vision does not support `custom_subdomain_name`** — leave that field out of the Terraform resource. The endpoint Azure generates follows a different pattern than the other services.

**Why F0 here but S0 everywhere else?** Pre-trained model calls (content safety, image analysis, PII) cost fractions of a cent per call — S0 pay-as-you-go is near zero. Custom Vision charges per compute hour of training time. Even a small training job costs $0.20–$0.40 on S0. F0 covers learning workloads completely (2 projects, 1 hour training/month free).

---

## Part 4 — Face API

The Face API detects human faces in images. It tells you how many faces are in the image and exactly where each face appears — the bounding box coordinates.

### What it does

Face API analyses an image and returns a list of every face it found. For each detected face you get:

- **Bounding box** — where the face is in the image (top, left, width, height in pixels)
- **Face landmarks** — positions of specific facial features: eyes, eyebrows, nose, mouth corners, chin. These are point coordinates, not a description.
- **Face ID** — a temporary UUID identifying this face in this request. Not the same person across different requests.

### Limited Access attributes — what we skip

Microsoft restricts several Face API features to **Limited Access** — you must submit a business justification to Microsoft and receive approval before using them. They are turned off by default and will return an error if you try to use them without approval.

Restricted attributes include:
- **Age** — estimated age in years
- **Emotion** — happiness, sadness, anger, surprise, etc.
- **Gender** — male/female prediction
- **Smile** — whether the person is smiling
- **Facial hair, glasses, makeup, accessories**
- **Identification and verification** — matching a face against a known person

**Why Microsoft restricted these:** Age and gender prediction raises ethical and legal concerns (surveillance, bias, discrimination). Identification raises privacy concerns (mass surveillance). Microsoft restricts access to limit misuse.

**What we use:** Face detection and bounding boxes only — no attributes. This is the most common production use case: "count the faces in this image and tell me where they are."

### Dedicated resource required

Face API requires its own dedicated Azure resource — it does not work through the multi-service `CognitiveServices` account (`FOUNDRY_ENDPOINT`).

| Resource kind | `Face` |
|---|---|
| Terraform resource | `azurerm_cognitive_account` |
| SKU | `S0` (pay-as-you-go) |
| Supports `custom_subdomain_name`? | Yes |

This is the same Terraform resource type as all other Cognitive Services accounts — just a different `kind`.

### Authentication — `CognitiveServicesCredentials`

Face API uses the older `msrest` SDK (same era as Custom Vision). It does **not** support `DefaultAzureCredential` or `AzureKeyCredential`. However, the credential type is slightly different from Custom Vision:

| Service | Credential class | How it works |
|---|---|---|
| Custom Vision | `ApiKeyCredentials(in_headers={"Training-key": key})` | You manually specify the header name |
| Face API | `CognitiveServicesCredentials(key)` | msrest fills in the standard header automatically |

`CognitiveServicesCredentials` sends your key as the `Ocp-Apim-Subscription-Key` HTTP header — the standard header for Cognitive Services APIs. You just pass the key directly, no header name needed.

### Why you choose the model — Face API vs every other service

For every other service (Image Analysis, Language, Content Safety), Microsoft manages the underlying model for you. When they release a better version, they upgrade silently and you get improvements automatically. You never know or care which version is running.

**Face API makes you choose explicitly because of face recognition.** If you enrol a person's face using `recognition_01` and Microsoft silently upgrades to `recognition_04`, your stored face data breaks — the new model reads faces differently and can no longer match against your old enrolments.

The rule: **the recognition model you enrol with must match the one you query with.** You cannot mix them.

So Microsoft forces you to pin the version — you pick it, you own it. Since the call already requires `recognition_model`, they added `detection_model` to the same call for consistency, even though detection does not have the same matching constraint.

We are not doing identification or verification (those require Limited Access), so the model constraint does not affect us — but we still must pass both parameters because the SDK requires them. Always use the latest.

### Detection models

| Model | Use when |
|---|---|
| `detection_03` | Standard photos — always use this, most accurate |
| `detection_01` | Legacy — still works but less accurate |

### Recognition models

| Model | Notes |
|---|---|
| `recognition_04` | Latest — always use this |
| `recognition_01` / `02` / `03` | Legacy — only if you already have enrolled faces from these versions |

### Terraform provisioning

```hcl
resource "azurerm_cognitive_account" "face" {
  name                  = "face-${var.workload}-${var.environment}"
  location              = var.location
  resource_group_name   = var.resource_group_name
  kind                  = "Face"
  sku_name              = "S0"
  custom_subdomain_name = "face-${var.workload}-${var.environment}"

  identity {
    type = "SystemAssigned"
  }

  network_acls {
    default_action = "Allow"
  }
}
```

Unlike Custom Vision, Face supports both `custom_subdomain_name` and `network_acls` — so we include both, same pattern as the multi-service account.

The outputs you need:
- `endpoint` — the Face API endpoint URL
- `primary_access_key` (sensitive) — the key for authentication

---

## AI-102 Exam — Key Points

**Image Analysis:**
- `VisualFeatures` is an enum — a fixed list of named options, not methods. They are just labels that tell `analyze_from_url` what to run.
- You only pay for the features you request — Azure does not run caption detection if you only ask for `READ`.
- Tags describe what is in the image (no location). Objects describe what is in the image AND where (bounding box).
- `VisualFeatures.READ` is for OCR on single images. For multi-page PDFs, use Document Intelligence.
- The result structure for OCR has three levels: blocks → lines → words.
- Azure AI Vision works with the multi-service `CognitiveServices` account — no dedicated resource needed.

**Custom Vision:**
- Minimum recommended images per tag: 15. Hard minimum to start training: 5.
- After training, you must explicitly **publish** the iteration before predictions work.
- Training and Prediction are two separate Azure resources — two separate endpoints, two separate keys.
- Custom Vision uses the old `msrest` SDK — `DefaultAzureCredential` and `AzureKeyCredential` do NOT work. Use `ApiKeyCredentials`.
- `custom_subdomain_name` is NOT supported on Custom Vision Terraform resources.
- `network_acls` requires `custom_subdomain_name` — if you cannot set one, omit both.
- Use F0 for Custom Vision — training charges per compute hour on S0, even for small jobs.
- The `prediction_resource_id` is the full Azure resource ID, not the endpoint URL.

**Face API:**
- Face API requires a dedicated `Face` resource — it does NOT work with the multi-service `CognitiveServices` account.
- Face API uses `CognitiveServicesCredentials(key)` from `msrest` — NOT `DefaultAzureCredential` or `AzureKeyCredential`.
- `CognitiveServicesCredentials` is different from `ApiKeyCredentials` (Custom Vision) — you pass the key directly, not a header dict.
- The bounding box returned by Face API uses `top`/`left`/`width`/`height` — not `x`/`y` like Image Analysis.
- Age, emotion, gender, identification, and verification all require **Limited Access** approval from Microsoft.
- **`return_face_id` defaults to `True` — always set it to `False` explicitly.** Face IDs enable identification, so Microsoft restricts them even when you are not doing identification yourself. Failing to set this gives a 403 `UnsupportedFeature` error.
- Face detection with `return_face_id=False` (bounding boxes + count only) is freely available — no approval needed.
- Use `detection_model="detection_03"` — the latest and most accurate detection algorithm.
- Face API DOES support `custom_subdomain_name` (unlike Custom Vision) — include it in Terraform.
