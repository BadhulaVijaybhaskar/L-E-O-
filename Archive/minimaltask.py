import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
import pyttsx3
import os
import threading

MODEL_PATH = r"D:\AI Models\J A R V I S\vosk-model-en-in-0.5"
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000

q = queue.Queue()
stream = None

def speak(text: str):
    """
    Stops the mic stream, re-initializes the TTS engine,
    speaks, and then restarts the mic stream.
    """
    global stream
    print(f"🤖 Assistant: {text}")

    # Stop the microphone stream
    if stream:
        try:
            stream.stop()
            stream.close()
            print("Microphone stream stopped.")
        except Exception as e:
            print(f"⚠️ Error stopping stream: {e}")

    # Re-initialize the pyttsx3 engine for each utterance
    try:
        engine = pyttsx3.init("sapi5")
        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id)
        engine.setProperty("rate", 160)
        engine.setProperty("volume", 1.0)
        
        engine.say(text)
        engine.runAndWait()
        
    except Exception as e:
        print(f"⚠️ TTS error: {e}")
    
    # Restart the microphone stream
    try:
        stream = sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
                                   dtype="int16", channels=1, callback=callback)
        stream.start()
        print("✅ Microphone stream restarted. Waiting for your input...")
    except Exception as e:
        print(f"⚠️ Error starting stream: {e}")


def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def main():
    global stream
    if not os.path.exists(MODEL_PATH):
        print("⚠️ Model not found, check path.")
        return

    print("🔄 Loading Vosk model...")
    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)

    # Initial stream setup
    stream = sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
                               dtype="int16", channels=1, callback=callback)
    
    # Intro message
    speak("Hello sir, I am listening. Say hello to test.")

    def audio_processor():
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                text = json.loads(result).get("text", "").strip().lower()
                if text:
                    print(f"🗣️ You said: {text}")
                    if "hello" in text:
                        speak("Hello sir, this is your assistant speaking.")
                    elif "stop" in text or "exit" in text:
                        speak("Goodbye sir, shutting down.")
                        os._exit(0)

    processor_thread = threading.Thread(target=audio_processor, daemon=True)
    processor_thread.start()

    with stream:
        while True:
            sd.sleep(100) # Keep the main thread alive

if __name__ == "__main__":
    main()