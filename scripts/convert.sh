#!/bin/bash
#
# Convert PDF/EPUB to Russian speech audio
# Usage: ./scripts/convert.sh <input_file> [output_file] [voice]
#
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Parse arguments
INPUT_FILE="$1"
OUTPUT_FILE="${2:-}"
VOICE="${3:-xenia}"

# Validate input
if [ -z "$INPUT_FILE" ]; then
    echo -e "${RED}Error: No input file specified${NC}"
    echo ""
    echo "Usage: $0 <input_file> [output_file] [voice]"
    echo ""
    echo "Arguments:"
    echo "  input_file   PDF or EPUB file (place in data/input/)"
    echo "  output_file  Output WAV filename (default: <input>.wav)"
    echo "  voice        Voice name: xenia, aidar, baya, kseniya, eugene (default: xenia)"
    echo ""
    echo "Example:"
    echo "  $0 book.pdf book.wav xenia"
    exit 1
fi

# Get just the filename if a path was provided
BASENAME=$(basename "$INPUT_FILE")
INPUT_PATH="data/input/$BASENAME"

# Check if input file exists
if [ ! -f "$INPUT_PATH" ]; then
    echo -e "${RED}Error: File not found: $INPUT_PATH${NC}"
    echo "Place your PDF/EPUB file in the data/input/ directory first."
    exit 1
fi

# Determine output filename
if [ -z "$OUTPUT_FILE" ]; then
    # Remove extension and add .wav
    OUTPUT_FILE="${BASENAME%.*}.wav"
fi
OUTPUT_BASENAME=$(basename "$OUTPUT_FILE")

echo -e "${GREEN}Starting conversion...${NC}"
echo "  Input:  $BASENAME"
echo "  Output: $OUTPUT_BASENAME"
echo "  Voice:  $VOICE"
echo ""

# Clean up any previous chunks
rm -f data/chunks/chunk_*.wav data/chunks/files.txt

# Run TTS in Docker container
echo -e "${YELLOW}Running TTS synthesis in Docker...${NC}"
docker compose run --rm tts \
    "/data/input/$BASENAME" \
    --chunks-dir /data/chunks \
    --voice "$VOICE"

# Check if chunks were created
CHUNK_COUNT=$(ls -1 data/chunks/chunk_*.wav 2>/dev/null | wc -l)
if [ "$CHUNK_COUNT" -eq 0 ]; then
    echo -e "${RED}Error: No audio chunks were generated${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Merging $CHUNK_COUNT chunks with ffmpeg...${NC}"

# Create file list for ffmpeg concat
cd data/chunks
ls -1 chunk_*.wav | sort -V | while read f; do
    echo "file '$f'"
done > files.txt

# Merge with ffmpeg
ffmpeg -y -f concat -safe 0 -i files.txt -c copy "../output/$OUTPUT_BASENAME" -loglevel warning

# Clean up chunks
rm -f chunk_*.wav files.txt

cd "$PROJECT_DIR"

# Report success
OUTPUT_SIZE=$(ls -lh "data/output/$OUTPUT_BASENAME" | awk '{print $5}')
echo ""
echo -e "${GREEN}Done!${NC}"
echo "  Output: data/output/$OUTPUT_BASENAME ($OUTPUT_SIZE)"
