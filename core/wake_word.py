import os
import struct
import sys
import pvporcupine
import sounddevice as sd
from core.config import get_key

class WakeWordDetector:
    """
    Porcupine-based wake word detector.
    Keyword and sensitivity should be provided at init (or pulled from config).
    """
    def __init__(self, keyword="Leo", sensitivity=0.7):
        access_key = get_key("PICOVOICE_ACCESS_KEY")
        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keywords=[keyword],
            sensitivities=[sensitivity]
        )

        try:
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=[keyword],
                sensitivities=[sensitivity]
            )
        except Exception as e:
            raise RuntimeError(f"Error initializing Porcupine: {e}")

        # Sounddevice raw stream that matches Porcupine expectations
        self.stream = sd.RawInputStream(
            samplerate=self.porcupine.sample_rate,
            blocksize=self.porcupine.frame_length,
            dtype="int16",
            channels=1,
            callback=self._audio_callback
        )

        self.detected = False

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        pcm = struct.unpack_from("h" * self.porcupine.frame_length, indata)
        result = self.porcupine.process(pcm)
        if result >= 0:
            print("Wake word detected!")
            self.detected = True

    def listen(self):
        """Block until wake word is detected."""
        print("Listening for wake word...")
        with self.stream:
            while not self.detected:
                sd.sleep(10)  # yield to audio thread

    def close(self):
        try:
            self.stream.close()
        except Exception:
            pass
        try:
            self.porcupine.delete()
        except Exception:
            pass
