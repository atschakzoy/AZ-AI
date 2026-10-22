# Stage 03 — Computer Vision Solutions

## What is this and why does it matter?

In AI-900 you learned what computer vision can do. In AI-102 you build it — calling the APIs from Python, handling responses, training custom models, and wiring everything into a real application.

This stage covers Azure AI Vision (image analysis, OCR), Custom Vision (training your own models), and the Face API.

---

## What you will learn

- Calling Azure AI Vision from Python (image analysis, OCR, object detection)
- Training and calling a Custom Vision classifier
- Calling the Face API for detection and analysis
- Working with the Image Analysis 4.0 SDK
- Handling errors and building production-ready vision code

---

## Part 1 — Azure AI Vision: Image Analysis

```bash
pip install azure-ai-vision-imageanalysis azure-identity
```

```python
import os
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.identity import DefaultAzureCredential

client = ImageAnalysisClient(
    endpoint=os.environ["VISION_ENDPOINT"],
    credential=DefaultAzureCredential()
)

result = client.analyze_from_url(
    image_url="https://example.com/image.jpg",
    visual_features=[
        VisualFeatures.CAPTION,
        VisualFeatures.OBJECTS,
        VisualFeatures.TAGS,
        VisualFeatures.READ,           # OCR
        VisualFeatures.PEOPLE,
        VisualFeatures.DENSE_CAPTIONS,
    ]
)

# Caption
if result.caption:
    print(f"Caption: {result.caption.text} (confidence: {result.caption.confidence:.2f})")

# Objects detected
if result.objects:
    for obj in result.objects.list:
        print(f"Object: {obj.tags[0].name} at {obj.bounding_box}")

# Tags
if result.tags:
    for tag in result.tags.list:
        print(f"Tag: {tag.name} ({tag.confidence:.2f})")

# OCR — Read text
if result.read:
    for block in result.read.blocks:
        for line in block.lines:
            print(f"Text: {line.text}")
```

**Analysing a local file instead of a URL:**
```python
with open("image.jpg", "rb") as f:
    image_data = f.read()

result = client.analyze(
    image_data=image_data,
    visual_features=[VisualFeatures.CAPTION, VisualFeatures.READ]
)
```

---

## Part 2 — OCR (Reading Text from Documents)

For reading text from documents (PDFs, scanned pages, forms), use the **Read API** — the same `VisualFeatures.READ` feature, but for multi-page documents use Document Intelligence (Stage 05).

```python
result = client.analyze_from_url(
    image_url="https://example.com/receipt.jpg",
    visual_features=[VisualFeatures.READ]
)

if result.read:
    full_text = ""
    for block in result.read.blocks:
        for line in block.lines:
            full_text += line.text + "\n"
            # Each word also has its bounding polygon
            for word in line.words:
                print(f"Word: '{word.text}' at {word.bounding_polygon}")
    print(full_text)
```

---

## Part 3 — Custom Vision

When Azure AI Vision's general categories don't fit your domain, train your own model.

**SDK:**
```bash
pip install azure-cognitiveservices-vision-customvision
```

**Training a classifier:**

```python
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import ImageUrlCreateEntry
from msrest.authentication import ApiKeyCredentials
import time

credentials = ApiKeyCredentials(in_headers={"Training-key": os.environ["CUSTOM_VISION_TRAINING_KEY"]})
trainer = CustomVisionTrainingClient(os.environ["CUSTOM_VISION_ENDPOINT"], credentials)

# Create project
project = trainer.create_project("product-classifier")

# Create tags (classes)
cat_tag = trainer.create_tag(project.id, "cat")
dog_tag = trainer.create_tag(project.id, "dog")

# Upload images with tags
cat_urls = [
    ImageUrlCreateEntry(url="https://example.com/cat1.jpg", tag_ids=[cat_tag.id]),
    ImageUrlCreateEntry(url="https://example.com/cat2.jpg", tag_ids=[cat_tag.id]),
]
dog_urls = [
    ImageUrlCreateEntry(url="https://example.com/dog1.jpg", tag_ids=[dog_tag.id]),
    ImageUrlCreateEntry(url="https://example.com/dog2.jpg", tag_ids=[dog_tag.id]),
]

trainer.create_images_from_urls(project.id, images=cat_urls + dog_urls)

# Train
iteration = trainer.train_project(project.id)
while iteration.status != "Completed":
    time.sleep(5)
    iteration = trainer.get_iteration(project.id, iteration.id)

# Publish
trainer.publish_iteration(project.id, iteration.id, "Iteration1", os.environ["PREDICTION_RESOURCE_ID"])
print("Training complete and published")
```

**Using the trained model:**

```python
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient

pred_credentials = ApiKeyCredentials(in_headers={"Prediction-key": os.environ["CUSTOM_VISION_PREDICTION_KEY"]})
predictor = CustomVisionPredictionClient(os.environ["CUSTOM_VISION_ENDPOINT"], pred_credentials)

results = predictor.classify_image_url(
    project.id,
    "Iteration1",
    url="https://example.com/test-image.jpg"
)

for prediction in results.predictions:
    if prediction.probability > 0.5:
        print(f"{prediction.tag_name}: {prediction.probability:.1%}")
```

---

## Part 4 — Face API

```bash
pip install azure-cognitiveservices-vision-face
```

```python
from azure.cognitiveservices.vision.face import FaceClient
from azure.cognitiveservices.vision.face.models import FaceAttributeType
from msrest.authentication import CognitiveServicesCredentials

client = FaceClient(
    os.environ["FACE_ENDPOINT"],
    CognitiveServicesCredentials(os.environ["FACE_KEY"])
)

# Detect faces and get attributes
detected_faces = client.face.detect_with_url(
    url="https://example.com/group-photo.jpg",
    return_face_attributes=[
        FaceAttributeType.age,
        FaceAttributeType.emotion,
        FaceAttributeType.glasses,
    ]
)

for face in detected_faces:
    rect = face.face_rectangle
    attrs = face.face_attributes
    print(f"Face at top={rect.top}, left={rect.left}")
    print(f"  Age estimate: {attrs.age}")
    print(f"  Glasses: {attrs.glasses}")
    dominant_emotion = max(
        vars(attrs.emotion).items(),
        key=lambda x: x[1] if isinstance(x[1], float) else 0
    )
    print(f"  Emotion: {dominant_emotion[0]}")
```

**Face verification (are these the same person?):**

```python
face1 = client.face.detect_with_url(url="https://example.com/person_a_1.jpg")[0]
face2 = client.face.detect_with_url(url="https://example.com/person_a_2.jpg")[0]

result = client.face.verify_face_to_face(
    face_id1=face1.face_id,
    face_id2=face2.face_id
)
print(f"Same person: {result.is_identical} ({result.confidence:.1%} confidence)")
```

---

## AI-102 Exam Checklist — Computer Vision

- [ ] What `VisualFeatures` options exist for `analyze_from_url`?
- [ ] How do you extract text (OCR) from an image using the Vision SDK?
- [ ] What is the minimum recommended images per class for Custom Vision?
- [ ] What is the difference between a training key and a prediction key in Custom Vision?
- [ ] After training a Custom Vision model, what must you do before you can call it? (publish the iteration)
- [ ] What Face API attributes can you request?
- [ ] What is face verification vs face identification?
- [ ] Why does face identification require a limited access application?

---

## Exercises

1. Call `analyze_from_url` with `CAPTION`, `OBJECTS`, and `TAGS` on a public image. Print the caption and all objects with confidence > 0.7.
2. Call the `READ` feature on an image containing printed text. Print each line of extracted text.
3. Train a Custom Vision classifier with at least 2 classes and 15+ images each. Publish the iteration and test predictions.
4. Detect faces in a group photo. Print the estimated age and dominant emotion for each face.
5. Download your Custom Vision model in Compact format and run it locally without calling the Azure endpoint.
