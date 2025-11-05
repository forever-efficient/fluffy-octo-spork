"""
Legal document chunker for Colorado Revised Statutes (and similar).

Parses hierarchical structure (TITLE/ARTICLE/PART), detects sections and
subsections, and produces semantically meaningful chunks suitable for
embedding and storage in ChromaDB.

Chunking constraints:
- Minimum size: 50 tokens (≈ 200 characters)
- Maximum size: 800 tokens (≈ 3,200 characters)
- Token estimation: ~4 characters per token

Output: LegalChunk dataclass with helpful metadata and helper methods to
integrate with ChromaDB.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple, Dict, Any


# -----------------------------
# Regular expressions
# -----------------------------
TITLE_RE = re.compile(r"^\s*TITLE\s+(\d+)[\s\-:]*", re.IGNORECASE)
ARTICLE_RE = re.compile(r"^\s*ARTICLE\s+(\d+)[\s\-:]*", re.IGNORECASE)
PART_RE = re.compile(r"^\s*PART\s+(\d+)[\s\-:]*", re.IGNORECASE)

# Section number with optional decimal extension, e.g., 17-1-101 or 17-1-101.5
SECTION_START_RE = re.compile(r"^(?P<num>\d+-\d+-\d+(?:\.\d+)?)[\.]?\s*(?P<title>.*)$")

# Subsection markers: (1), (2) ...; (a), (b) ...; (i), (ii), (iii) ...
SUBSECTION_RE = re.compile(r"(?P<mark>\((?:\d+|[a-z]|[ivx]+)\))", re.IGNORECASE)

# Editor's note lines to skip when collecting content
EDITORS_NOTE_RE = re.compile(r"^\s*Editor\'s note:|^\s*Editors note:|^\s*Editor’s note:", re.IGNORECASE)


# -----------------------------
# Utilities
# -----------------------------
MIN_TOKENS = 50
MAX_TOKENS = 800
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Rough token estimate assuming ~4 characters per token."""
    return max(1, (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN)


def trim_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def split_on_sentences(text: str) -> List[str]:
    """Lightweight sentence split using punctuation. No external deps.

    This is a heuristic; legal text often has long sentences. We'll use it
    only as a fallback to respect MAX_TOKENS when needed.
    """
    # Keep punctuation attached; split on period, question, exclamation followed by space/cap
    # Also handle semicolons as soft sentence boundaries in statutes
    parts: List[str] = []
    start = 0
    for m in re.finditer(r"([\.;!?])(\s+)", text):
        end = m.end()
        parts.append(text[start:end].strip())
        start = end
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return [p for p in parts if p]


@dataclass
class LegalChunk:
    """A semantic chunk of legal text with hierarchy and citation metadata."""

    content: str
    section_number: str
    section_title: str
    subsection: Optional[str]
    hierarchy: List[str]
    full_citation: str
    token_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dict suitable for JSON serialization."""
        return asdict(self)

    def get_searchable_text(self) -> str:
        """Return a text string optimized for embedding/RAG retrieval."""
        hierarchy_str = " | ".join(self.hierarchy)
        citation = f"{self.section_number}. {self.section_title}".strip()
        preamble = f"{hierarchy_str} || {citation}"
        return trim_whitespace(f"{preamble}\n{self.content}")


class LegalChunkerError(Exception):
    """Domain-specific error for parsing issues."""


class LegalChunker:
    """Parser and chunker for Colorado Revised Statutes-like documents."""

    def __init__(self, min_tokens: int = MIN_TOKENS, max_tokens: int = MAX_TOKENS):
        if min_tokens <= 0 or max_tokens <= 0 or min_tokens >= max_tokens:
            raise ValueError("Invalid token bounds for chunker")
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens

    # -----------------------------
    # Public API
    # -----------------------------
    def parse_document(self, text: str) -> List[LegalChunk]:
        """Parse entire document text into a list of LegalChunk.

        Steps:
        - Track TITLE/ARTICLE/PART headers as hierarchy context
        - Split by section numbers (e.g., 17-1-101.)
        - Within each section, split by subsections and sub-subsections
        - Enforce token size constraints
        """
        if not isinstance(text, str):
            raise LegalChunkerError("Input text must be a string")

        lines = text.splitlines()
        # Track current hierarchy labels
        current_title: Optional[str] = None
        current_article: Optional[str] = None
        current_part: Optional[str] = None

        # Accumulate lines by section blocks keyed by section_number
        sections: List[Tuple[str, str, List[str]]] = []  # (section_number, section_title, lines)

        buffer_lines: List[str] = []
        buffer_section_number: Optional[str] = None
        buffer_section_title: str = ""

        def flush_section():
            nonlocal buffer_lines, buffer_section_number, buffer_section_title
            if buffer_section_number is not None and buffer_lines:
                sections.append((buffer_section_number, buffer_section_title, buffer_lines))
            buffer_lines = []
            buffer_section_number = None
            buffer_section_title = ""

        for raw_line in lines:
            line = raw_line.rstrip()
            if EDITORS_NOTE_RE.search(line):
                # Skip editor's notes entirely
                continue

            # Hierarchy detection
            tmatch = TITLE_RE.match(line)
            if tmatch:
                current_title = f"TITLE {tmatch.group(1)}"
                # On new title, flush any open section
                flush_section()
                continue

            amatch = ARTICLE_RE.match(line)
            if amatch:
                current_article = f"ARTICLE {amatch.group(1)}"
                flush_section()
                continue

            pmatch = PART_RE.match(line)
            if pmatch:
                current_part = f"PART {pmatch.group(1)}"
                flush_section()
                continue

            # Section start
            smatch = SECTION_START_RE.match(line)
            if smatch:
                # Starting a new section: flush previous
                flush_section()
                buffer_section_number = smatch.group("num").strip()
                buffer_section_title = smatch.group("title").strip()
                continue

            # Regular content line for current section
            if buffer_section_number is not None:
                buffer_lines.append(line)
            else:
                # Lines before first section can be ignored or added to context; ignore.
                continue

        # Flush last section
        flush_section()

        # Now chunk per section with current hierarchy snapshot at the time of section.
        # Note: hierarchy changes affect subsequent sections, which we reflected via flush.
        chunks: List[LegalChunk] = []

        # We need to keep the hierarchy that applied when the section was read. Since we
        # rebuilt hierarchy on headers and flushed sections then, the current_hierarchy now
        # reflects the last header state; but we didn't store per-section hierarchy. We'll
        # approximate by re-parsing hierarchy from the nearest headers that appeared before
        # the section. To avoid complexity, we pass through the current hierarchy tracked at
        # parse time by capturing snapshots into the sections list. Simplify: carry a parallel
        # list mapping of hierarchies by inserting markers into sections during the loop.
        # For simplicity and robustness, re-scan lines for hierarchy within each section's
        # surrounding context isn't available now; instead, reuse the best-known hierarchy snapshot
        # when the section began. We'll track it during the first pass.
        #
        # Revised approach: Patch the first pass to also store hierarchy snapshot alongside section.
        # To avoid rewriting the loop, reconstruct hierarchy = [TITLE?, ARTICLE?, PART?] that's last
        # set at time of section start. We'll do that by a secondary pass where we re-walk the text
        # updating hierarchy and assigning to sections in order.

        # Secondary pass to attach hierarchy snapshots to each section in order of appearance
        section_hierarchies: List[List[str]] = []
        current_title = None
        current_article = None
        current_part = None
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            if TITLE_RE.match(line):
                current_title = f"TITLE {TITLE_RE.match(line).group(1)}"
                current_article = None
                current_part = None
            elif ARTICLE_RE.match(line):
                current_article = f"ARTICLE {ARTICLE_RE.match(line).group(1)}"
                current_part = None
            elif PART_RE.match(line):
                current_part = f"PART {PART_RE.match(line).group(1)}"
            elif SECTION_START_RE.match(line):
                # Start of a section, snapshot current hierarchy
                snapshot = [h for h in [current_title, current_article, current_part] if h]
                section_hierarchies.append(snapshot)

        # If counts mismatch, pad with last known hierarchy
        if section_hierarchies and len(section_hierarchies) != len(sections):
            # Pad or truncate to match
            if len(section_hierarchies) < len(sections):
                last = section_hierarchies[-1]
                while len(section_hierarchies) < len(sections):
                    section_hierarchies.append(last)
            else:
                section_hierarchies = section_hierarchies[: len(sections)]
        elif not section_hierarchies and sections:
            section_hierarchies = [[] for _ in sections]

        for idx, (sec_num, sec_title, sec_lines) in enumerate(sections):
            hierarchy = section_hierarchies[idx] if idx < len(section_hierarchies) else []
            section_text = trim_whitespace(" ".join(ln for ln in sec_lines if ln))
            if not section_text:
                continue

            # Split into subsections if present
            subsections = self._split_by_subsections(section_text)
            if not subsections:
                # No subsection markers; treat as one body chunk and enforce bounds
                chunks.extend(self._chunk_text_body(sec_num, sec_title, None, hierarchy, section_text))
            else:
                for sub_mark, sub_body in subsections:
                    # If too large, split by sub-subsections (a)(b)(i)...
                    if estimate_tokens(sub_body) > self.max_tokens:
                        subsubs = self._split_by_subsections(sub_body)
                        if subsubs:
                            for subsub_mark, subsub_body in subsubs:
                                composite_mark = f"{sub_mark}{subsub_mark}"
                                chunks.extend(
                                    self._chunk_text_body(sec_num, sec_title, composite_mark, hierarchy, subsub_body)
                                )
                        else:
                            # Fallback to sentence-based splitting
                            chunks.extend(
                                self._chunk_text_body(sec_num, sec_title, sub_mark, hierarchy, sub_body)
                            )
                    else:
                        chunks.extend(
                            self._chunk_text_body(sec_num, sec_title, sub_mark, hierarchy, sub_body)
                        )

        return chunks

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def _split_by_subsections(self, text: str) -> List[Tuple[str, str]]:
        """Split text by subsection markers (1)/(a)/(i) ... preserving markers.

        Returns list of (marker, body) pairs. If fewer than 2 markers found,
        returns empty list to signal "no meaningful subsections".
        """
        matches = list(SUBSECTION_RE.finditer(text))
        if len(matches) < 2:
            return []
        parts: List[Tuple[str, str]] = []
        for i, m in enumerate(matches):
            start = m.start()
            mark = m.group("mark")
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end]
            # Remove the mark from body but keep as separate field
            body_wo_mark = trim_whitespace(body[len(mark) :])
            parts.append((mark, body_wo_mark))
        return parts

    def _chunk_text_body(
        self,
        section_number: str,
        section_title: str,
        subsection: Optional[str],
        hierarchy: List[str],
        body: str,
    ) -> List[LegalChunk]:
        """Enforce token bounds on a body of text and return chunks."""
        text = trim_whitespace(body)
        if not text:
            return []

        chunks: List[LegalChunk] = []

        # If within bounds, emit directly (but also ensure minimum—if too small, try to merge later).
        tokens = estimate_tokens(text)
        if tokens <= self.max_tokens:
            if tokens < self.min_tokens:
                # For very short items, we still emit a chunk to avoid data loss.
                pass
            chunks.append(self._make_chunk(text, section_number, section_title, subsection, hierarchy))
            return chunks

        # Too large: split on sentences to fit <= max_tokens
        sentences = split_on_sentences(text)
        if not sentences:
            # Degenerate case: hard split by characters
            chunks.extend(self._hard_split(text, section_number, section_title, subsection, hierarchy))
            return chunks

        current: List[str] = []
        current_len = 0
        for sent in sentences:
            s = trim_whitespace(sent)
            if not s:
                continue
            tks = estimate_tokens(s)
            if current and current_len + tks > self.max_tokens:
                # flush
                piece = trim_whitespace(" ".join(current))
                if piece:
                    chunks.append(self._make_chunk(piece, section_number, section_title, subsection, hierarchy))
                current = [s]
                current_len = tks
            else:
                current.append(s)
                current_len += tks
        if current:
            piece = trim_whitespace(" ".join(current))
            if piece:
                chunks.append(self._make_chunk(piece, section_number, section_title, subsection, hierarchy))

        return chunks

    def _hard_split(
        self,
        text: str,
        section_number: str,
        section_title: str,
        subsection: Optional[str],
        hierarchy: List[str],
    ) -> List[LegalChunk]:
        """Hard split text by character count into <= max size pieces."""
        max_chars = self.max_tokens * CHARS_PER_TOKEN
        out: List[LegalChunk] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + max_chars)
            piece = trim_whitespace(text[start:end])
            if piece:
                out.append(self._make_chunk(piece, section_number, section_title, subsection, hierarchy))
            start = end
        return out

    def _make_chunk(
        self,
        content: str,
        section_number: str,
        section_title: str,
        subsection: Optional[str],
        hierarchy: List[str],
    ) -> LegalChunk:
        token_count = estimate_tokens(content)
        citation = f"{section_number}. {section_title}".strip()
        return LegalChunk(
            content=content,
            section_number=section_number,
            section_title=section_title,
            subsection=subsection,
            hierarchy=hierarchy,
            full_citation=citation,
            token_count=token_count,
        )

    # -----------------------------
    # ChromaDB preparation
    # -----------------------------
    @staticmethod
    def prepare_for_chromadb(chunks: List[LegalChunk]) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """Prepare documents, metadatas, and ids for ChromaDB ingestion.

        - documents: searchable text strings
        - metadatas: dicts with rich metadata
        - ids: unique identifiers per chunk
        """
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []

        # Ensure IDs are unique even when a subsection yields multiple chunks
        base_id_counts: Dict[str, int] = {}

        for ch in chunks:
            documents.append(ch.get_searchable_text())
            base_id = ch.section_number if not ch.subsection else f"{ch.section_number}_{ch.subsection}"
            idx = base_id_counts.get(base_id, 0)
            base_id_counts[base_id] = idx + 1

            # Unique ID within this preparation batch
            unique_id = base_id if idx == 0 else f"{base_id}#{idx}"

            # Ensure metadata values are primitives (no None) to satisfy Chroma
            metadatas.append(
                {
                    "section_number": str(ch.section_number),
                    "section_title": str(ch.section_title),
                    "subsection": "" if ch.subsection is None else str(ch.subsection),
                    "hierarchy": " | ".join(ch.hierarchy) if ch.hierarchy else "",
                    "full_citation": str(ch.full_citation),
                    "token_count": int(ch.token_count),
                    "chunk_index": int(idx),
                }
            )
            ids.append(unique_id)

        return documents, metadatas, ids


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    example_text = (
        "TITLE 17\n"
        "CORRECTIONS\n"
        "ARTICLE 1\n"
        "Department of Corrections\n"
        "PART 1\n"
        "CORRECTIONS ADMINISTRATION\n"
        "17-1-101. Executive director - creation - division heads. (1) The governor shall appoint an executive director. (2) There is created the division of correctional industries.\n"
    )

    chunker = LegalChunker()
    chunks = chunker.parse_document(example_text)
    print(f"Parsed chunks: {len(chunks)}")
    for c in chunks:
        print("-", c.to_dict())

    docs, metas, ids = LegalChunker.prepare_for_chromadb(chunks)
    print(f"Prepared for ChromaDB -> documents={len(docs)}, metadatas={len(metas)}, ids={len(ids)}")
