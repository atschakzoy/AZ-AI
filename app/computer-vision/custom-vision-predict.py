import os
from dotenv import load_dotenv
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from azure.cognitiveservices.vision.customvision.prediction.models import ImageUrl
from msrest.authentication import ApiKeyCredentials

load_dotenv()

training_endpoint = os.environ["CUSTOM_VISION_TRAINING_ENDPOINT"]
training_key = os.environ["CUSTOM_VISION_TRAINING_KEY"]
prediction_endpoint = os.environ["CUSTOM_VISION_PREDICTION_ENDPOINT"]
prediction_key = os.environ["CUSTOM_VISION_PREDICTION_KEY"]

training_credentials = ApiKeyCredentials(in_headers={"Training-key": training_key})
trainer = CustomVisionTrainingClient(training_endpoint, training_credentials)
project = next(p for p in trainer.get_projects() if p.name == "fruit-classifier")

prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})
predictor = CustomVisionPredictionClient(prediction_endpoint.rstrip("/"), prediction_credentials)

test_url = "https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Apple%20Red%201/0_100.jpg"

results = predictor.classify_image_url(project.id, "Iteration1", url=test_url)


print("Predictions:")
for prediction in results.predictions:
    print(f"{prediction.tag_name}: {prediction.probability:.1%}")
