"""Edge-TTS synthesis module (Microsoft neural TTS, requires internet)."""

import sys
import time
from pathlib import Path

import edge_tts

MAX_RETRIES = 5
RETRY_BASE_DELAY = 5  # seconds

# Available voices per language
VOICES = {
    "ru": {
        "ru-RU-DmitryNeural": "Russian male, deep (default)",
        "ru-RU-SvetlanaNeural": "Russian female, clear",
    },
    "en": {
        "en-US-GuyNeural": "American male, standard (default)",
        "en-US-AriaNeural": "American female, expressive",
        "en-US-JennyNeural": "American female, warm",
        "en-US-ChristopherNeural": "American male, calm",
        "en-US-EricNeural": "American male, deep",
        "en-US-MichelleNeural": "American female, clear",
        "en-US-RogerNeural": "American male, mature",
        "en-US-SteffanNeural": "American male, professional",
    },
    "en_gb": {
        "en-GB-RyanNeural": "British male, standard (default)",
        "en-GB-SoniaNeural": "British female, warm",
        "en-GB-ThomasNeural": "British male, calm",
        "en-GB-LibbyNeural": "British female, clear",
    },
}

DEFAULT_VOICES = {
    "ru": "ru-RU-DmitryNeural",
    "en": "en-US-GuyNeural",
    "en_gb": "en-GB-RyanNeural",
}


class EdgeTTS:
    """Wrapper for Edge-TTS (Microsoft neural TTS)."""

    def __init__(self, language: str = "ru", voice: str = None):
        if language not in VOICES:
            raise ValueError(f"Unsupported language: {language}. Available: {list(VOICES.keys())}")

        self.language = language
        self.voice_name = voice or DEFAULT_VOICES[language]

        if self.voice_name not in VOICES[language]:
            raise ValueError(f"Unknown voice: {self.voice_name}. Available: {list(VOICES[language].keys())}")

    def synthesize(self, text: str, output_path: str | Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        for attempt in range(MAX_RETRIES):
            try:
                communicate = edge_tts.Communicate(text, self.voice_name)
                communicate.save_sync(str(output_path))
                return output_path
            except Exception as e:
                if "503" in str(e) and attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    print(f"\n  Rate limited (503), retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})...", file=sys.stderr)
                    time.sleep(delay)
                else:
                    raise

    def synthesize_chunks(
        self,
        chunks: list[str],
        output_dir: str | Path,
        progress_callback=None,
        resume: bool = False,
    ) -> tuple[list[Path], int]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        audio_files = []
        total = len(chunks)
        skipped = 0

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            output_path = output_dir / f"chunk_{i:04d}.mp3"

            if resume and output_path.exists() and output_path.stat().st_size > 0:
                audio_files.append(output_path)
                skipped += 1
                if progress_callback:
                    progress_callback(i + 1, total)
                continue

            self.synthesize(chunk, output_path)
            audio_files.append(output_path)

            if progress_callback:
                progress_callback(i + 1, total)

        return audio_files, skipped


def list_voices(language: str = None) -> dict:
    if language is None:
        return {lang: voices.copy() for lang, voices in VOICES.items()}
    if language not in VOICES:
        raise ValueError(f"Unsupported language: {language}")
    return VOICES[language].copy()


def list_languages() -> list[str]:
    return list(VOICES.keys())
