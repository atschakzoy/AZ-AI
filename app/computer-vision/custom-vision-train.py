import os
import time
from dotenv import load_dotenv
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import ImageUrlCreateEntry, ImageUrlCreateBatch
from msrest.authentication import ApiKeyCredentials

load_dotenv()

training_endpoint = os.environ["CUSTOM_VISION_TRAINING_ENDPOINT"]
training_key = os.environ["CUSTOM_VISION_TRAINING_KEY"]
prediction_resource_id = os.environ["CUSTOM_VISION_PREDICTION_RESOURCE_ID"]

training_credentials = ApiKeyCredentials(in_headers={"Training-key": training_key})
trainer = CustomVisionTrainingClient(training_endpoint, training_credentials)

# Delete any existing projects so the script can be run from scratch
for p in trainer.get_projects():
    for iteration in trainer.get_iterations(p.id):
        if iteration.publish_name:
            trainer.unpublish_iteration(p.id, iteration.id)
    trainer.delete_project(p.id)
    print(f"Deleted existing project: {p.name}")

print("Creating project...")
project = trainer.create_project("fruit-classifier")

apple_tag = trainer.create_tag(project.id, "apple")
banana_tag = trainer.create_tag(project.id, "banana")

print("Uploading images...")

apple_images = [
    ImageUrlCreateEntry(url="https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Apple%20Red%201/0_100.jpg", tag_ids=[apple_tag.id]),
    ImageUrlCreateEntry(url="https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Apple%20Red%201/1_100.jpg", tag_ids=[apple_tag.id]),
    ImageUrlCreateEntry(url="https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Apple%20Red%201/2_100.jpg", tag_ids=[apple_tag.id]),
    ImageUrlCreateEntry(url="https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Apple%20Red%201/6_100.jpg", tag_ids=[apple_tag.id]),
    ImageUrlCreateEntry(url="https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Apple%20Red%202/0_100.jpg", tag_ids=[apple_tag.id]),
    ImageUrlCreateEntry(url="https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Apple%20Red%202/1_100.jpg", tag_ids=[apple_tag.id]),
]

banana_images = [
    ImageUrlCreateEntry(url="https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Banana/0_100.jpg", tag_ids=[banana_tag.id]),
    ImageUrlCreateEntry(url="https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Banana/1_100.jpg", tag_ids=[banana_tag.id]),
    ImageUrlCreateEntry(url="https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Banana/2_100.jpg", tag_ids=[banana_tag.id]),
    ImageUrlCreateEntry(url="https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Banana/3_100.jpg", tag_ids=[banana_tag.id]),
    ImageUrlCreateEntry(url="https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Banana/4_100.jpg", tag_ids=[banana_tag.id]),
    ImageUrlCreateEntry(url="https://raw.githubusercontent.com/Horea94/Fruit-Images-Dataset/master/Training/Banana/5_100.jpg", tag_ids=[banana_tag.id]),
]

batch = ImageUrlCreateBatch(images=apple_images + banana_images)
upload_result = trainer.create_images_from_urls(project.id, batch)

stored = sum(1 for img in upload_result.images if img.status == "OK")
print(f"Images stored: {stored}/{len(upload_result.images)}")

print("Training...")
iteration = trainer.train_project(project.id)

while iteration.status != "Completed":
    time.sleep(5)
    iteration = trainer.get_iteration(project.id, iteration.id)
    print(f"Status: {iteration.status}")

print("Training complete.")

trainer.publish_iteration(
    project.id,
    iteration.id,
    "Iteration1",
    prediction_resource_id
)

print("Published.")
print(f"Project ID: {project.id}")
print("Add CUSTOM_VISION_PROJECT_ID to your .env file with the value above.")
