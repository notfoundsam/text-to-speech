#!/bin/bash
#
# Convert PDF/EPUB to speech audio
# Usage: ./scripts/convert.sh <input_file> [voice] [--lang <code>] [--engine <name>] [--clean] [--background]
#
set -e

# Colors for output (disabled when running in background)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Parse arguments
CLEAN_START=false
BACKGROUND=false
LANG="ru"
ENGINE="silero"
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_START=true
            shift
            ;;
        --background)
            BACKGROUND=true
            shift
            ;;
        --lang)
            LANG="$2"
            shift 2
            ;;
        --engine)
            ENGINE="$2"
            shift 2
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

INPUT_FILE="${POSITIONAL_ARGS[0]:-}"
VOICE="${POSITIONAL_ARGS[1]:-}"

# Set default voice based on engine and language
if [ -z "$VOICE" ]; then
    case $ENGINE in
        silero)
            case $LANG in
                ru) VOICE="aidar" ;;
                en) VOICE="en_0" ;;
                *) VOICE="aidar" ;;
            esac
            ;;
        piper)
            case $LANG in
                en) VOICE="en_US-lessac-medium" ;;
                ru) VOICE="ru_RU-ruslan-medium" ;;
                *) VOICE="en_US-lessac-medium" ;;
            esac
            ;;
        kokoro)
            case $LANG in
                en) VOICE="af_heart" ;;
                en_gb) VOICE="bf_alice" ;;
                es) VOICE="ef_dora" ;;
                fr) VOICE="ff_siwis" ;;
                ja) VOICE="jf_alpha" ;;
                zh) VOICE="zf_xiaobei" ;;
                *) VOICE="af_heart" ;;
            esac
            ;;
        chatterbox)
            VOICE=""
            ;;
    esac
fi

# Validate input
if [ -z "$INPUT_FILE" ]; then
    echo -e "${RED}Error: No input file specified${NC}"
    echo ""
    echo "Usage: $0 <input_file> [voice] [--lang <code>] [--engine <name>] [--clean] [--background]"
    echo ""
    echo "Arguments:"
    echo "  input_file   Path to PDF or EPUB file"
    echo "  voice        Voice name (optional, see below)"
    echo ""
    echo "Options:"
    echo "  --lang       Language: ru (default), en"
    echo "  --engine     TTS engine: silero (default), piper, kokoro, chatterbox, xtts"
    echo "  --clean      Start fresh, removing existing chunks"
    echo "  --background Run in background, logs saved to data/logs/"
    echo ""
    echo "Engines:"
    echo "  silero       Fast, good Russian, basic English"
    echo "  piper        Fast, good US English, lightweight"
    echo "  kokoro       Fast, multi-voice English (Apache 2.0, 82M params)"
    echo "  chatterbox   Voice cloning, English turbo + 23 languages (MIT)"
    echo "  xtts         Slow, excellent quality for all languages"
    echo ""
    echo "Silero voices:"
    echo "  Russian (ru): aidar (default), baya, kseniya, xenia, eugene"
    echo "  English (en): en_0 (default), en_1, en_2, en_3, en_4"
    echo ""
    echo "Piper voices:"
    echo "  English (en): en_US-lessac-medium (default), en_US-lessac-high, en_US-amy-medium"
    echo "  Russian (ru): ru_RU-ruslan-medium (default), ru_RU-irina-medium"
    echo ""
    echo "Kokoro voices:"
    echo "  English (en):    af_heart (default), am_adam, af_bella, am_michael, ..."
    echo "  British (en_gb): bf_alice (default), bm_daniel, bf_emma, ..."
    echo "  Also: es, fr, ja, zh, hi, it, pt"
    echo ""
    echo "Chatterbox voices:"
    echo "  Pass --voice <path_to_reference.wav> for voice cloning (optional)"
    echo "  Languages: en, ru, es, fr, de, it, pt, pl, tr, nl, cs, ar, zh, ja, ko, hu, ..."
    echo ""
    echo "Output: Audio file saved next to the input file (e.g., book.epub -> book.mp3)"
    echo ""
    echo "Example:"
    echo "  $0 /path/to/books/mybook.epub"
    echo "  $0 /path/to/books/mybook.epub --engine piper --lang en"
    echo "  $0 /path/to/books/english_book.epub --lang en --engine kokoro"
    echo "  $0 /path/to/books/english_book.epub --lang en --engine chatterbox"
    echo "  $0 /path/to/books/english_book.epub --lang en --engine xtts"
    echo "  $0 /path/to/books/mybook.epub --background"
    exit 1
fi

# Resolve full path of input file
if [[ "$INPUT_FILE" = /* ]]; then
    FULL_INPUT_PATH="$INPUT_FILE"
else
    FULL_INPUT_PATH="$(cd "$(dirname "$INPUT_FILE")" && pwd)/$(basename "$INPUT_FILE")"
fi

# Check if input file exists
if [ ! -f "$FULL_INPUT_PATH" ]; then
    echo -e "${RED}Error: File not found: $FULL_INPUT_PATH${NC}"
    exit 1
fi

# If --background flag is set, re-run this script in background
if [ "$BACKGROUND" = true ]; then
    mkdir -p "$PROJECT_DIR/data/logs"

    BASENAME=$(basename "$FULL_INPUT_PATH")
    FILENAME="${BASENAME%.*}"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    LOG_FILE="$PROJECT_DIR/data/logs/${FILENAME}_${TIMESTAMP}.log"

    # Build args without --background to avoid infinite loop
    ARGS=("$FULL_INPUT_PATH")
    if [ -n "$VOICE" ]; then
        ARGS+=("$VOICE")
    fi
    ARGS+=("--lang" "$LANG" "--engine" "$ENGINE")
    if [ "$CLEAN_START" = true ]; then
        ARGS+=("--clean")
    fi

    # Run in background with nohup
    nohup "$0" "${ARGS[@]}" > "$LOG_FILE" 2>&1 &
    PID=$!

    echo "Started background conversion (PID: $PID)"
    echo "  Input:    $FULL_INPUT_PATH"
    echo "  Language: $LANG"
    echo "  Engine:   $ENGINE"
    echo "  Log:      $LOG_FILE"
    echo ""
    echo "Monitor progress:"
    echo "  tail -f $LOG_FILE"
    echo ""
    echo "Check if running:"
    echo "  ps -p $PID"
    exit 0
fi

# Disable colors when output is not a terminal (e.g., when logging)
if [ ! -t 1 ]; then
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

# Extract directory, basename, and extension
INPUT_DIR=$(dirname "$FULL_INPUT_PATH")
BASENAME=$(basename "$FULL_INPUT_PATH")
FILENAME="${BASENAME%.*}"
OUTPUT_BASENAME="${FILENAME}.mp3"

# Use book-specific chunks directory to avoid conflicts between books
BOOK_HASH=$(echo -n "$BASENAME" | md5sum | cut -c1-8)
CHUNKS_DIR="data/chunks/$BOOK_HASH"
mkdir -p "$CHUNKS_DIR"

echo -e "${GREEN}Starting conversion...${NC}"
echo "  Input:    $FULL_INPUT_PATH"
echo "  Output:   $INPUT_DIR/$OUTPUT_BASENAME"
echo "  Language: $LANG"
echo "  Engine:   $ENGINE"
if [ -n "$VOICE" ]; then
    echo "  Voice:    $VOICE"
fi
echo "  Time:     $(date)"

# Copy input file to working directory
cp "$FULL_INPUT_PATH" "data/input/$BASENAME"

# Check for existing chunks
EXISTING_CHUNKS=$(ls -1 "$CHUNKS_DIR"/chunk_*.wav 2>/dev/null | wc -l | tr -d ' ')
if [ "$EXISTING_CHUNKS" -gt 0 ]; then
    if [ "$CLEAN_START" = true ]; then
        echo "  Mode:     Clean start (removing $EXISTING_CHUNKS existing chunks)"
        rm -f "$CHUNKS_DIR"/chunk_*.wav "$CHUNKS_DIR"/files.txt
    else
        echo "  Mode:     Resume (found $EXISTING_CHUNKS existing chunks)"
    fi
else
    echo "  Mode:     Fresh start"
fi
echo ""

# Build docker command
DOCKER_ARGS=(
    "/data/input/$BASENAME"
    "--chunks-dir" "/data/chunks/$BOOK_HASH"
    "--lang" "$LANG"
    "--engine" "$ENGINE"
    "--resume"
)

# Add voice if set
if [ -n "$VOICE" ]; then
    DOCKER_ARGS+=("--voice" "$VOICE")
fi

# Run TTS in Docker container
echo -e "${YELLOW}Running TTS synthesis in Docker...${NC}"
case $ENGINE in
    xtts)
        echo -e "${YELLOW}Note: XTTS is slower but produces higher quality audio${NC}"
        ;;
    piper)
        echo -e "${YELLOW}Note: Piper is fast with good English quality${NC}"
        ;;
    kokoro)
        echo -e "${YELLOW}Note: Kokoro is fast with excellent multi-voice English${NC}"
        ;;
    chatterbox)
        echo -e "${YELLOW}Note: Chatterbox supports voice cloning with reference audio${NC}"
        ;;
esac
docker compose run --rm tts "${DOCKER_ARGS[@]}"

# Check if chunks were created
CHUNK_COUNT=$(ls -1 "$CHUNKS_DIR"/chunk_*.wav 2>/dev/null | wc -l)
if [ "$CHUNK_COUNT" -eq 0 ]; then
    echo -e "${RED}Error: No audio chunks were generated${NC}"
    # Clean up copied input file
    rm -f "data/input/$BASENAME"
    exit 1
fi

echo ""
echo -e "${YELLOW}Merging $CHUNK_COUNT chunks with ffmpeg...${NC}"

# Create file list for ffmpeg concat
cd "$PROJECT_DIR/$CHUNKS_DIR"
ls -1 chunk_*.wav | sort -V | while read f; do
    echo "file '$f'"
done > files.txt

# Merge and encode to MP3
ffmpeg -y -f concat -safe 0 -i files.txt -codec:a libmp3lame -b:a 192k "$PROJECT_DIR/data/output/$OUTPUT_BASENAME" -loglevel warning

cd "$PROJECT_DIR"

# Copy output to original book location
cp "data/output/$OUTPUT_BASENAME" "$INPUT_DIR/$OUTPUT_BASENAME"

# Clean up working directory
rm -rf "$CHUNKS_DIR"
rm -f "data/input/$BASENAME"
rm -f "data/output/$OUTPUT_BASENAME"

# Report success
OUTPUT_SIZE=$(ls -lh "$INPUT_DIR/$OUTPUT_BASENAME" | awk '{print $5}')
echo ""
echo -e "${GREEN}Done!${NC}"
echo "  Output: $INPUT_DIR/$OUTPUT_BASENAME ($OUTPUT_SIZE)"
echo "  Time:   $(date)"
