"""Piper TTS synthesis module using piper-tts package."""

import wave
from pathlib import Path

from piper import PiperVoice

# Available Piper voices (model_name: description)
# Models are downloaded from https://huggingface.co/rhasspy/piper-voices
VOICES = {
    "en": {
        "en_US-lessac-medium": "US English, male, medium quality (default)",
        "en_US-lessac-high": "US English, male, high quality",
        "en_US-libritts-high": "US English, neutral, high quality",
        "en_US-amy-medium": "US English, female, medium quality",
        "en_US-ryan-medium": "US English, male, medium quality",
        "en_GB-alan-medium": "UK English, male, medium quality",
    },
    "ru": {
        "ru_RU-ruslan-medium": "Russian, male, medium quality",
        "ru_RU-irina-medium": "Russian, female, medium quality",
    },
}

DEFAULT_VOICES = {
    "en": "en_US-lessac-medium",
    "ru": "ru_RU-ruslan-medium",
}

PIPER_MODELS_DIR = Path("/data/piper-models")


def _download_voice(voice_name: str) -> tuple[Path, Path]:
    """Download voice model if not present.

    Returns:
        Tuple of (model_path, config_path)
    """
    import urllib.request

    PIPER_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    model_path = PIPER_MODELS_DIR / f"{voice_name}.onnx"
    config_path = PIPER_MODELS_DIR / f"{voice_name}.onnx.json"

    if model_path.exists() and config_path.exists():
        return model_path, config_path

    # Build URL path from voice name
    # e.g., en_US-lessac-medium -> en/en_US/lessac/medium/
    parts = voice_name.split("-")
    lang_region = parts[0]  # e.g., en_US
    lang = lang_region.split("_")[0]  # e.g., en
    name = parts[1]  # e.g., lessac
    quality = parts[2]  # e.g., medium

    base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
    model_url = f"{base_url}/{lang}/{lang_region}/{name}/{quality}/{voice_name}.onnx"
    config_url = f"{base_url}/{lang}/{lang_region}/{name}/{quality}/{voice_name}.onnx.json"

    print(f"Downloading Piper voice: {voice_name}...")

    # Download with progress
    def show_progress(block_num, block_size, total_size):
        if total_size > 0:
            percent = min(100, block_num * block_size * 100 // total_size)
            print(f"\r  Downloading: {percent}%", end="", flush=True)

    urllib.request.urlretrieve(model_url, model_path, show_progress)
    print()  # newline after progress
    urllib.request.urlretrieve(config_url, config_path)

    print(f"Voice downloaded: {voice_name}")
    return model_path, config_path


class PiperTTS:
    """Wrapper for Piper TTS."""

    def __init__(self, language: str = "en", voice: str = None):
        """Initialize Piper TTS.

        Args:
            language: Language code ('en' or 'ru').
            voice: Voice model name. If None, uses default for language.
        """
        if language not in VOICES:
            raise ValueError(f"Unsupported language: {language}. Available: {list(VOICES.keys())}")

        self.language = language
        self.voice_name = voice or DEFAULT_VOICES[language]

        if self.voice_name not in VOICES[language]:
            raise ValueError(f"Unknown voice: {self.voice_name}. Available: {list(VOICES[language].keys())}")

        # Download model if needed and load voice
        model_path, config_path = _download_voice(self.voice_name)
        self._voice = PiperVoice.load(str(model_path), config_path=str(config_path))

    def synthesize(self, text: str, output_path: str | Path) -> Path:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize.
            output_path: Path for output WAV file.

        Returns:
            Path to the generated WAV file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Synthesize to WAV
        # Pre-configure WAV params in case Piper's generator yields nothing
        # (e.g., punctuation-only text producing no phonemes in piper-tts 1.4.0+)
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setframerate(self._voice.config.sample_rate)
            wav_file.setsampwidth(2)
            wav_file.setnchannels(1)
            self._voice.synthesize(text, wav_file)

        return output_path

    def synthesize_chunks(
        self,
        chunks: list[str],
        output_dir: str | Path,
        progress_callback=None,
        resume: bool = False,
    ) -> tuple[list[Path], int]:
        """Synthesize multiple chunks to WAV files.

        Args:
            chunks: List of text chunks.
            output_dir: Directory for output WAV files.
            progress_callback: Optional callback(current, total) for progress.
            resume: If True, skip existing chunks.

        Returns:
            Tuple of (list of paths to generated WAV files, number of skipped chunks).
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        wav_files = []
        total = len(chunks)
        skipped = 0

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            output_path = output_dir / f"chunk_{i:04d}.wav"

            # Skip if file exists and resume is enabled
            if resume and output_path.exists() and output_path.stat().st_size > 0:
                wav_files.append(output_path)
                skipped += 1
                if progress_callback:
                    progress_callback(i + 1, total)
                continue

            self.synthesize(chunk, output_path)
            wav_files.append(output_path)

            if progress_callback:
                progress_callback(i + 1, total)

        return wav_files, skipped


def list_voices(language: str = None) -> dict:
    """Get available voices.

    Args:
        language: Language to filter by. If None, returns all.

    Returns:
        Dictionary of voices.
    """
    if language is None:
        return {lang: voices.copy() for lang, voices in VOICES.items()}
    if language not in VOICES:
        raise ValueError(f"Unsupported language: {language}")
    return VOICES[language].copy()


def list_languages() -> list[str]:
    """Get available language codes."""
    return list(VOICES.keys())
