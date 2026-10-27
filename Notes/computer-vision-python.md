# Computer Vision — Python Patterns

Python concepts and patterns introduced in Stage 03. Builds on the patterns in `python-scripting.md`.

---

## Imports for Image Analysis

```python
import os
from dotenv import load_dotenv
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.identity import DefaultAzureCredential
```

- `ImageAnalysisClient` — the client class for Azure AI Vision. From the `azure-ai-vision-imageanalysis` package.
- `VisualFeatures` — an **enum** imported from `.models`. An enum is a fixed set of named options — instead of typing the string `"CAPTION"`, you write `VisualFeatures.CAPTION`. This prevents typos and makes the IDE help you.

---

## Enums — what they are

An **enum** is a class where each value is a named constant — a label, not a function. They do not do anything by themselves. Think of them as checkboxes on a form:

```
[ ] Caption     — describe the whole image in one sentence
[ ] Objects     — find objects and mark where they are
[ ] Tags        — list keywords that describe the image
[ ] Read        — read any text visible in the image (OCR)
[ ] People      — find people and mark where they are
[ ] Dense captions — describe different regions of the image
```

`VisualFeatures.CAPTION` is just the checkbox labelled "Caption". It is a value — like the number `5` or the string `"hello"`. Its only purpose is to tell `analyze_from_url()` which boxes you ticked.

`analyze_from_url()` reads your list of ticked boxes, sends the image to Azure, and Azure runs only the requested analyses. Results come back only for the features you listed.

**These are not Python built-ins.** Microsoft wrote them inside the `azure-ai-vision-imageanalysis` package. Under the hood, they are just strings with readable names:

```python
class VisualFeatures:
    CAPTION = "caption"
    OBJECTS = "objects"
    TAGS    = "tags"
    READ    = "read"
    PEOPLE  = "people"
```

Microsoft chose this pattern so that:
- Your IDE shows you the full list when you type `VisualFeatures.`
- If you mistype a name, Python raises an error immediately — instead of silently sending the wrong string to Azure
- You never have to remember the exact string Azure expects

The same pattern exists across all Azure SDKs — every package defines its own named options. They all live only inside their package; Python itself knows nothing about them.

---

## Passing a list of features

```python
result = client.analyze_from_url(
    image_url="https://...",
    visual_features=[
        VisualFeatures.CAPTION,
        VisualFeatures.OBJECTS,
        VisualFeatures.TAGS,
    ]
)
```

`visual_features` expects a **list** — square brackets containing multiple `VisualFeatures` values. You pick exactly what you need. The API only runs those features and returns only those results.

---

## Checking results with `if`

The result object has one property per feature. If you did not request a feature, that property is `None`. Always check before using:

```python
if result.caption:
    print(result.caption.text)
```

`if result.caption` — checks whether `caption` has a value. If you requested `CAPTION`, it will be a result object. If you did not request it, it will be `None`, and `if None` evaluates to `False` — so the print is skipped safely.

---

## Nested lists — objects and tags

Objects and tags come back as nested structures — not a flat list, but an object that contains a list:

```python
if result.objects:
    for obj in result.objects.list:
        print(obj.tags[0].name)
        print(obj.bounding_box)
```

- `result.objects` — the objects result object (not a list itself)
- `result.objects.list` — the actual list of detected objects
- `obj.tags[0].name` — each object has a list of tags; `[0]` takes the first (most relevant) one
- `obj.bounding_box` — a rectangle showing where in the image the object is

---

## Bounding boxes — what they are

A **bounding box** is a rectangle that marks where something appears in the image:

```
x      — how far from the left edge (in pixels)
y      — how far from the top edge (in pixels)
width  — how wide the box is
height — how tall the box is
```

Every time the Vision API detects an object, a face, or a person — it returns a bounding box so you know exactly where it is.

---

## analyze_from_url — the main method

```python
result = client.analyze_from_url(
    image_url="https://...",
    visual_features=[
        VisualFeatures.CAPTION,
        VisualFeatures.OBJECTS,
        VisualFeatures.TAGS,
    ]
)
```

- `image_url` — a publicly accessible URL. Azure's servers download the image directly — it never passes through your machine. Wikipedia blocks this (hotlink protection). Use Azure Samples GitHub URLs or other hotlink-friendly sources.
- `visual_features` — a list of `VisualFeatures` values. Azure only runs the features you list and only returns results for those features.

---

## Caption result

```python
if result.caption:
    print(f"Caption: {result.caption.text} (confidence: {result.caption.confidence:.2f})")
```

- `result.caption.text` — the generated sentence describing the image
- `result.caption.confidence` — 0.0 to 1.0. Lower confidence means less certainty, not wrong code.

---

## Tags result

```python
if result.tags:
    for tag in result.tags.list:
        print(f"Tag: {tag.name} ({tag.confidence:.2f})")
```

- `result.tags` — wrapper object (not a list)
- `result.tags.list` — the actual list of tag objects
- `tag.name` — keyword string, e.g. `"outdoor"`, `"building"`, `"ruins"`
- `tag.confidence` — 0.0 to 1.0

Tags come back sorted highest to lowest confidence.

---

## Objects result

```python
if result.objects:
    for obj in result.objects.list:
        print(f"Object: {obj.tags[0].name} at {obj.bounding_box}")
```

- `result.objects.list` — same wrapper pattern as tags
- `obj.tags[0].name` — each object has a list of name guesses; `[0]` takes the most confident one
- `obj.bounding_box` — rectangle showing where the object is in the image (x, y, width, height in pixels)

Not every image returns objects. Azure only returns an object if it can confidently place a bounding box around something specific.

---

## OCR result structure

OCR (reading text from images) uses `VisualFeatures.READ`. The result is structured in three levels:

```
result.read
  └── blocks — groups of text (like paragraphs or regions)
        └── lines — one line of text per item
              └── words — individual words with their own bounding boxes
```

```python
if result.read:
    for block in result.read.blocks:
        for line in block.lines:
            print(line.text)
```

You loop through blocks, then lines. `line.text` gives you the full line as a string — this is what you need most of the time.

If you need to know where each individual word is in the image:
```python
for word in line.words:
    print(f"{word.text} at {word.bounding_polygon}")
```

`word.bounding_polygon` — a polygon (set of corner points) around the word, useful for highlighting text in the original image.

---

## Custom Vision — SDK and Authentication

Custom Vision uses a different SDK and a different authentication method than all the other services we have used.

```python
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import ImageUrlCreateEntry
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials
```

**Why `ApiKeyCredentials` instead of `DefaultAzureCredential` or `AzureKeyCredential`?**

There are three credential types you will encounter in Azure SDKs:

| Credential | Library | Works with |
|---|---|---|
| `DefaultAzureCredential` | `azure-identity` (modern) | Modern SDKs — Content Safety, Language, Image Analysis |
| `AzureKeyCredential` | `azure-core` (modern) | Modern SDKs — same family as above, wraps an API key |
| `ApiKeyCredentials` | `msrest` (old) | Old SDKs — Custom Vision only |

**`DefaultAzureCredential`** — uses Managed Identity or Azure CLI login. No keys stored anywhere. All newer Azure SDKs use this.

**`AzureKeyCredential`** — also from the modern SDK family. Wraps an API key for modern services. You might think this would work for Custom Vision — it does not.

**`ApiKeyCredentials`** — from `msrest`, Microsoft's first Python authentication library (2015-2016). Custom Vision was built in this era and never rewritten. It only knows how to work with `msrest` — `DefaultAzureCredential` and `AzureKeyCredential` are a completely different socket shape; this SDK cannot accept them.

Think of it like a power plug — same electricity, different socket. `ApiKeyCredentials` is the only plug shape the Custom Vision SDK accepts. This is why Custom Vision keys must be in `.env` — there is no Managed Identity option with this SDK.

---

## Custom Vision — Training Client

```python
credentials = ApiKeyCredentials(in_headers={"Training-key": os.environ["CUSTOM_VISION_TRAINING_KEY"]})
trainer = CustomVisionTrainingClient(os.environ["CUSTOM_VISION_TRAINING_ENDPOINT"], credentials)
```

- `ApiKeyCredentials(in_headers={"Training-key": ...})` — wraps your key into a header format the API expects. `in_headers` means: send this key as an HTTP header named `"Training-key"` on every request
- `CustomVisionTrainingClient` — the client for the Training resource. Takes the endpoint first, then credentials

---

## Creating a project and tags

```python
project = trainer.create_project("my-classifier")

cat_tag = trainer.create_tag(project.id, "cat")
dog_tag = trainer.create_tag(project.id, "dog")
```

- `create_project("name")` — creates a new project in your Custom Vision account. Returns a project object with an `.id` property
- `create_tag(project.id, "label")` — creates a tag (class) inside the project. Returns a tag object with its own `.id`
- `project.id` and `cat_tag.id` — UUID strings that identify the project and tag. You pass them in later calls

---

## Uploading images with tags

In SDK version 3.1.1, `create_images_from_urls` requires images to be wrapped in an `ImageUrlCreateBatch` object — it will not accept a plain list or a `images=` keyword argument.

```python
from azure.cognitiveservices.vision.customvision.training.models import ImageUrlCreateEntry, ImageUrlCreateBatch

images = [
    ImageUrlCreateEntry(url="https://example.com/cat1.jpg", tag_ids=[cat_tag.id]),
    ImageUrlCreateEntry(url="https://example.com/cat2.jpg", tag_ids=[cat_tag.id]),
]

batch = ImageUrlCreateBatch(images=images)
upload_result = trainer.create_images_from_urls(project.id, batch)
```

- `ImageUrlCreateEntry` — pairs one image URL with a list of tag IDs
- `tag_ids=[cat_tag.id]` — a list even when there is only one tag. Square brackets required
- `ImageUrlCreateBatch(images=images)` — wraps the list into a batch object the SDK requires
- `upload_result` — capture the return value to check how many images were actually stored

**Checking what was stored:**

`create_images_from_urls` does not raise an error if some images fail to download — it silently skips them. Always check the result:

```python
stored = sum(1 for img in upload_result.images if img.status == "OK")
print(f"Images stored: {stored}/{len(upload_result.images)}")
```

If `stored` is less than 5 per tag, training will fail with "Not enough images per tag". Common cause: Wikipedia URLs are blocked by Azure's servers. Use GitHub raw content URLs instead — they are always accessible.

**GitHub raw URL format:**
```
https://raw.githubusercontent.com/<owner>/<repo>/master/<path>/<filename>
```

---

## Training and waiting for completion

```python
import time

iteration = trainer.train_project(project.id)

while iteration.status != "Completed":
    time.sleep(5)
    iteration = trainer.get_iteration(project.id, iteration.id)
```

- `train_project(project.id)` — starts the training job. Returns an Iteration object immediately, but training is still running in the background
- `iteration.status` — the current status: `"Training"`, `"Completed"`, `"Failed"`
- `while ... != "Completed"` — a loop that keeps running until training finishes
- `time.sleep(5)` — waits 5 seconds between checks. Without this, you would be hammering the API with requests every millisecond
- `trainer.get_iteration(project.id, iteration.id)` — fetches the latest status of this iteration from Azure. Replaces `iteration` with the updated version

**`while` loop** — runs as long as the condition is `True`. Each loop: check status → if not complete, wait 5 seconds → fetch updated status → check again. When status becomes `"Completed"`, the condition is `False` and the loop exits.

---

## Publishing an iteration

```python
trainer.publish_iteration(
    project.id,
    iteration.id,
    "Iteration1",
    os.environ["CUSTOM_VISION_PREDICTION_RESOURCE_ID"]
)
```

Training is done but the model is not yet callable. Publishing makes it available on the Prediction endpoint:
- `"Iteration1"` — the name you give this published iteration. You use this name when calling predictions
- `CUSTOM_VISION_PREDICTION_RESOURCE_ID` — the full Azure resource ID of your Prediction resource (not the endpoint, the resource ID). Format: `/subscriptions/.../resourceGroups/.../providers/Microsoft.CognitiveServices/accounts/name`

---

## Custom Vision — Prediction Client

```python
from msrest.authentication import ApiKeyCredentials
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient

pred_credentials = ApiKeyCredentials(in_headers={"Prediction-key": os.environ["CUSTOM_VISION_PREDICTION_KEY"]})
predictor = CustomVisionPredictionClient(os.environ["CUSTOM_VISION_PREDICTION_ENDPOINT"], pred_credentials)
```

Same pattern as the Training client — different key name (`"Prediction-key"`) and different client class.

---

## Making a prediction

```python
results = predictor.classify_image_url(project.id, "Iteration1", url=test_url)

for prediction in results.predictions:
    print(f"{prediction.tag_name}: {prediction.probability:.1%}")
```

- `classify_image_url` — sends one image URL to your trained model. Returns predictions for every tag in the project
- `"Iteration1"` — the published iteration name, must match exactly what you used in `publish_iteration`
- `url=test_url` — pass the image URL as a keyword argument. Do NOT wrap it in `ImageUrl(url=...)` — the SDK serialises that incorrectly and Azure returns "Invalid image url"
- `results.predictions` — a list of prediction objects, one per tag
- `prediction.tag_name` — the tag name, e.g. `"apple"`, `"banana"`
- `prediction.probability` — 0.0 to 1.0. `:.1%` formats it as a percentage: `0.9999` → `"100.0%"`

**Common errors and fixes:**

| Error | Cause | Fix |
|---|---|---|
| `PermissionDenied` (401) | Prediction key wrong in `.env` — quotes around the value | Remove quotes: `KEY=abc123` not `KEY="abc123"` |
| `Invalid image url` | SDK `ImageUrl` wrapper serialises incorrectly | Use `url=test_url` keyword argument instead |
| `Not enough images per tag` | Fewer than 5 images stored per tag | Check upload results — some URLs may be blocked |
| `Exceeds 2 projects` | F0 limit reached from previous failed runs | Add cleanup loop to delete existing projects before creating a new one |
| `Cannot delete project with published iteration` | Cleanup loop tries to delete before unpublishing | Unpublish all iterations before deleting the project |

**Why `.env` values must not have quotes:**
In Python's `python-dotenv`, a value like `KEY="abc"` reads as the string `"abc"` including the quote characters. Azure receives `"abc"` not `abc` — the key does not match and authentication fails.

**Training script vs prediction script — keep them separate:**
The training script runs once (or when you retrain). The prediction script runs in your application. Combining them means waiting through full training every time you get a prediction error — separating them saves significant time during development.

**Cleanup pattern — make training idempotent:**
An idempotent script produces the same result no matter how many times you run it. The cleanup loop at the start of the training script makes it idempotent — delete any existing project first, then create fresh. This prevents "Exceeds 2 projects" errors on re-runs:

```python
for p in trainer.get_projects():
    for iteration in trainer.get_iterations(p.id):
        if iteration.publish_name:
            trainer.unpublish_iteration(p.id, iteration.id)
    trainer.delete_project(p.id)
```

---

## Face API — Imports

```python
import os
from dotenv import load_dotenv
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
```

- `FaceClient` — the client class for the Face API. From the `azure-cognitiveservices-vision-face` package.
- `CognitiveServicesCredentials` — from `msrest`. This is different from `ApiKeyCredentials` used in Custom Vision. You pass the key directly and msrest handles the HTTP header automatically.

Install: `pip install azure-cognitiveservices-vision-face msrest`

---

## Face API — Client Setup

```python
load_dotenv()

endpoint = os.environ["FACE_ENDPOINT"]
key = os.environ["FACE_KEY"]

client = FaceClient(endpoint, CognitiveServicesCredentials(key))
```

- `CognitiveServicesCredentials(key)` — wraps your key. Unlike Custom Vision's `ApiKeyCredentials(in_headers={...})`, you just pass the key directly. msrest sends it as the `Ocp-Apim-Subscription-Key` header automatically.
- `FaceClient(endpoint, credentials)` — same pattern as Custom Vision clients: endpoint first, credentials second.

---

## Face API — Detecting Faces

```python
detected_faces = client.face.detect_with_url(
    url=image_url,
    detection_model="detection_03",
    recognition_model="recognition_04",
    return_face_id=True,
    return_face_landmarks=False,
    return_face_attributes=[]
)
```

- `client.face.detect_with_url` — the main method. Note it is `client.face.detect_with_url`, not `client.detect_with_url` — `face` is a sub-client.
- `url=image_url` — a publicly accessible image URL. Same rule as Image Analysis: Wikipedia blocks Azure servers, use GitHub raw URLs.
- `detection_model="detection_03"` — always use `detection_03`, the latest and most accurate. This chooses the algorithm Azure uses to locate faces.
- `recognition_model="recognition_04"` — required even when you are not doing face recognition. Use the latest version. This must match the model used at enrolment time — if you enrolled faces with `recognition_01` and switched to `recognition_04`, your database breaks. We are not enrolling anyone so it does not matter here, but the parameter is still required by the SDK.
- `return_face_id=False` — **always set this explicitly to `False`**. The default is `True`, but face IDs are restricted by Microsoft (June 2023) because they can be used for identification even if you are not doing identification yourself. Leaving the default causes a 403 `UnsupportedFeature: Identification,Verification` error.
- `return_face_landmarks=False` — set to `True` if you want the exact pixel coordinates of eyes, nose tip, mouth corners, etc.
- `return_face_attributes=[]` — the list of attributes to return. We pass an empty list because age, emotion, and gender all require Microsoft's Limited Access approval. Passing an empty list avoids errors.
- Returns a **list** of `DetectedFace` objects — one per face found. If no faces are found, the list is empty.

---

## Face API — Counting Faces and Bounding Boxes

```python
print(f"Faces found: {len(detected_faces)}")

for face in detected_faces:
    box = face.face_rectangle
    print(f"Face at top={box.top}, left={box.left}, width={box.width}, height={box.height}")
```

- `len(detected_faces)` — the total number of faces detected in the image. `len()` counts items in a list.
- `face.face_rectangle` — the bounding box showing where this face is in the image.
- `box.top` — pixels from the top of the image to the top edge of the face box.
- `box.left` — pixels from the left edge of the image to the left edge of the face box.
- `box.width` — width of the face box in pixels.
- `box.height` — height of the face box in pixels.

**Important difference from Image Analysis:** Image Analysis bounding boxes use `x` and `y`. Face API uses `top` and `left`. Same idea — different property names.

```
Image Analysis: bounding_box.x,  bounding_box.y,  bounding_box.width, bounding_box.height
Face API:       face_rectangle.left, face_rectangle.top, face_rectangle.width, face_rectangle.height
```

---

## Face API — Face Landmarks (optional)

If you set `return_face_landmarks=True`, each detected face has a `.face_landmarks` object with named point coordinates:

```python
detected_faces = client.face.detect_with_url(
    url=image_url,
    detection_model="detection_03",
    recognition_model="recognition_04",
    return_face_landmarks=True,
    return_face_attributes=[]
)

for face in detected_faces:
    lm = face.face_landmarks
    print(f"Nose tip: x={lm.nose_tip.x:.0f}, y={lm.nose_tip.y:.0f}")
    print(f"Left eye: x={lm.pupil_left.x:.0f}, y={lm.pupil_left.y:.0f}")
    print(f"Right eye: x={lm.pupil_right.x:.0f}, y={lm.pupil_right.y:.0f}")
```

- `lm.nose_tip`, `lm.pupil_left`, `lm.pupil_right` — specific named points on the face. Each has `.x` and `.y` pixel coordinates.
- `:.0f` — formats a float with 0 decimal places (rounds to whole number). Face coordinates are floats even though pixels are whole numbers.
- Landmarks use `x`/`y` coordinates (not `top`/`left`) — consistent with standard image coordinate systems.

---

## Face API — Common Errors

| Error | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Wrong key or endpoint | Check `FACE_ENDPOINT` and `FACE_KEY` in `.env`. No quotes around values. |
| `FaceAttributeType` error | Requesting a restricted attribute | Remove that attribute from `return_face_attributes`. Age, emotion, gender require Limited Access approval. |
| Empty list returned | No faces found | The image may have no visible faces, poor quality, or faces too small. Try a different image. |
| `InvalidURL` | URL blocked or unreachable | Do not use Wikipedia URLs — Azure servers cannot download them. Use GitHub raw URLs. |
