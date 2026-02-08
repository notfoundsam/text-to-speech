# Text-to-Speech Converter

Convert PDF, EPUB, FB2, and TXT documents to natural-sounding speech. Supports Russian and English with multiple TTS engines.

## Features

- Six TTS engines:
  - **Silero** — Fast, excellent Russian (offline)
  - **Piper** — Fast, good US English (offline, recommended for English)
  - **Kokoro** — Fast, multi-voice English (offline, Apache 2.0, 82M params)
  - **Chatterbox** — Voice cloning, 23 languages (offline, MIT, 350-500M params)
  - **Edge-TTS** — Microsoft neural TTS, excellent Russian & English (cloud, free, no API key)
  - **XTTS** — Slow but highest quality (offline, experimental)
- Docker-based (clean, isolated environment)
- Supports PDF, EPUB, FB2, and TXT formats
- Resume interrupted conversions
- Background processing with logs
- Output saved next to input file

## Requirements

- Docker and Docker Compose
- ffmpeg (installed on host)

## Quick Start

```bash
# 1. Build the Docker image
docker compose build

# 2. Convert a book (output saved next to the input file)
./scripts/convert.sh /path/to/books/mybook.epub
```

## Usage

```bash
./scripts/convert.sh <input_file> [voice] [--lang <code>] [--engine <name>] [--clean] [--background] [--filter-meta]
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `input_file` | Path to PDF, EPUB, FB2, or TXT file | required |
| `voice` | Voice name (see below) | per engine/language |

### Options

| Option | Description |
|--------|-------------|
| `--lang <code>` | Language code (default: `ru`) |
| `--engine <name>` | TTS engine: `silero` (default), `piper`, `kokoro`, `chatterbox`, `edge`, or `xtts` |
| `--clean` | Start fresh, removing existing chunks |
| `--background` | Run in background, logs saved to `data/logs/` |
| `--filter-meta` | Filter out publishing boilerplate (ISBN, copyright, TOC, etc.) |

## TTS Engines

| Engine | Speed | English | Russian | RAM | Use Case |
|--------|-------|---------|---------|-----|----------|
| **Silero** | Fast (~10x RT) | Basic | Excellent | ~500MB | Russian books |
| **Piper** | Very fast (~20x RT) | Good (US) | Good | ~200MB | English books |
| **Kokoro** | Fast (~10x RT) | Excellent | — | ~500MB | Multi-voice English |
| **Chatterbox** | Medium (~2x RT) | Excellent | Good | ~2-4GB | Voice cloning |
| **Edge-TTS** | Very fast (cloud) | Excellent | Excellent | ~100MB | Cloud TTS (requires internet) |
| **XTTS** | Slow (~0.5x RT) | Excellent | Excellent | ~6-8GB | Best quality |

**Recommendations:**
- Russian books: Use Edge-TTS (`--engine edge`) or Silero (default, offline)
- English books: Use Kokoro (`--engine kokoro --lang en`) or Piper (`--engine piper --lang en`)
- Voice cloning: Use Chatterbox (`--engine chatterbox --lang en`)
- Best quality (slow): Use XTTS (`--engine xtts`)
- Cloud with no setup: Use Edge-TTS (`--engine edge`, requires internet, free)

## Available Voices

### Silero Voices

**Russian (`--lang ru`):**

| Voice | Gender | Description |
|-------|--------|-------------|
| aidar | Male | Deep, calm (default) |
| eugene | Male | Standard, professional |
| baya | Female | Warm, expressive |
| kseniya | Female | Young, energetic |
| xenia | Female | Clear, neutral |

**English (`--lang en`):**

| Voice | Description |
|-------|-------------|
| en_0 | Male, neutral (default) |
| en_1 | Male, calm |
| en_2 | Female, clear |
| en_3 | Female, expressive |
| en_4 | Male, deep |

### Piper Voices

**English (`--lang en`):**

| Voice | Description |
|-------|-------------|
| en_US-ryan-medium | US male, medium quality (default) |
| en_US-ryan-high | US male, high quality |
| en_US-lessac-medium | US female, medium quality |
| en_US-lessac-high | US female, high quality |
| en_US-amy-medium | US female, medium quality |
| en_GB-alan-medium | UK male, medium quality |

**Russian (`--lang ru`):**

| Voice | Description |
|-------|-------------|
| ru_RU-ruslan-medium | Russian male (default) |
| ru_RU-irina-medium | Russian female |

### Kokoro Voices

**English (`--lang en`):**

| Voice | Description |
|-------|-------------|
| am_adam | American male, deep (default) |
| af_heart | American female, warm |
| af_bella | American female, soft |
| am_michael | American male, clear |
| af_nova | American female, energetic |
| am_onyx | American male, rich |

**British English (`--lang en_gb`):**

| Voice | Description |
|-------|-------------|
| bf_alice | British female, clear (default) |
| bm_daniel | British male, standard |

Also supports: es, fr, ja, zh, hi, it, pt. Use `--list-voices` to see all.

### Edge-TTS Voices

Microsoft neural TTS (cloud, free, no API key, requires internet).

**Russian (`--lang ru`):**

| Voice | Description |
|-------|-------------|
| ru-RU-DmitryNeural | Male, deep (default) |
| ru-RU-SvetlanaNeural | Female, clear |

**English (`--lang en`):**

| Voice | Description |
|-------|-------------|
| en-US-GuyNeural | Male, standard (default) |
| en-US-AriaNeural | Female, expressive |
| en-US-JennyNeural | Female, warm |
| en-US-ChristopherNeural | Male, calm |
| en-US-EricNeural | Male, deep |
| en-US-MichelleNeural | Female, clear |
| en-US-RogerNeural | Male, mature |
| en-US-SteffanNeural | Male, professional |

**British English (`--lang en_gb`):**

| Voice | Description |
|-------|-------------|
| en-GB-RyanNeural | Male, standard (default) |
| en-GB-SoniaNeural | Female, warm |
| en-GB-ThomasNeural | Male, calm |
| en-GB-LibbyNeural | Female, clear |

### Chatterbox

Chatterbox supports voice cloning via a reference WAV file. Pass `--voice <path>` to clone a voice, or omit for default.

Supports 23 languages: en, ru, es, fr, de, it, pt, pl, tr, nl, cs, ar, zh, ja, ko, hu, sv, da, fi, no, el, ro, uk.

- English uses the Turbo model (350M, fastest)
- Other languages use the Multilingual model (500M)

### XTTS

XTTS uses a built-in voice (no selection needed). Supports 16+ languages including: en, ru, es, fr, de, it, pt, pl, tr, nl, cs, ar, zh, ja, ko, hu.

**Note:** XTTS uses Coqui's non-commercial license (CPML).

## Examples

```bash
# Russian book with Silero (default)
./scripts/convert.sh /path/to/books/russian_book.epub

# Russian with female voice
./scripts/convert.sh /path/to/books/russian_book.epub xenia

# English book with Piper (recommended for English)
./scripts/convert.sh /path/to/books/english_book.epub --lang en --engine piper

# English with high quality Piper voice
./scripts/convert.sh /path/to/books/english_book.epub en_US-ryan-high --lang en --engine piper

# English with Kokoro (fast, multi-voice)
./scripts/convert.sh /path/to/books/english_book.epub --lang en --engine kokoro

# English with Kokoro, specific voice
./scripts/convert.sh /path/to/books/english_book.epub am_adam --lang en --engine kokoro

# Russian with Edge-TTS (cloud, excellent quality)
./scripts/convert.sh /path/to/books/russian_book.epub --engine edge

# English with Edge-TTS
./scripts/convert.sh /path/to/books/english_book.epub --lang en --engine edge

# English with Chatterbox
./scripts/convert.sh /path/to/books/english_book.epub --lang en --engine chatterbox

# English with XTTS (best quality, slow)
./scripts/convert.sh /path/to/books/english_book.epub --lang en --engine xtts

# Run in background (recommended for long books)
./scripts/convert.sh /path/to/books/long_book.epub --background

# Filter out publishing boilerplate (ISBN, copyright, TOC, etc.)
./scripts/convert.sh /path/to/books/book.epub --engine edge --filter-meta

# Force restart (discard previous progress)
./scripts/convert.sh /path/to/books/book.epub --clean
```

## Background Processing

For long books, use `--background`:

```bash
./scripts/convert.sh /path/to/books/long_book.epub --engine piper --lang en --background
```

Output:
```
Started background conversion (PID: 12345)
  Input:    /path/to/books/long_book.epub
  Language: en
  Engine:   piper
  Log:      /home/user/text-to-speech/data/logs/long_book_20240115_143022.log

Monitor progress:
  tail -f /home/user/text-to-speech/data/logs/long_book_20240115_143022.log

Check if running:
  ps -p 12345
```

## Resume Interrupted Conversions

If a conversion is interrupted, run the same command again. The script automatically resumes from where it left off, skipping already-generated chunks.

## Project Structure

```
text-to-speech/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-base.txt
├── tts_app/
│   ├── cli.py          # CLI interface
│   ├── extract.py      # PDF/EPUB/FB2/TXT extraction
│   ├── preprocess.py   # Text cleaning
│   ├── synthesize.py      # Silero TTS wrapper
│   ├── piper_tts.py       # Piper TTS wrapper
│   ├── kokoro_tts.py      # Kokoro TTS wrapper
│   ├── chatterbox_tts.py     # Chatterbox TTS wrapper
│   ├── edge_tts_wrapper.py   # Edge-TTS wrapper (cloud)
│   └── xtts.py               # XTTS wrapper
├── scripts/
│   └── convert.sh      # Main conversion script
├── data/
│   ├── input/          # Temporary input files
│   ├── chunks/         # Temporary audio chunks
│   ├── output/         # Temporary output files
│   ├── samples/        # XTTS reference audio
│   └── logs/           # Background job logs
└── models/
    ├── torch/          # Silero models cache
    ├── piper/          # Piper models cache (~60MB per voice)
    ├── huggingface/    # Kokoro & Chatterbox models cache
    └── tts/            # XTTS models cache (~1.9GB)
```

## Remote Usage

From your local machine:

```bash
# One-liner: upload, convert, download
scp book.epub server:~/books/ && \
ssh server "cd ~/text-to-speech && ./scripts/convert.sh ~/books/book.epub --engine piper --lang en" && \
scp server:~/books/book.mp3 .
```

## Model Downloads

| Engine | Model Size | Downloaded on first use |
|--------|------------|------------------------|
| Silero (ru) | ~100MB | Yes |
| Silero (en) | ~100MB | Yes |
| Piper (per voice) | ~60MB | Yes |
| Kokoro | ~200MB | Yes |
| Chatterbox Turbo | ~350MB | Yes |
| Chatterbox Multilingual | ~500MB | Yes |
| Edge-TTS | None (cloud) | N/A |
| XTTS | ~1.9GB | Yes |

Models are cached in `models/` directory and persist across container restarts.

## Notes

- Use `--filter-meta` to skip publishing boilerplate (ISBN, copyright, TOC, URLs) for cleaner audio
- Large books are automatically split into chunks
- Punctuation in source text improves speech intonation
- Output is MP3 format (192kbps) saved next to input file
- For English content, Piper is recommended (fast + good quality)
- XTTS is significantly slower but produces the most natural speech
