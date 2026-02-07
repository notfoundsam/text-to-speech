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
    DEFAULT_VOICES,
    DEFAULT_SAMPLE_RATE,
)

# Maximum chunk size per language/engine
MAX_CHUNK_CHARS = {
    "silero": {"ru": 1000, "en": 250},
    "xtts": {"default": 400},  # XTTS works best with shorter chunks
}

ENGINES = ["silero", "xtts"]


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
        help="TTS engine: silero (fast) or xtts (high quality). Default: silero",
    )

    parser.add_argument(
        "--lang",
        default=DEFAULT_LANGUAGE,
        help=f"Language code (default: {DEFAULT_LANGUAGE})",
    )

    parser.add_argument(
        "--voice",
        default=None,
        help="Voice to use (Silero only). Use --list-voices to see options.",
    )

    parser.add_argument(
        "--sample-rate",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        choices=[24000, 48000],
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
        help="List available voices (Silero only) and exit",
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
        print("Silero voices:")
        all_voices = silero_list_voices()
        for lang, voices in all_voices.items():
            default = DEFAULT_VOICES[lang]
            print(f"\n  {lang.upper()}:")
            for name, description in voices.items():
                marker = " (default)" if name == default else ""
                print(f"    {name:10} - {description}{marker}")
        print("\nXTTS: Uses built-in voice (no selection needed)")
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
    elif args.engine == "xtts":
        max_chars = MAX_CHUNK_CHARS["xtts"]["default"]
    else:
        max_chars = MAX_CHUNK_CHARS["silero"].get(args.lang, 500)

    # Preprocess
    if not args.quiet:
        print("Preprocessing text...", file=sys.stderr)

    chunks = preprocess(text, max_chunk_chars=max_chars)

    if not chunks:
        print("Error: No text chunks to process", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Generated {len(chunks)} chunks", file=sys.stderr)

    # Initialize TTS engine
    if args.engine == "xtts":
        from .xtts import XttsTTS, list_languages as xtts_list_languages

        # Validate language for XTTS
        xtts_languages = xtts_list_languages()
        if args.lang not in xtts_languages:
            print(f"Error: Language '{args.lang}' not supported by XTTS", file=sys.stderr)
            print(f"Available: {', '.join(xtts_languages)}", file=sys.stderr)
            return 1

        if not args.quiet:
            print(f"Synthesizing with XTTS ({args.lang})", file=sys.stderr)
            print("Note: XTTS is slower but higher quality", file=sys.stderr)

        tts = XttsTTS(language=args.lang)
        progress_fn = None if args.quiet else print_progress

        try:
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
        # Validate language for Silero
        silero_languages = silero_list_languages()
        if args.lang not in silero_languages:
            print(f"Error: Language '{args.lang}' not supported by Silero", file=sys.stderr)
            print(f"Available: {', '.join(silero_languages)}", file=sys.stderr)
            return 1

        # Set default voice for language if not specified
        voice = args.voice
        if voice is None:
            voice = DEFAULT_VOICES[args.lang]

        # Validate voice for selected language
        available_voices = silero_list_voices(args.lang)
        if voice not in available_voices:
            print(f"Error: Voice '{voice}' not available for language '{args.lang}'", file=sys.stderr)
            print(f"Available voices: {', '.join(available_voices.keys())}", file=sys.stderr)
            return 1

        if not args.quiet:
            print(f"Synthesizing with Silero voice: {voice} ({args.lang})", file=sys.stderr)

        tts = SileroTTS(language=args.lang, sample_rate=args.sample_rate)
        progress_fn = None if args.quiet else print_progress

        try:
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
