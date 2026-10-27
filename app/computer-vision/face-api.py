import os
from dotenv import load_dotenv
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials

load_dotenv()

endpoint = os.environ["FACE_ENDPOINT"]
key = os.environ["FACE_KEY"]

client = FaceClient(endpoint, CognitiveServicesCredentials(key))

image_path = "/Users/rezanazari/Documents/Important Documents/Reza Docs/3x4 pictures/Foto.jpg"

with open(image_path, "rb") as f:
    detected_faces = client.face.detect_with_stream(f, return_face_id=False)

print(f"Faces found: {len(detected_faces)}")

for i, face in enumerate(detected_faces):
    box = face.face_rectangle
    print(f"Face {i + 1}: top={box.top}, left={box.left}, width={box.width}, height={box.height}")
