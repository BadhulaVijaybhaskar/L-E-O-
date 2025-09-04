import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
import pyttsx3
import os
import threading
import time
import sys
from pathlib import Path
from core.constants import ASSISTANT_NAME

# Windows-only beep (fastest). On non-Windows, we’ll fall back to TTS.
if sys.platform.startswith("win"):
    import winsound

from core.config import load_config, get_key
from core.wake_word import WakeWordDetector
from core.ui import show_listening, show_sleeping, show_message
from core.history import HistoryRecorder

MODEL_PATH = r"D:\AI Models\J A R V I S\vosk-model-en-in-0.5"
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000

q = queue.Queue()
stream = None  # Vosk mic stream

# session state
_session_state = {
    "mode": "sleep",           # "sleep" | "recognize"
    "last_activity": 0.0       # monotonic timestamp of last recognized speech
}

def now():
    return time.monotonic()

def beep():
    """Short confirmation beep on wake (Windows fast path)."""
    if sys.platform.startswith("win"):
        try:
            winsound.Beep(880, 120)
            winsound.Beep(1320, 120)
            return
        except Exception:
            pass
    # fallback: quick TTS chirp
    speak("ding")

def speak(text: str):
    """Stop mic stream, speak with TTS, then restart mic stream if in recognize mode."""
    global stream, history
    print(f"🤖 Assistant: {text}")
    if history:
        history.log({ASSISTANT_NAME}, text)

    if stream:
        try:
            stream.stop()
            stream.close()
        except Exception as e:
            print(f"⚠️ Error stopping stream: {e}")

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

    try:
        if recognizer_active():
            start_vosk_stream()
    except Exception as e:
        print(f"⚠️ Error starting stream: {e}")

def callback(indata, frames, time_info, status):
    if status:
        print(status)
    q.put(bytes(indata))

def start_vosk_stream():
    global stream
    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="int16",
        channels=1,
        callback=callback
    )
    stream.start()

def recognizer_active() -> bool:
    return _session_state.get("mode") == "recognize"

def wait_for_wake(cfg):
    # Ensure key exists (clear error if missing)
    get_key("PICOVOICE_ACCESS_KEY")
    detector = WakeWordDetector(
        keyword=cfg["wake_word"],
        sensitivity=float(cfg["wake_sensitivity"])
    )
    try:
        if cfg.get("overlay_enabled", True):
            show_sleeping()
        print(f"👂 Waiting for wake word: '{cfg['wake_word']}' …")
        detector.listen()
    finally:
        detector.close()

def vosk_session(model, recognizer, cfg):
    from skills.registry import load_skills, dispatch

    skills = load_skills()
    print(f"🧩 Loaded skills: {', '.join([s.name for s in skills]) or 'none'}")
    if history:
        history.event(f"Skills loaded: {', '.join([s.name for s in skills]) or 'none'}")

    _session_state["mode"] = "recognize"
    _session_state["last_activity"] = now()

    start_vosk_stream()

    # Visual + audio confirmation on wake
    if cfg.get("overlay_enabled", True):
        show_listening()
    if cfg.get("beep_on_wake", True):
        beep()
    else:
        speak("I'm listening.")

    timeout_sec = int(cfg.get("session_timeout_sec", 120))

    def audio_processor():
        while recognizer_active():
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                text = json.loads(result).get("text", "").strip().lower()
                if text:
                    print(f"🗣️ You said: {text}")
                    if history:
                        history.log("You", text)
                    _session_state["last_activity"] = now()

                    if any(k in text for k in ("stop", "exit", "shutdown", "quit")):
                        speak("Goodbye sir, shutting down.")
                        if history:
                            history.event("System exiting by voice command.")
                        os._exit(0)

                    if any(k in text for k in ("go to sleep", "stop listening", "sleep mode")):
                        speak("Going to sleep. Say the wake word to activate me.")
                        if history:
                            history.event("Going to sleep by voice command.")
                        _session_state["mode"] = "sleep"
                        break

                    handled = dispatch(text, speak)
                    if history:
                        history.event(f"Dispatch handled={handled}")
                    if not handled:
                        # Optional: fallback
                        pass

    processor_thread = threading.Thread(target=audio_processor, daemon=True)
    processor_thread.start()

    # Keep device alive and check for inactivity timeout
    try:
        with stream:
            while recognizer_active():
                sd.sleep(100)
                if timeout_sec > 0 and (now() - _session_state["last_activity"]) > timeout_sec:
                    speak("No activity detected. Going to sleep.")
                    if history:
                        history.event("Auto-sleep due to inactivity.")
                    _session_state["mode"] = "sleep"
                    break
    finally:
        try:
            if stream:
                stream.stop()
                stream.close()
        except Exception:
            pass
        if cfg.get("overlay_enabled", True):
            show_sleeping()

def main():
    global history
    cfg = load_config()

    # History setup
    logs_dir = Path(cfg.get("history_dir", "logs"))
    history_enabled = bool(cfg.get("history_enabled", True))
    history = HistoryRecorder(logs_dir, enabled=history_enabled)

    if not os.path.exists(MODEL_PATH):
        msg = "Vosk model not found, check MODEL_PATH."
        print("⚠️ " + msg)
        if history:
            history.event(msg)
        return

    print("🔄 Loading Vosk model…")
    if history:
        history.event("Loading Vosk model")
    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)

    while True:
        _session_state["mode"] = "sleep"
        wait_for_wake(cfg)
        if history:
            history.event("Wake word detected")
        vosk_session(model, recognizer, cfg)

if __name__ == "__main__":
    main()
