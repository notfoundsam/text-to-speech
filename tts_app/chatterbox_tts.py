"""Chatterbox TTS synthesis module."""

from pathlib import Path

import torch

# Chatterbox multilingual model weights are saved with CUDA tensors,
# which fails on CPU-only machines. Patch torch.load to force CPU mapping.
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    kwargs.setdefault("map_location", "cpu")
    kwargs.setdefault("weights_only", False)
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

import torchaudio

# Chatterbox supported languages
LANGUAGES = [
    "en", "ru", "es", "fr", "de", "it", "pt", "pl", "tr", "nl",
    "cs", "ar", "zh", "ja", "ko", "hu", "sv", "da", "fi", "no",
    "el", "ro", "uk",
]

# English uses the Turbo model, all others use Multilingual
TURBO_LANGUAGES = {"en"}

DEFAULT_SAMPLE_RATE = 24000


class ChatterboxTTS:
    """Wrapper for Chatterbox TTS (Turbo + Multilingual)."""

    def __init__(self, language: str = "en", voice: str = None):
        """Initialize Chatterbox TTS.

        Args:
            language: Language code (e.g., 'en', 'ru').
            voice: Path to reference WAV for voice cloning. Optional.
        """
        if language not in LANGUAGES:
            raise ValueError(f"Unsupported language: {language}. Available: {LANGUAGES}")

        self.language = language
        self.speaker_wav = voice
        self.sample_rate = DEFAULT_SAMPLE_RATE
        self._model = None

    @property
    def model(self):
        """Lazy load the Chatterbox model."""
        if self._model is None:
            if self.language in TURBO_LANGUAGES:
                from chatterbox.tts_turbo import ChatterboxTurboTTS

                self._model = ChatterboxTurboTTS.from_pretrained(device="cpu")
            else:
                from chatterbox.mtl_tts import ChatterboxMultilingualTTS

                self._model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
        return self._model

    def _get_speaker_wav(self) -> str | None:
        """Get path to reference speaker WAV file.

        Checks --voice parameter first, then /data/samples/ for a reference.
        """
        if self.speaker_wav:
            return self.speaker_wav

        # Check for a language-specific reference in samples dir
        samples_dir = Path("/data/samples")
        ref_file = samples_dir / f"reference_{self.language}.wav"
        if ref_file.exists():
            return str(ref_file)

        return None

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

        speaker_wav = self._get_speaker_wav()

        if self.language in TURBO_LANGUAGES:
            # Turbo model (English)
            if speaker_wav:
                wav = self.model.generate(text, audio_prompt_path=speaker_wav)
            else:
                wav = self.model.generate(text)
        else:
            # Multilingual model
            if speaker_wav:
                wav = self.model.generate(
                    text,
                    audio_prompt_path=speaker_wav,
                    language_id=self.language,
                )
            else:
                wav = self.model.generate(text, language_id=self.language)

        torchaudio.save(str(output_path), wav, self.model.sr)
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

            self.synthesize(chunk, output_path)
            wav_files.append(output_path)

            if progress_callback:
                progress_callback(i + 1, total)

        return wav_files, skipped


def list_languages() -> list[str]:
    """Get available language codes for Chatterbox.

    Returns:
        List of language codes.
    """
    return LANGUAGES.copy()
