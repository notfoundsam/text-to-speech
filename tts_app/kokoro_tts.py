"""Kokoro TTS synthesis module."""

from pathlib import Path

import numpy as np
import soundfile as sf

# Language code mapping for Kokoro
LANG_CODES = {
    "en": "a",
    "en_gb": "b",
    "es": "e",
    "fr": "f",
    "ja": "j",
    "zh": "z",
    "hi": "h",
    "it": "i",
    "pt": "p",
}

# Available Kokoro voices per language
VOICES = {
    "en": {
        "af_heart": "American female, warm (default)",
        "af_alloy": "American female, neutral",
        "af_aoede": "American female, expressive",
        "af_bella": "American female, soft",
        "af_jessica": "American female, clear",
        "af_kore": "American female, bright",
        "af_nicole": "American female, calm",
        "af_nova": "American female, energetic",
        "af_river": "American female, smooth",
        "af_sarah": "American female, professional",
        "af_sky": "American female, light",
        "am_adam": "American male, deep",
        "am_echo": "American male, resonant",
        "am_eric": "American male, standard",
        "am_liam": "American male, warm",
        "am_michael": "American male, clear",
        "am_onyx": "American male, rich",
    },
    "en_gb": {
        "bf_alice": "British female, clear (default)",
        "bf_emma": "British female, warm",
        "bf_isabella": "British female, elegant",
        "bf_lily": "British female, soft",
        "bm_daniel": "British male, standard",
        "bm_fable": "British male, storytelling",
        "bm_george": "British male, deep",
        "bm_lewis": "British male, calm",
    },
    "es": {
        "ef_dora": "Spanish female (default)",
        "em_alex": "Spanish male",
        "em_santa": "Spanish male, warm",
    },
    "fr": {
        "ff_siwis": "French female (default)",
    },
    "ja": {
        "jf_alpha": "Japanese female (default)",
        "jf_gongitsune": "Japanese female, storytelling",
        "jf_nezumi": "Japanese female, bright",
        "jf_tebukuro": "Japanese female, soft",
        "jm_kumo": "Japanese male",
    },
    "zh": {
        "zf_xiaobei": "Chinese female (default)",
        "zf_xiaoni": "Chinese female, warm",
        "zf_xiaoxiao": "Chinese female, bright",
        "zf_xiaoyi": "Chinese female, clear",
        "zm_yunjian": "Chinese male",
        "zm_yunxi": "Chinese male, standard",
        "zm_yunxia": "Chinese male, calm",
        "zm_yunyang": "Chinese male, deep",
    },
    "hi": {
        "hf_alpha": "Hindi female (default)",
        "hf_beta": "Hindi female, warm",
        "hm_omega": "Hindi male",
        "hm_psi": "Hindi male, deep",
    },
    "it": {
        "if_sara": "Italian female (default)",
        "im_nicola": "Italian male",
    },
    "pt": {
        "pf_dora": "Portuguese female (default)",
        "pm_alex": "Portuguese male",
        "pm_santa": "Portuguese male, warm",
    },
}

DEFAULT_VOICES = {
    "en": "af_heart",
    "en_gb": "bf_alice",
    "es": "ef_dora",
    "fr": "ff_siwis",
    "ja": "jf_alpha",
    "zh": "zf_xiaobei",
    "hi": "hf_alpha",
    "it": "if_sara",
    "pt": "pf_dora",
}

DEFAULT_SAMPLE_RATE = 24000


class KokoroTTS:
    """Wrapper for Kokoro TTS."""

    def __init__(self, language: str = "en", voice: str = None):
        """Initialize Kokoro TTS.

        Args:
            language: Language code (e.g., 'en', 'en_gb', 'ja').
            voice: Voice name. If None, uses default for language.
        """
        if language not in VOICES:
            raise ValueError(f"Unsupported language: {language}. Available: {list(VOICES.keys())}")

        self.language = language
        self.voice_name = voice or DEFAULT_VOICES[language]

        if self.voice_name not in VOICES[language]:
            raise ValueError(f"Unknown voice: {self.voice_name}. Available: {list(VOICES[language].keys())}")

        self.sample_rate = DEFAULT_SAMPLE_RATE
        self._pipeline = None

    @property
    def pipeline(self):
        """Lazy load the Kokoro pipeline."""
        if self._pipeline is None:
            from kokoro import KPipeline

            lang_code = LANG_CODES[self.language]
            self._pipeline = KPipeline(lang_code=lang_code)
        return self._pipeline

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

        # Generate audio segments
        segments = []
        for _graphemes, _phonemes, audio in self.pipeline(text, voice=self.voice_name):
            if audio is not None:
                segments.append(audio)

        if segments:
            audio_concat = np.concatenate(segments)
        else:
            # Empty audio fallback
            audio_concat = np.zeros(self.sample_rate, dtype=np.float32)

        sf.write(str(output_path), audio_concat, self.sample_rate)
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
