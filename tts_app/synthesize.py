"""Silero TTS synthesis module."""

from pathlib import Path

import torch

# Available Russian voices in Silero v4
VOICES = {
    "xenia": "Female, clear and neutral",
    "aidar": "Male, deep and calm",
    "baya": "Female, warm and expressive",
    "kseniya": "Female, young and energetic",
    "eugene": "Male, standard and professional",
}

DEFAULT_VOICE = "aidar"
DEFAULT_SAMPLE_RATE = 48000


class SileroTTS:
    """Wrapper for Silero TTS model."""

    def __init__(self, sample_rate: int = DEFAULT_SAMPLE_RATE):
        """Initialize Silero TTS model.

        Args:
            sample_rate: Audio sample rate (24000 or 48000).
        """
        self.sample_rate = sample_rate
        self._model = None

    @property
    def model(self):
        """Lazy load the TTS model."""
        if self._model is None:
            self._model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language="ru",
                speaker="v4_ru",
            )
        return self._model

    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        voice: str = DEFAULT_VOICE,
    ) -> Path:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize.
            output_path: Path for output WAV file.
            voice: Voice name (see VOICES dict).

        Returns:
            Path to the generated WAV file.

        Raises:
            ValueError: If voice is not available.
        """
        if voice not in VOICES:
            raise ValueError(f"Unknown voice: {voice}. Available: {list(VOICES.keys())}")

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
        voice: str = DEFAULT_VOICE,
        progress_callback=None,
        resume: bool = False,
    ) -> list[Path]:
        """Synthesize multiple chunks to WAV files.

        Args:
            chunks: List of text chunks.
            output_dir: Directory for output WAV files.
            voice: Voice name.
            progress_callback: Optional callback(current, total) for progress.
            resume: If True, skip existing chunks.

        Returns:
            List of paths to generated WAV files.
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

            self.synthesize(chunk, output_path, voice)
            wav_files.append(output_path)

            if progress_callback:
                progress_callback(i + 1, total)

        return wav_files, skipped


def list_voices() -> dict[str, str]:
    """Get available voices and their descriptions.

    Returns:
        Dictionary mapping voice names to descriptions.
    """
    return VOICES.copy()
