from piper import PiperVoice
import wave
import io
import os

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
else:
    print("OK: Audio was generated")
