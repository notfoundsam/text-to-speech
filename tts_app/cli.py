"""Command-line interface for TTS."""

import argparse
import sys
from pathlib import Path

from .extract import extract_text
from .preprocess import preprocess
from .synthesize import (
    SileroTTS,
    list_voices as silero_list_voices,
    list_languages as silero_list_languages,
    DEFAULT_LANGUAGE,
    DEFAULT_VOICES as SILERO_DEFAULT_VOICES,
    DEFAULT_SAMPLE_RATE,
)

# Maximum chunk size per engine/language
MAX_CHUNK_CHARS = {
    "silero": {"ru": 500, "en": 250},
    "xtts": {"default": 170},
    "piper": {"default": 500},
    "kokoro": {"default": 400},
    "chatterbox": {"default": 400},
}

ENGINES = ["silero", "xtts", "piper", "kokoro", "chatterbox"]


def print_progress(current: int, total: int):
    """Print progress bar to stderr."""
    bar_width = 40
    progress = current / total
    filled = int(bar_width * progress)
    bar = "=" * filled + "-" * (bar_width - filled)
    sys.stderr.write(f"\r[{bar}] {current}/{total} chunks")
    sys.stderr.flush()
    if current == total:
        sys.stderr.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF/EPUB to speech using TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "input",
        nargs="?",
        help="Path to input PDF or EPUB file",
    )

    parser.add_argument(
        "--chunks-dir",
        default="/data/chunks",
        help="Directory for output WAV chunks (default: /data/chunks)",
    )

    parser.add_argument(
        "--engine",
        default="silero",
        choices=ENGINES,
        help="TTS engine: silero (fast), piper (fast, good English), kokoro (fast, multi-voice English), chatterbox (voice cloning), xtts (slow, best quality). Default: silero",
    )

    parser.add_argument(
        "--lang",
        default=DEFAULT_LANGUAGE,
        help=f"Language code (default: {DEFAULT_LANGUAGE})",
    )

    parser.add_argument(
        "--voice",
        default=None,
        help="Voice to use. Use --list-voices to see options.",
    )

    parser.add_argument(
        "--sample-rate",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        choices=[22050, 24000, 48000],
        help=f"Audio sample rate (default: {DEFAULT_SAMPLE_RATE})",
    )

    parser.add_argument(
        "--max-chunk-chars",
        type=int,
        default=None,
        help="Maximum characters per chunk (default: auto based on engine/language)",
    )

    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available voices and exit",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing chunks (skip already generated files)",
    )

    args = parser.parse_args()

    # Handle --list-voices
    if args.list_voices:
        print("=== Silero voices ===")
        all_silero = silero_list_voices()
        for lang, voices in all_silero.items():
            default = SILERO_DEFAULT_VOICES[lang]
            print(f"\n{lang.upper()}:")
            for name, description in voices.items():
                marker = " (default)" if name == default else ""
                print(f"  {name:10} - {description}{marker}")

        print("\n=== Piper voices ===")
        from .piper_tts import list_voices as piper_list_voices, DEFAULT_VOICES as PIPER_DEFAULT_VOICES
        all_piper = piper_list_voices()
        for lang, voices in all_piper.items():
            default = PIPER_DEFAULT_VOICES[lang]
            print(f"\n{lang.upper()}:")
            for name, description in voices.items():
                marker = " (default)" if name == default else ""
                print(f"  {name} - {description}{marker}")

        print("\n=== Kokoro voices ===")
        from .kokoro_tts import list_voices as kokoro_list_voices, DEFAULT_VOICES as KOKORO_DEFAULT_VOICES
        all_kokoro = kokoro_list_voices()
        for lang, voices in all_kokoro.items():
            default = KOKORO_DEFAULT_VOICES[lang]
            print(f"\n{lang.upper()}:")
            for name, description in voices.items():
                marker = " (default)" if name == default else ""
                print(f"  {name:20} - {description}{marker}")

        print("\n=== Chatterbox ===")
        print("Voice cloning engine (--voice <path_to_reference.wav>)")
        from .chatterbox_tts import list_languages as chatterbox_list_languages
        print(f"Languages: {', '.join(chatterbox_list_languages())}")

        print("\n=== XTTS ===")
        print("Uses built-in voice (no selection needed)")
        print("Languages: en, ru, es, fr, de, it, pt, pl, tr, nl, cs, ar, zh, ja, ko, hu")
        return 0

    # Require input file if not listing voices
    if not args.input:
        parser.error("the following arguments are required: input")

    input_path = Path(args.input)
    chunks_dir = Path(args.chunks_dir)

    # Extract text
    if not args.quiet:
        print(f"Extracting text from: {input_path.name}", file=sys.stderr)

    try:
        text = extract_text(input_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Determine max chunk size
    if args.max_chunk_chars:
        max_chars = args.max_chunk_chars
    elif args.engine in MAX_CHUNK_CHARS:
        max_chars = MAX_CHUNK_CHARS[args.engine].get(args.lang, MAX_CHUNK_CHARS[args.engine].get("default", 500))
    else:
        max_chars = 500

    # Preprocess
    if not args.quiet:
        print("Preprocessing text...", file=sys.stderr)

    chunks = preprocess(text, max_chunk_chars=max_chars)

    if not chunks:
        print("Error: No text chunks to process", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Generated {len(chunks)} chunks", file=sys.stderr)

    progress_fn = None if args.quiet else print_progress

    # Initialize TTS engine
    if args.engine == "piper":
        from .piper_tts import PiperTTS, list_voices as piper_list_voices, list_languages as piper_list_languages, DEFAULT_VOICES as PIPER_DEFAULT_VOICES

        # Validate language
        piper_languages = piper_list_languages()
        if args.lang not in piper_languages:
            print(f"Error: Language '{args.lang}' not supported by Piper", file=sys.stderr)
            print(f"Available: {', '.join(piper_languages)}", file=sys.stderr)
            return 1

        # Set default voice
        voice = args.voice or PIPER_DEFAULT_VOICES[args.lang]

        if not args.quiet:
            print(f"Synthesizing with Piper voice: {voice} ({args.lang})", file=sys.stderr)

        try:
            tts = PiperTTS(language=args.lang, voice=voice)
            wav_files, skipped = tts.synthesize_chunks(
                chunks=chunks,
                output_dir=chunks_dir,
                progress_callback=progress_fn,
                resume=args.resume,
            )
        except Exception as e:
            print(f"Error during synthesis: {e}", file=sys.stderr)
            return 1

    elif args.engine == "xtts":
        from .xtts import XttsTTS, list_languages as xtts_list_languages

        # Validate language
        xtts_languages = xtts_list_languages()
        if args.lang not in xtts_languages:
            print(f"Error: Language '{args.lang}' not supported by XTTS", file=sys.stderr)
            print(f"Available: {', '.join(xtts_languages)}", file=sys.stderr)
            return 1

        if not args.quiet:
            print(f"Synthesizing with XTTS ({args.lang})", file=sys.stderr)
            print("Note: XTTS is slower but higher quality", file=sys.stderr)

        try:
            tts = XttsTTS(language=args.lang)
            wav_files, skipped = tts.synthesize_chunks(
                chunks=chunks,
                output_dir=chunks_dir,
                progress_callback=progress_fn,
                resume=args.resume,
            )
        except Exception as e:
            print(f"Error during synthesis: {e}", file=sys.stderr)
            return 1

    elif args.engine == "kokoro":
        from .kokoro_tts import KokoroTTS, list_languages as kokoro_list_languages, DEFAULT_VOICES as KOKORO_DEFAULT_VOICES

        # Validate language
        kokoro_languages = kokoro_list_languages()
        if args.lang not in kokoro_languages:
            print(f"Error: Language '{args.lang}' not supported by Kokoro", file=sys.stderr)
            print(f"Available: {', '.join(kokoro_languages)}", file=sys.stderr)
            return 1

        # Set default voice
        voice = args.voice or KOKORO_DEFAULT_VOICES[args.lang]

        if not args.quiet:
            print(f"Synthesizing with Kokoro voice: {voice} ({args.lang})", file=sys.stderr)

        try:
            tts = KokoroTTS(language=args.lang, voice=voice)
            wav_files, skipped = tts.synthesize_chunks(
                chunks=chunks,
                output_dir=chunks_dir,
                progress_callback=progress_fn,
                resume=args.resume,
            )
        except Exception as e:
            print(f"Error during synthesis: {e}", file=sys.stderr)
            return 1

    elif args.engine == "chatterbox":
        from .chatterbox_tts import ChatterboxTTS, list_languages as chatterbox_list_languages

        # Validate language
        chatterbox_languages = chatterbox_list_languages()
        if args.lang not in chatterbox_languages:
            print(f"Error: Language '{args.lang}' not supported by Chatterbox", file=sys.stderr)
            print(f"Available: {', '.join(chatterbox_languages)}", file=sys.stderr)
            return 1

        if not args.quiet:
            voice_info = f" with reference: {args.voice}" if args.voice else ""
            print(f"Synthesizing with Chatterbox ({args.lang}){voice_info}", file=sys.stderr)

        try:
            tts = ChatterboxTTS(language=args.lang, voice=args.voice)
            wav_files, skipped = tts.synthesize_chunks(
                chunks=chunks,
                output_dir=chunks_dir,
                progress_callback=progress_fn,
                resume=args.resume,
            )
        except Exception as e:
            print(f"Error during synthesis: {e}", file=sys.stderr)
            return 1

    else:  # silero
        # Validate language
        silero_languages = silero_list_languages()
        if args.lang not in silero_languages:
            print(f"Error: Language '{args.lang}' not supported by Silero", file=sys.stderr)
            print(f"Available: {', '.join(silero_languages)}", file=sys.stderr)
            return 1

        # Set default voice
        voice = args.voice or SILERO_DEFAULT_VOICES[args.lang]

        # Validate voice
        available_voices = silero_list_voices(args.lang)
        if voice not in available_voices:
            print(f"Error: Voice '{voice}' not available for language '{args.lang}'", file=sys.stderr)
            print(f"Available voices: {', '.join(available_voices.keys())}", file=sys.stderr)
            return 1

        if not args.quiet:
            print(f"Synthesizing with Silero voice: {voice} ({args.lang})", file=sys.stderr)

        try:
            tts = SileroTTS(language=args.lang, sample_rate=args.sample_rate)
            wav_files, skipped = tts.synthesize_chunks(
                chunks=chunks,
                output_dir=chunks_dir,
                voice=voice,
                progress_callback=progress_fn,
                resume=args.resume,
            )
        except Exception as e:
            print(f"Error during synthesis: {e}", file=sys.stderr)
            return 1

    if not args.quiet:
        if skipped > 0:
            print(f"Skipped {skipped} existing chunks, generated {len(wav_files) - skipped} new", file=sys.stderr)
        else:
            print(f"Generated {len(wav_files)} WAV files in {chunks_dir}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
