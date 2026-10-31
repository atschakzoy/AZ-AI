import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

key = os.environ["SPEECH_KEY"]
region = os.environ ["SPEECH_REGION"]

speech_config = speechsdk.SpeechConfig(subscription=key, region=region)

synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

result = synthesizer.speak_text_async("AAAAhhhoy, chiki bum bum dady dady. Nice to meet you.").get()

if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("Speech synthesized successfully")

else:
    print("Error:", result.reason)


print("-------------------------")
##### speech to text

recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

print("Speak now...")
recognitiion_result = recognizer.recognize_once_async().get()

if recognitiion_result.reason == speechsdk.ResultReason.RecognizedSpeech:
    print("Recognised:", recognitiion_result.text)
else:
    print("Error:", recognitiion_result.reason)
