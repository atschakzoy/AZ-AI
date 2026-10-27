import os
from dotenv import load_dotenv
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.identity import DefaultAzureCredential

load_dotenv()

endpoint = os.environ["FOUNDRY_ENDPOINT"]

client = ImageAnalysisClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential()
)

result = client.analyze_from_url(
    image_url="https://raw.githubusercontent.com/Azure-Samples/cognitive-services-sample-data-files/master/ComputerVision/Images/landmark.jpg",

    visual_features=[
        VisualFeatures.CAPTION,
        VisualFeatures.OBJECTS,
        VisualFeatures.TAGS,
    ]
)

if result.caption:
    print(f"Caption: {result.caption.text} (confidence: {result.caption.confidence:.2f})")

if result.objects:
    for obj in result.objects.list:
        print(f"Object: {obj.tags[0].name} at {obj.bounding_box}")

if result.tags:
    for tag in result.tags.list:
        print(f"Tag: {tag.name} ({tag.confidence:.2f})")
