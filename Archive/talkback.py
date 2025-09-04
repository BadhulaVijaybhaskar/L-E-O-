import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
import pyttsx3
import os
import threading
from typing import Optional

# ---------------------------
# Config constants
# ---------------------------
MODEL_PATH = r"D:\AI Models\J A R V I S\vosk-model-en-in-0.5"
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000

# ---------------------------
# Queues
# ---------------------------
speech_queue: queue.Queue[str] = queue.Queue()
audio_queue: queue.Queue[bytes] = queue.Queue()

# ---------------------------
# Initialize TTS
# ---------------------------
try:
    engine = pyttsx3.init("sapi5")
    voices = engine.getProperty("voices")
    if voices:
        engine.setProperty("voice", voices[0].id)  # pick first available voice
    engine.setProperty("rate", 160)
    engine.setProperty("volume", 1.0)
except Exception as e:
    print(f"⚠️ Failed to initialize TTS engine: {e}")
    engine = None

# ---------------------------
# TTS Worker Thread
# ---------------------------
def tts_worker():
    """Background thread for text-to-speech."""
    while True:
        text = speech_queue.get()
        if text == "EXIT":
            break
        if engine:
            try:
                print(f"🤖 Assistant: {text}")
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"⚠️ TTS error: {e}")
        speech_queue.task_done()

tts_thread = threading.Thread(target=tts_worker)
tts_thread.start()

def speak(text: str) -> None:
    """Put text into the speech queue."""
    speech_queue.put(text)

# ---------------------------
# Audio Callback
# ---------------------------
def callback(indata, frames, time, status):
    if status:
        print(status)
    audio_queue.put(bytes(indata))

# ---------------------------
# Command Processing
# ---------------------------
def process_command(text: str) -> Optional[bool]:
    """
    Process recognized speech.
    Return False to exit, True to continue.
    """
    text = text.lower().strip()
    print(f"🗣️ You said: {text}")

    if "hello" in text:
        speak("Hello sir, how are you?")
    elif "stop" in text or "exit" in text:
        speak("Shutting down. Goodbye sir.")
        return False
    else:
        speak(f"You said: {text}")

    return True

# ---------------------------
# Main Loop
# ---------------------------
def listen_and_reply() -> None:
    if not os.path.exists(MODEL_PATH):
        print("⚠️ Vosk model not found. Please check the path.")
        return

    print("🔄 Loading Vosk model...")
    try:
        model = Model(MODEL_PATH)
        recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    except Exception as e:
        print(f"⚠️ Failed to load model: {e}")
        return

    speak("Hello sir, I am listening.")

    try:
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
                               dtype="int16", channels=1, callback=callback):
            while True:
                data = audio_queue.get()
                try:
                    if recognizer.AcceptWaveform(data):
                        result = recognizer.Result()
                        text = json.loads(result).get("text", "").strip()
                        if text:
                            if not process_command(text):
                                break
                        else:
                            speak("Sorry sir, I didn’t catch that.")
                except Exception as e:
                    print(f"⚠️ Recognition error: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user. Shutting down.")

    # Graceful shutdown
    speech_queue.put("EXIT")
    tts_thread.join()
    print("✅ Assistant shut down gracefully.")

# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    listen_and_reply()


