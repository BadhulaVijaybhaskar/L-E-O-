import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
import pyttsx3
import os

# Path to your downloaded Vosk model
MODEL_PATH = r"D:\AI Models\J A R V I S\vosk-model-small-en-us-0.15"

# Initialize text-to-speech
engine = pyttsx3.init()
engine.setProperty("rate", 160)  # speaking speed
engine.setProperty("volume", 1.0)

# Queue for audio
q = queue.Queue()

def speak(text):
    print(f"🤖 Assistant: {text}")
    engine.say(text)
    engine.runAndWait()

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def listen_and_reply():
    if not os.path.exists(MODEL_PATH):
        print("⚠️ Vosk model not found. Please check the path.")
        return

    print("🔄 Loading Vosk model...")
    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, 16000)

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                           channels=1, callback=callback):
        speak("Hello sir, I am listening.")
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                text = json.loads(result)["text"]
                if text.strip():
                    print(f"🗣️ You said: {text}")
                    # Reply logic
                    if "hello" in text:
                        speak("Hello sir, how are you?")
                    elif "stop" in text or "exit" in text:
                        speak("Shutting down. Goodbye sir.")
                        break
                    else:
                        speak(f"You said {text}")

if __name__ == "__main__":
    listen_and_reply()
