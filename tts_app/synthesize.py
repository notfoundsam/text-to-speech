"""Silero TTS synthesis module."""

from pathlib import Path

import torch

# Available voices per language
VOICES = {
    "ru": {
        "aidar": "Male, deep and calm",
        "baya": "Female, warm and expressive",
        "kseniya": "Female, young and energetic",
        "xenia": "Female, clear and neutral",
        "eugene": "Male, standard and professional",
    },
    "en": {
        "en_0": "Male, neutral",
        "en_1": "Male, calm",
        "en_2": "Female, clear",
        "en_3": "Female, expressive",
        "en_4": "Male, deep",
    },
}

# Default voices per language
DEFAULT_VOICES = {
    "ru": "aidar",
    "en": "en_0",
}

# Silero model speakers per language
MODEL_SPEAKERS = {
    "ru": "v4_ru",
    "en": "v3_en",
}

DEFAULT_LANGUAGE = "ru"
DEFAULT_SAMPLE_RATE = 48000


class SileroTTS:
    """Wrapper for Silero TTS model."""

    def __init__(self, language: str = DEFAULT_LANGUAGE, sample_rate: int = DEFAULT_SAMPLE_RATE):
        """Initialize Silero TTS model.

        Args:
            language: Language code ('ru' or 'en').
            sample_rate: Audio sample rate (24000 or 48000).
        """
        if language not in VOICES:
            raise ValueError(f"Unsupported language: {language}. Available: {list(VOICES.keys())}")

        self.language = language
        self.sample_rate = sample_rate
        self._model = None

    @property
    def model(self):
        """Lazy load the TTS model."""
        if self._model is None:
            try:
                self._model, _ = torch.hub.load(
                    repo_or_dir="snakers4/silero-models",
                    model="silero_tts",
                    language=self.language,
                    speaker=MODEL_SPEAKERS[self.language],
                )
            except Exception as e:
                raise RuntimeError(f"Failed to load Silero model for '{self.language}': {e}") from e
        return self._model

    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        voice: str | None = None,
    ) -> Path:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize.
            output_path: Path for output WAV file.
            voice: Voice name (see VOICES dict). If None, uses default for language.

        Returns:
            Path to the generated WAV file.

        Raises:
            ValueError: If voice is not available.
        """
        if voice is None:
            voice = DEFAULT_VOICES[self.language]

        available_voices = VOICES[self.language]
        if voice not in available_voices:
            raise ValueError(
                f"Unknown voice: {voice}. Available for {self.language}: {list(available_voices.keys())}"
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.model.save_wav(
            text=text,
            speaker=voice,
            sample_rate=self.sample_rate,
            audio_path=str(output_path),
        )

        return output_path

    def synthesize_chunks(
        self,
        chunks: list[str],
        output_dir: str | Path,
        voice: str | None = None,
        progress_callback=None,
        resume: bool = False,
    ) -> tuple[list[Path], int]:
        """Synthesize multiple chunks to WAV files.

        Args:
            chunks: List of text chunks.
            output_dir: Directory for output WAV files.
            voice: Voice name. If None, uses default for language.
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
        chunk_idx = 0

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            output_path = output_dir / f"chunk_{chunk_idx:04d}.wav"
            chunk_idx += 1

            # Skip if file exists and resume is enabled
            if resume:
                try:
                    if output_path.exists() and output_path.stat().st_size > 0:
                        wav_files.append(output_path)
                        skipped += 1
                        if progress_callback:
                            progress_callback(i + 1, total)
                        continue
                except OSError:
                    pass  # File disappeared between checks, re-synthesize

            self.synthesize(chunk, output_path, voice)
            wav_files.append(output_path)

            if progress_callback:
                progress_callback(i + 1, total)

        return wav_files, skipped


def list_voices(language: str | None = None) -> dict:
    """Get available voices and their descriptions.

    Args:
        language: Language code to filter by. If None, returns all languages.

    Returns:
        Dictionary mapping voice names to descriptions.
    """
    if language is None:
        return {lang: voices.copy() for lang, voices in VOICES.items()}
    if language not in VOICES:
        raise ValueError(f"Unsupported language: {language}. Available: {list(VOICES.keys())}")
    return VOICES[language].copy()


def list_languages() -> list[str]:
    """Get available language codes.

    Returns:
        List of language codes.
    """
    return list(VOICES.keys())
