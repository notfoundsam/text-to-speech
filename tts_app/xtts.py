"""Coqui XTTS v2 synthesis module."""

import os
from pathlib import Path

# Auto-accept XTTS license (for personal/non-commercial use)
os.environ["COQUI_TOS_AGREED"] = "1"

import torch
from TTS.api import TTS

# XTTS supported languages
LANGUAGES = ["en", "ru", "es", "fr", "de", "it", "pt", "pl", "tr", "nl", "cs", "ar", "zh", "ja", "ko", "hu"]

DEFAULT_SAMPLE_RATE = 24000  # XTTS outputs 24kHz


class XttsTTS:
    """Wrapper for Coqui XTTS v2 model."""

    def __init__(self, language: str = "en"):
        """Initialize XTTS model.

        Args:
            language: Language code (e.g., 'en', 'ru').
        """
        if language not in LANGUAGES:
            raise ValueError(f"Unsupported language: {language}. Available: {LANGUAGES}")

        self.language = language
        self.sample_rate = DEFAULT_SAMPLE_RATE
        self._tts = None

    @property
    def tts(self):
        """Lazy load the TTS model."""
        if self._tts is None:
            self._tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            # Use CPU explicitly
            self._tts.to("cpu")
        return self._tts

    def synthesize(
        self,
        text: str,
        output_path: str | Path,
    ) -> Path:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize.
            output_path: Path for output WAV file.

        Returns:
            Path to the generated WAV file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.tts.tts_to_file(
            text=text,
            file_path=str(output_path),
            language=self.language,
        )

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


def list_languages() -> list[str]:
    """Get available language codes for XTTS.

    Returns:
        List of language codes.
    """
    return LANGUAGES.copy()
