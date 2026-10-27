import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures

load_dotenv()

endpoint = os.environ["FOUNDRY_ENDPOINT"]

client = ImageAnalysisClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential()
)

result = client.analyze_from_url(
    image_url="https://raw.githubusercontent.com/Azure-Samples/cognitive-services-sample-data-files/master/ComputerVision/Images/printed_text.jpg",
    visual_features=[VisualFeatures.READ]
)

if result.read:
    for block in result.read.blocks:
        for line in block.lines:
            print(line.text)
