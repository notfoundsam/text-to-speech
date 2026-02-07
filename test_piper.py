import os
os.environ["ESPEAK_DATA_PATH"] = "/usr/local/lib/python3.11/site-packages/piper/espeak-ng-data"

from piper import PiperVoice
import wave
import io

model_path = "/data/piper-models/en_US-lessac-medium.onnx"
config_path = "/data/piper-models/en_US-lessac-medium.onnx.json"

if not os.path.exists(model_path):
    print(f"Model not found: {model_path}")
    exit(1)

voice = PiperVoice.load(model_path, config_path=config_path)

buf = io.BytesIO()
with wave.open(buf, "wb") as wf:
    wf.setframerate(voice.config.sample_rate)
    wf.setsampwidth(2)
    wf.setnchannels(1)
    voice.synthesize("Hello world, this is a test.", wf)

print(f"WAV size: {buf.tell()} bytes")

if buf.tell() < 100:
    print("PROBLEM: WAV is essentially empty")

    # Try without setting ESPEAK_DATA_PATH
    print("\nTrying without ESPEAK_DATA_PATH...")
    del os.environ["ESPEAK_DATA_PATH"]

    voice2 = PiperVoice.load(model_path, config_path=config_path)
    buf2 = io.BytesIO()
    with wave.open(buf2, "wb") as wf2:
        wf2.setframerate(voice2.config.sample_rate)
        wf2.setsampwidth(2)
        wf2.setnchannels(1)
        voice2.synthesize("Hello world, this is a test.", wf2)
    print(f"WAV size without env: {buf2.tell()} bytes")
else:
    print("OK: Audio was generated")
