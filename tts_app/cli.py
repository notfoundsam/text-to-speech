"""Command-line interface for Russian TTS."""

import argparse
import sys
from pathlib import Path

from .extract import extract_text
from .preprocess import preprocess
from .synthesize import SileroTTS, list_voices, DEFAULT_VOICE, DEFAULT_SAMPLE_RATE


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
        description="Convert PDF/EPUB to Russian speech using Silero TTS",
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
        "--voice",
        default=DEFAULT_VOICE,
        choices=list(list_voices().keys()),
        help=f"Voice to use (default: {DEFAULT_VOICE})",
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
        default=1000,
        help="Maximum characters per chunk (default: 1000)",
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
        print("Available voices:")
        for name, description in list_voices().items():
            print(f"  {name:10} - {description}")
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

    # Preprocess
    if not args.quiet:
        print("Preprocessing text...", file=sys.stderr)

    chunks = preprocess(text, max_chunk_chars=args.max_chunk_chars)

    if not chunks:
        print("Error: No text chunks to process", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Generated {len(chunks)} chunks", file=sys.stderr)

    # Synthesize
    if not args.quiet:
        print(f"Synthesizing with voice: {args.voice}", file=sys.stderr)

    tts = SileroTTS(sample_rate=args.sample_rate)

    progress_fn = None if args.quiet else print_progress

    try:
        wav_files, skipped = tts.synthesize_chunks(
            chunks=chunks,
            output_dir=chunks_dir,
            voice=args.voice,
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
