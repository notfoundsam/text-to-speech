"""Text preprocessing and chunking for TTS."""

import re


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace while preserving paragraph structure.

    Args:
        text: Raw text input.

    Returns:
        Text with normalized whitespace.
    """
    # Replace multiple spaces/tabs with single space
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace 3+ newlines with double newline (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace from lines
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def remove_page_artifacts(text: str) -> str:
    """Remove common PDF artifacts like page numbers and headers.

    Args:
        text: Text with potential artifacts.

    Returns:
        Cleaned text.
    """
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        stripped = line.strip()

        # Skip standalone page numbers
        if re.match(r"^-?\s*\d+\s*-?$", stripped):
            continue

        # Skip very short lines that look like headers/footers
        if len(stripped) < 3 and not stripped.isalpha():
            continue

        cleaned.append(line)

    return "\n".join(cleaned)


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences, respecting Russian punctuation.

    Args:
        text: Input text.

    Returns:
        List of sentences.
    """
    # Split on sentence-ending punctuation followed by space or newline
    # Handles: . ! ? ... and combinations like ?! or !?
    pattern = r"(?<=[.!?])\s+(?=[А-ЯA-Z\"])"

    sentences = re.split(pattern, text)

    # Clean up and filter empty
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def split_into_chunks(text: str, max_chars: int = 1000) -> list[str]:
    """Split text into chunks suitable for TTS processing.

    Attempts to split at sentence boundaries when possible.

    Args:
        text: Input text.
        max_chars: Maximum characters per chunk.

    Returns:
        List of text chunks.
    """
    sentences = split_into_sentences(text)

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)

        # If single sentence exceeds max, split it by punctuation/words
        if sentence_length > max_chars:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0

            # Split long sentence at clause boundaries or word boundaries
            sub_chunks = _split_long_sentence(sentence, max_chars)
            chunks.extend(sub_chunks)
            continue

        # Check if adding this sentence would exceed limit
        new_length = current_length + sentence_length + (1 if current_chunk else 0)

        if new_length > max_chars:
            # Save current chunk and start new one
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length = new_length

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def _split_long_sentence(sentence: str, max_chars: int) -> list[str]:
    """Split a long sentence into smaller parts.

    Args:
        sentence: Long sentence to split.
        max_chars: Maximum characters per part.

    Returns:
        List of sentence parts.
    """
    # Try splitting at clause boundaries first
    clause_pattern = r"(?<=[,;:\-\u2014])\s+"
    parts = re.split(clause_pattern, sentence)

    chunks = []
    current = []
    current_length = 0

    for part in parts:
        part_length = len(part)

        if part_length > max_chars:
            # Last resort: split by words
            if current:
                chunks.append(" ".join(current))
                current = []
                current_length = 0

            words = part.split()
            word_chunk = []
            word_length = 0

            for word in words:
                if word_length + len(word) + 1 > max_chars:
                    if word_chunk:
                        chunks.append(" ".join(word_chunk))
                    word_chunk = [word]
                    word_length = len(word)
                else:
                    word_chunk.append(word)
                    word_length += len(word) + 1

            if word_chunk:
                chunks.append(" ".join(word_chunk))

            continue

        new_length = current_length + part_length + (1 if current else 0)

        if new_length > max_chars:
            if current:
                chunks.append(" ".join(current))
            current = [part]
            current_length = part_length
        else:
            current.append(part)
            current_length = new_length

    if current:
        chunks.append(" ".join(current))

    return chunks


def preprocess(text: str, max_chunk_chars: int = 1000) -> list[str]:
    """Full preprocessing pipeline: clean and chunk text.

    Args:
        text: Raw extracted text.
        max_chunk_chars: Maximum characters per chunk.

    Returns:
        List of cleaned text chunks ready for TTS.
    """
    text = normalize_whitespace(text)
    text = remove_page_artifacts(text)

    # Final cleanup of excessive whitespace that might remain
    text = re.sub(r"\n{2,}", "\n\n", text)

    chunks = split_into_chunks(text, max_chars=max_chunk_chars)

    return chunks
