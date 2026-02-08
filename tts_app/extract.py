"""Text extraction from PDF and EPUB files."""

from pathlib import Path


def extract_from_pdf(path: str | Path) -> str:
    """Extract text from a PDF file.

    Args:
        path: Path to the PDF file.

    Returns:
        Extracted text content.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If no text could be extracted.
    """
    import fitz  # pymupdf

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    with fitz.open(path) as doc:
        pages = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages.append(text)

    if not pages:
        raise ValueError(f"No text extracted from PDF: {path}. It may be a scanned document.")

    return "\n".join(pages)


def extract_from_epub(path: str | Path, filter_meta: bool = False) -> str:
    """Extract text from an EPUB file.

    Args:
        path: Path to the EPUB file.
        filter_meta: If True, skip navigation/cover pages (non-chapter items).

    Returns:
        Extracted text content.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If no text could be extracted.
    """
    from ebooklib import epub, ITEM_DOCUMENT
    from bs4 import BeautifulSoup

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"EPUB file not found: {path}")

    book = epub.read_epub(str(path))
    parts = []

    for item in book.get_items():
        if item.get_type() == ITEM_DOCUMENT:
            if filter_meta and not item.is_chapter():
                continue
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text()
            if text.strip():
                parts.append(text)

    if not parts:
        raise ValueError(f"No text extracted from EPUB: {path}")

    return "\n".join(parts)


_TOC_KEYWORDS = {
    "содержание", "оглавление",
    "contents", "table of contents",
}


def _is_toc_section(section) -> bool:
    """Check if an FB2 section looks like a table of contents."""
    title = section.find("title")
    if not title:
        return False
    title_text = title.get_text(strip=True).lower()
    return title_text in _TOC_KEYWORDS


def extract_from_fb2(path: str | Path, filter_meta: bool = False) -> str:
    """Extract text from an FB2 file.

    Args:
        path: Path to the FB2 file.
        filter_meta: If True, skip TOC-like sections.

    Returns:
        Extracted text content.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If no text could be extracted.
    """
    from bs4 import BeautifulSoup

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"FB2 file not found: {path}")

    with open(path, "rb") as f:
        soup = BeautifulSoup(f, "lxml-xml")

    body = soup.find("body")
    if not body:
        raise ValueError(f"No <body> found in FB2: {path}")

    parts = []
    for section in body.find_all("section"):
        if filter_meta and _is_toc_section(section):
            continue
        text = section.get_text(separator="\n")
        if text.strip():
            parts.append(text)

    if not parts:
        # Fallback: get all text from body
        text = body.get_text(separator="\n")
        if text.strip():
            parts.append(text)

    if not parts:
        raise ValueError(f"No text extracted from FB2: {path}")

    return "\n".join(parts)


def extract_text(path: str | Path, filter_meta: bool = False) -> str:
    """Extract text from a PDF or EPUB file based on extension.

    Args:
        path: Path to the input file.
        filter_meta: If True, apply structural filtering to skip boilerplate.

    Returns:
        Extracted text content.

    Raises:
        ValueError: If the file format is not supported.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return extract_from_pdf(path)
    elif suffix == ".epub":
        return extract_from_epub(path, filter_meta=filter_meta)
    elif suffix == ".fb2":
        return extract_from_fb2(path, filter_meta=filter_meta)
    elif suffix == ".txt":
        if not path.exists():
            raise FileNotFoundError(f"Text file not found: {path}")
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            raise ValueError(f"No text in file: {path}")
        return text
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use PDF, EPUB, FB2, or TXT.")
